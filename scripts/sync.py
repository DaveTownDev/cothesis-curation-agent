"""
Firestore approved records → Compendium /api/import/json.

Reads `resources` collection where editorial_status=published and
compendium_synced_at is absent, transforms via compendium_bridge,
batches and POSTs to the Compendium API, then writes sync status back.

Triggered by Cloud Scheduler every 30 minutes via the agent Cloud Run
/trigger/sync endpoint, or run directly:
  python -m scripts.sync_to_compendium --dry-run
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from google.cloud.firestore import Client as FirestoreClient
from google.cloud.firestore import SERVER_TIMESTAMP

from agents.shared.compendium_bridge import to_compendium_record
from agents.shared.compendium_sync import (
    ImportBatchResult,
    ResourceSyncOutcome,
    needs_compendium_resync,
    parse_import_response,
)

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    synced: int = 0
    errors: int = 0
    batch_ids: list[str] = field(default_factory=list)
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------

def fetch_unsynced_records(
    db: FirestoreClient,
    limit: int = 0,
) -> list[dict[str, Any]]:
    """
    Return published resources that need Compendium sync or re-sync (missing id/url).
    Filters on editorial_status == 'published'; resync eligibility is checked
    client-side (Firestore can't filter on missing fields directly).
    Pass limit > 0 to cap the result set.
    """
    col = db.collection("resources")
    query = col.where("editorial_status", "==", "published")
    if limit > 0:
        query = query.limit(limit)
    records = []
    for doc in query.stream():
        data = doc.to_dict()
        if needs_compendium_resync(data):
            data["_doc_id"] = doc.id
            records.append(data)
    return records


def mark_synced(
    db: FirestoreClient,
    doc_id: str,
    batch_id: str,
    outcome: ResourceSyncOutcome | None = None,
) -> None:
    update: dict[str, Any] = {
        "compendium_synced_at": SERVER_TIMESTAMP,
        "compendium_batch_id": batch_id,
        "compendium_sync_error": None,
    }
    if outcome:
        if outcome.compendium_id:
            update["compendium_id"] = outcome.compendium_id
        if outcome.compendium_url:
            update["compendium_url"] = outcome.compendium_url
    db.collection("resources").document(doc_id).update(update)


def mark_sync_error(
    db: FirestoreClient,
    doc_id: str,
    error: str,
) -> None:
    db.collection("resources").document(doc_id).update({
        "compendium_sync_error": error,
    })


# ---------------------------------------------------------------------------
# Compendium POST
# ---------------------------------------------------------------------------

def post_to_compendium(
    records: list[dict[str, Any]],
    compendium_url: str,
    api_key: str,
    timeout: int = 30,
) -> ImportBatchResult:
    """
    POST a batch of records to /api/import/json.
    Returns batch id plus per-record compendium_id/url when the API provides them.
    Raises httpx.HTTPStatusError on non-2xx.
    """
    candidates = [to_compendium_record(r) for r in records]
    url = f"{compendium_url.rstrip('/')}/api/import/json"
    resp = httpx.post(
        url,
        json={
            "source_file": f"cothesis-agent-sync-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "source_tool": "claude",
            "resources": candidates,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return parse_import_response(resp.json(), records, compendium_url)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_sync(
    db: FirestoreClient,
    compendium_url: str,
    api_key: str,
    batch_size: int = 50,
    dry_run: bool = False,
) -> SyncResult:
    """
    Full sync run. Fetches unsynced records, batches them, POSTs to Compendium,
    and writes sync status back to Firestore.
    """
    result = SyncResult(dry_run=dry_run)
    records = fetch_unsynced_records(db)

    if not records:
        logger.info("sync: no unsynced records found")
        return result

    logger.info("sync: found %d unsynced records", len(records))

    if dry_run:
        logger.info("sync: dry-run — would POST %d records in %d batches",
                    len(records), math.ceil(len(records) / batch_size))
        return result

    # Chunk into batches
    for i in range(0, len(records), batch_size):
        chunk = records[i : i + batch_size]
        try:
            batch = post_to_compendium(chunk, compendium_url, api_key)
            result.batch_ids.append(batch.import_batch_id)
            for r, outcome in zip(chunk, batch.outcomes):
                try:
                    mark_synced(db, r["_doc_id"], batch.import_batch_id, outcome)
                    result.synced += 1
                except Exception as fs_err:
                    logger.error("sync: Firestore update failed for %s: %s", r.get("_doc_id"), fs_err)
                    result.errors += 1
            logger.info("sync: batch %s — %d records posted", batch.import_batch_id, len(chunk))
        except Exception as exc:
            logger.error("sync: POST failed for chunk %d-%d: %s", i, i + len(chunk), exc)
            for r in chunk:
                try:
                    mark_sync_error(db, r["_doc_id"], str(exc))
                except Exception:
                    pass
            result.errors += len(chunk)

    return result
