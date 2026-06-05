"""
Railway Postgres enrichment_queue → agent pipeline.

Reads pending items from compendium.enrichment_queue, constructs a structured
input message for each, calls the deployed Cloud Run agent, and updates the
queue status.

Triggered by Cloud Scheduler twice daily via the agent Cloud Run
/trigger/batch endpoint, or run directly:
  python -m scripts.run_batch --batch-size 50 --dry-run

Auth: the Cloud Run agent requires a bearer token.
  - Local: set AGENT_BEARER_TOKEN in .env or pass --token flag.
  - Cloud Scheduler: uses OIDC token from agent-runtime SA (auto-injected).
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Postgres helpers
# ---------------------------------------------------------------------------

_FETCH_SQL = """
    SELECT
        eq.id          AS queue_id,
        eq.resource_id,
        eq.resource_type,
        ic.title,
        ic.url,
        ic.description,
        ic.methodology_tags,
        ic.doi,
        ic.pmid,
        ic.isbn,
        ic.access_type
    FROM compendium.enrichment_queue eq
    JOIN compendium.import_candidates ic
        ON ic.resource_id = eq.resource_id
    WHERE eq.status = 'pending'
    ORDER BY eq.priority ASC, eq.scheduled_at ASC
    LIMIT %s
"""

_MARK_PROCESSING_SQL = """
    UPDATE compendium.enrichment_queue
    SET status = 'processing', started_at = NOW(), retry_count = retry_count + 1
    WHERE id = %s
"""

_MARK_COMPLETE_SQL = """
    UPDATE compendium.enrichment_queue
    SET status = 'complete', completed_at = NOW()
    WHERE id = %s
"""

_MARK_FAILED_SQL = """
    UPDATE compendium.enrichment_queue
    SET status = 'failed', error_message = %s
    WHERE id = %s
"""


def fetch_pending_items(
    conn: Any,
    batch_size: int = 50,
) -> list[dict[str, Any]]:
    """Return up to batch_size pending enrichment queue items with resource metadata."""
    with conn.cursor() as cur:
        cur.execute(_FETCH_SQL, (batch_size,))
        rows = cur.fetchall()
    return rows


def mark_item_processing(conn: Any, queue_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(_MARK_PROCESSING_SQL, (queue_id,))
    conn.commit()


def mark_item_complete(conn: Any, queue_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(_MARK_COMPLETE_SQL, (queue_id,))
    conn.commit()


def mark_item_failed(conn: Any, queue_id: str, error: str) -> None:
    with conn.cursor() as cur:
        cur.execute(_MARK_FAILED_SQL, (error, queue_id))
    conn.commit()


# ---------------------------------------------------------------------------
# Agent message construction
# ---------------------------------------------------------------------------

def build_agent_message(row: dict[str, Any]) -> dict[str, Any]:
    """
    Build the /run request body for a single enrichment queue item.
    Provides available metadata so the pipeline can skip redundant discovery.
    """
    resource_id = row.get("resource_id", "unknown")
    resource_type = row.get("resource_type", "unknown")
    title = row.get("title", "")
    url = row.get("url", "")
    description = row.get("description", "")
    methodology_tags = row.get("methodology_tags") or []
    doi = row.get("doi") or ""
    pmid = row.get("pmid") or ""

    # Build a structured text prompt the orchestrator can parse
    meta_lines = [f"Resource type: {resource_type}", f"Title: {title}", f"URL: {url}"]
    if doi:
        meta_lines.append(f"DOI: {doi}")
    if pmid:
        meta_lines.append(f"PMID: {pmid}")
    if methodology_tags:
        meta_lines.append(f"Methodology hints: {', '.join(methodology_tags)}")
    if description:
        meta_lines.append(f"Description: {description}")

    prompt = (
        f"Curate this {resource_type} for the CoThesis Compendium. "
        f"Run the full pipeline (appraisal → classification → editorial → QC → arbiter).\n\n"
        + "\n".join(meta_lines)
    )

    session_id = f"{resource_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    return {
        "appName": "agents",
        "userId": "batch-runner",
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": prompt}],
        },
    }


# ---------------------------------------------------------------------------
# Agent call
# ---------------------------------------------------------------------------

def call_agent(
    message: dict[str, Any],
    agent_url: str,
    bearer_token: str,
    timeout: int = 600,  # full pipeline can take several minutes
) -> dict[str, Any]:
    """
    Create the ADK session, then POST to /run.

    ADK's /run endpoint requires the session to already exist — it returns 404
    otherwise. We create it via POST /apps/{app}/users/{user}/sessions/{id}.
    """
    base = agent_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }
    app_name = message["appName"]
    user_id = message["userId"]
    session_id = message["sessionId"]

    # 1. Create the session (idempotent — ignore 409 if it already exists)
    session_url = f"{base}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
    sess_resp = httpx.post(session_url, json={}, headers=headers, timeout=30)
    if sess_resp.status_code not in (200, 201, 409):
        sess_resp.raise_for_status()

    # 2. Run the pipeline
    resp = httpx.post(f"{base}/run", json=message, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _pascal_to_snake(s: str) -> str:
    """ReportingGuideline -> reporting_guideline (queue data is PascalCase)."""
    if not s:
        return "article"
    out = re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
    return out


def build_resource_input(row: dict[str, Any]) -> dict[str, Any]:
    """Map a Postgres enrichment_queue row to the run_pipeline input dict."""
    return {
        "resource_code": None,  # derived from title in the orchestrator
        "title": row.get("title", ""),
        "url": row.get("url", ""),
        "description": row.get("description", ""),
        "resource_type": _pascal_to_snake(row.get("resource_type", "")),
        "methodology_tags": row.get("methodology_tags") or [],
        "doi": row.get("doi"),
        "pmid": row.get("pmid"),
    }


def run_batch(
    conn: Any,
    batch_size: int = 50,
    dry_run: bool = False,
    pipeline_fn: Any = None,
) -> BatchResult:
    """
    Full batch run. Fetches pending items and runs each through the
    DETERMINISTIC code orchestrator (agents.pipeline.deterministic.run_pipeline),
    not the non-deterministic LlmAgent /run endpoint. Updates queue status.

    pipeline_fn is injectable for testing; defaults to the real orchestrator.
    """
    if pipeline_fn is None:
        from agents.pipeline.deterministic import run_pipeline as pipeline_fn  # noqa: N806

    result = BatchResult(dry_run=dry_run)
    items = fetch_pending_items(conn, batch_size=batch_size)

    if not items:
        logger.info("batch: no pending items in enrichment_queue")
        return result

    logger.info("batch: processing %d items (deterministic orchestrator)", len(items))

    if dry_run:
        logger.info("batch: dry-run — would process %d items", len(items))
        return result

    for item in items:
        queue_id = item.get("queue_id") or item.get("id")
        resource_id = item.get("resource_id", "unknown")
        try:
            mark_item_processing(conn, queue_id)
            resource_input = build_resource_input(item)
            outcome = pipeline_fn(resource_input, pipeline_run_id=str(resource_id))
            mark_item_complete(conn, queue_id)
            result.processed += 1
            logger.info("batch: processed %s -> %s (queue_id=%s)",
                        resource_id, outcome.get("routing", "?"), queue_id)
        except Exception as exc:
            logger.error("batch: failed resource %s: %s", resource_id, exc)
            try:
                mark_item_failed(conn, queue_id, str(exc)[:500])
            except Exception:
                pass
            result.failed += 1

    return result
