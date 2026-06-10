#!/usr/bin/env python3
"""
Re-run live Compendium resources through the deterministic curation pipeline.

1. Export from Postgres / Neo4j (or load a prior JSON export)
2. Run ``agents.pipeline.deterministic.run_pipeline`` on each row
3. Stamp ``compendium_id`` / ``compendium_url`` on Firestore for round-trip sync
4. Optionally re-sync published rows to Compendium after taxonomy fix

Usage:
  # Export + process first 5 (dry-run — no pipeline calls):
  python3 -m scripts.reprocess_live_resources --dry-run --limit 5

  # Full export from Postgres, run pipeline:
  DATABASE_PUBLIC_URL=... GOOGLE_CLOUD_PROJECT=cothesis-curation-agent \\
    python3 -m scripts.reprocess_live_resources --limit 50

  # Use cached export, skip rows already in pipeline_state:
  python3 -m scripts.reprocess_live_resources --input data/live_resources/export.json --skip-existing

  # After processing, normalize taxonomy + push published to Compendium:
  python3 -m scripts.reprocess_live_resources --input data/live_resources/export.json \\
    --taxonomy-only --sync-published
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def _load_input(path: str | None, source: str, limit: int) -> list[dict]:
    if path:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = doc.get("resources") or doc
        if not isinstance(rows, list):
            raise ValueError(f"Invalid export JSON: {path}")
        return rows[:limit] if limit > 0 else rows

    from agents.shared.live_compendium_export import fetch_live_resources

    return fetch_live_resources(source=source, limit=limit)


def _pipeline_state_exists(db, resource_code: str) -> bool:
    snaps = (
        db.collection("pipeline_state")
        .where("resource_code", "==", resource_code)
        .limit(1)
        .stream()
    )
    return any(True for _ in snaps)


def _stamp_compendium_link(db, resource_code: str, row: dict) -> None:
    rid = row.get("resource_id") or row.get("compendium_id")
    if not rid:
        return
    url = row.get("compendium_url") or row.get("public_url")
    patch = {
        "compendium_id": rid,
        "compendium_url": url,
        "compendium_source": "live_reprocess",
    }
    db.collection("resources").document(resource_code).set(patch, merge=True)
    db.collection("draft_records").document(resource_code).set(
        {"compendium_id": rid, "compendium_url": url},
        merge=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Reprocess live Compendium resources through run_pipeline")
    parser.add_argument("--input", help="Prior export JSON (skip live fetch)")
    parser.add_argument("--source", choices=["auto", "postgres", "neo4j"], default="auto")
    parser.add_argument("--limit", type=int, default=0, help="Max records to process (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="List records only; no pipeline/Firestore writes")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if pipeline_state exists for resource_code")
    parser.add_argument(
        "--taxonomy-only",
        action="store_true",
        help="Skip pipeline; only run scripts.reprocess_taxonomy on Firestore",
    )
    parser.add_argument(
        "--sync-published",
        action="store_true",
        help="After run, sync published Firestore rows to Compendium (needs import secrets)",
    )
    parser.add_argument("--export-first", metavar="PATH", help="Write fetched rows to JSON before processing")
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")

    rows = _load_input(args.input, args.source, args.limit)
    if not rows:
        logger.warning("No live resources to process")
        return 0

    if args.export_first and not args.dry_run:
        from agents.shared.live_compendium_export import write_export_json

        write_export_json(args.export_first, rows, source=args.source)
        logger.info("Exported %d rows → %s", len(rows), args.export_first)

    if args.dry_run:
        for i, row in enumerate(rows[:10], 1):
            logger.info(
                "[%d] %s | %s | %s",
                i,
                row.get("resource_id"),
                str(row.get("title", ""))[:50],
                row.get("url", "")[:60],
            )
        if len(rows) > 10:
            logger.info("... and %d more", len(rows) - 10)
        return 0

    if args.taxonomy_only:
        from google.cloud.firestore import Client as FirestoreClient

        from agents.shared.taxonomy_reprocess import reprocess_record_fields

        db = FirestoreClient(project=project)
        updated = 0
        for coll in ("resources", "draft_records"):
            for doc in db.collection(coll).stream():
                patch = reprocess_record_fields(doc.to_dict() or {})
                if patch:
                    doc.reference.update(patch)
                    updated += 1
        for doc in db.collection("review_queue").where("status", "==", "pending").stream():
            data = doc.to_dict() or {}
            draft = data.get("draft_record")
            if isinstance(draft, dict):
                patch = reprocess_record_fields(draft)
                if patch:
                    doc.reference.update({"draft_record": {**draft, **patch}})
                    updated += 1
        logger.info("Taxonomy-only: %d documents patched", updated)
        if args.sync_published:
            compendium_url = os.environ.get("COMPENDIUM_IMPORT_URL", "")
            api_key = os.environ.get("IMPORT_API_KEY", "")
            if not compendium_url or not api_key:
                logger.error("--sync-published requires COMPENDIUM_IMPORT_URL and IMPORT_API_KEY")
                return 1
            from scripts.sync import run_sync

            result = run_sync(db=db, compendium_url=compendium_url, api_key=api_key, batch_size=50, dry_run=False)
            logger.info("Compendium sync: synced=%d errors=%d", result.synced, result.errors)
        return 0

    from google.cloud import firestore

    from agents.pipeline.deterministic import derive_resource_code, run_pipeline
    from agents.shared.live_compendium_export import to_pipeline_input
    from agents.shared.taxonomy_reprocess import reprocess_record_fields

    db = firestore.Client(project=project)
    outcomes: Counter[str] = Counter()
    processed = 0
    skipped = 0
    failed = 0

    for idx, row in enumerate(rows, 1):
        title = row.get("title") or ""
        resource_code = derive_resource_code(
            title,
            doi=row.get("doi"),
            url=row.get("url"),
        )
        if args.skip_existing and _pipeline_state_exists(db, resource_code):
            skipped += 1
            logger.info("[%d/%d] skip existing %s", idx, len(rows), resource_code)
            continue

        pipeline_input = to_pipeline_input(row)
        run_id = str(row.get("resource_id") or resource_code)
        try:
            logger.info("[%d/%d] pipeline %s — %s", idx, len(rows), resource_code, title[:50])
            result = run_pipeline(pipeline_input, pipeline_run_id=run_id)
            routing = result.get("routing", "unknown")
            outcomes[routing] += 1
            processed += 1

            _stamp_compendium_link(db, resource_code, row)

            # Normalize taxonomy on anything the pipeline wrote
            for coll in ("resources", "draft_records"):
                doc = db.collection(coll).document(resource_code).get()
                if doc.exists:
                    patch = reprocess_record_fields(doc.to_dict() or {})
                    if patch:
                        db.collection(coll).document(resource_code).update(patch)

            queue_snaps = (
                db.collection("review_queue")
                .where("resource_code", "==", resource_code)
                .where("status", "==", "pending")
                .limit(1)
                .stream()
            )
            for qdoc in queue_snaps:
                data = qdoc.to_dict() or {}
                draft = data.get("draft_record")
                if isinstance(draft, dict):
                    patch = reprocess_record_fields(draft)
                    if patch:
                        db.collection("review_queue").document(qdoc.id).update(
                            {"draft_record": {**draft, **patch}},
                        )
        except Exception as exc:
            failed += 1
            logger.error("[%d/%d] FAILED %s: %s", idx, len(rows), resource_code, exc)

    logger.info(
        "Done: processed=%d skipped=%d failed=%d outcomes=%s",
        processed,
        skipped,
        failed,
        dict(outcomes),
    )

    if args.sync_published:
        compendium_url = os.environ.get("COMPENDIUM_IMPORT_URL", "")
        api_key = os.environ.get("IMPORT_API_KEY", "")
        if not compendium_url or not api_key:
            logger.error("--sync-published requires COMPENDIUM_IMPORT_URL and IMPORT_API_KEY")
            return 1
        from scripts.sync import run_sync

        result = run_sync(
            db=db,
            compendium_url=compendium_url,
            api_key=api_key,
            batch_size=50,
            dry_run=False,
        )
        logger.info("Compendium sync: synced=%d errors=%d", result.synced, result.errors)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
