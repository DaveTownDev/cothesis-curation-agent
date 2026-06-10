#!/usr/bin/env python3
"""
Reset all pipeline Firestore state and reprocess live Compendium resources.

Wipes drafts, draft_records, review_queue, pipeline_state, and resources, then
runs the deterministic pipeline on every row from the live Compendium export so
classification uses the current methodology/specialty taxonomy (148 + 53).

Usage:
  # Preview counts (no writes):
  python3 -m scripts.reset_and_reprocess_live --dry-run

  # Full reset + export + reprocess (long-running — hours for ~1500 rows):
  doppler run --project dave-ai-stack --config prd -- \\
    python3 -m scripts.reset_and_reprocess_live --confirm-reset \\
    --refresh-taxonomy --export data/live_resources/export.json \\
    2>&1 | tee data/live_resources/reprocess.log

  # Reset only (no pipeline):
  python3 -m scripts.reset_and_reprocess_live --confirm-reset --reset-only
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def _count_collection(db, name: str) -> int:
    return sum(1 for _ in db.collection(name).stream())


def _preview_counts(db) -> dict[str, int]:
    from agents.shared.firestore_reset import collections_to_clear

    return {name: _count_collection(db, name) for name in collections_to_clear(include_resources=True)}


def _refresh_taxonomy() -> None:
    logger.info("Refreshing live taxonomy from Compendium sitemap…")
    subprocess.run(
        [sys.executable, "-m", "scripts.fetch_live_taxonomy"],
        cwd=ROOT,
        check=True,
    )


def _export_live(path: str, source: str, limit: int) -> list[dict]:
    from agents.shared.live_compendium_export import fetch_live_resources, write_export_json

    rows = fetch_live_resources(source=source, limit=limit)
    write_export_json(path, rows, source=source)
    logger.info("Exported %d rows → %s", len(rows), path)
    return rows


def _sync_enrichment_queue(*, export_path: str) -> int:
    db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
    if not db_url:
        logger.error("--sync-enrichment-queue requires DATABASE_PUBLIC_URL")
        return 1
    import psycopg2
    import psycopg2.extras

    from agents.shared.enrichment_queue_sync import (
        fetch_live_catalog,
        sync_to_enrichment_queue,
    )

    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        catalog = fetch_live_catalog(conn, source="merge")
        stats = sync_to_enrichment_queue(conn, catalog, reset_existing=True)
        logger.info("enrichment_queue sync: %s", stats)
        if export_path:
            from agents.shared.live_compendium_export import write_export_json

            write_export_json(export_path, list(catalog.values()), source="merge")
        return 0
    finally:
        conn.close()


def _load_export(path: str, limit: int) -> list[dict]:
    import json

    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = doc.get("resources") or doc
    if not isinstance(rows, list):
        raise ValueError(f"Invalid export JSON: {path}")
    return rows[:limit] if limit > 0 else rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset Firestore pipeline state and reprocess live Compendium")
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Required to delete Firestore collections",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only; no deletes or pipeline calls")
    parser.add_argument("--reset-only", action="store_true", help="Clear collections and exit (no export/pipeline)")
    parser.add_argument(
        "--refresh-taxonomy",
        action="store_true",
        help="Run scripts.fetch_live_taxonomy before processing",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        default="data/live_resources/export.json",
        help="Write/read live export JSON",
    )
    parser.add_argument("--source", choices=["auto", "postgres", "neo4j"], default="auto")
    parser.add_argument("--limit", type=int, default=0, help="Max records to process (0 = all)")
    parser.add_argument(
        "--use-cached-export",
        action="store_true",
        help="Skip live fetch; load --export file (must exist)",
    )
    parser.add_argument(
        "--sync-enrichment-queue",
        action="store_true",
        help="After reset, sync live catalog into Postgres enrichment_queue (needs DATABASE_PUBLIC_URL)",
    )
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")

    from google.cloud import firestore

    from agents.shared.firestore_reset import clear_collections

    db = firestore.Client(project=project)
    counts = _preview_counts(db)
    logger.info("Current Firestore counts: %s", counts)

    if args.dry_run:
        logger.info(
            "Dry-run: would clear %d docs across %d collections",
            sum(counts.values()),
            len(counts),
        )
        if not args.use_cached_export:
            logger.info("Would export live resources → %s", args.export)
        logger.info("Would run run_pipeline on each exported row (no --skip-existing)")
        return 0

    if not args.confirm_reset:
        logger.error("Refusing to delete without --confirm-reset (use --dry-run to preview)")
        return 1

    if args.refresh_taxonomy:
        _refresh_taxonomy()

    deleted = clear_collections(db, include_resources=True)
    logger.info("Reset complete: %s", deleted)

    if args.reset_only:
        if args.sync_enrichment_queue:
            return _sync_enrichment_queue(export_path=args.export)
        return 0

    if args.sync_enrichment_queue:
        code = _sync_enrichment_queue(export_path=args.export)
        if code != 0:
            return code

    if args.use_cached_export:
        if not Path(args.export).is_file():
            logger.error("Cached export not found: %s", args.export)
            return 1
        rows = _load_export(args.export, args.limit)
        logger.info("Loaded %d rows from %s", len(rows), args.export)
    else:
        rows = _export_live(args.export, args.source, args.limit)

    if not rows:
        logger.warning("No resources to process")
        return 0

    from agents.pipeline.deterministic import derive_resource_code, run_pipeline
    from agents.shared.live_compendium_export import to_pipeline_input
    from agents.shared.taxonomy_reprocess import reprocess_record_fields

    outcomes: Counter[str] = Counter()
    processed = 0
    failed = 0

    for idx, row in enumerate(rows, 1):
        title = row.get("title") or ""
        resource_code = derive_resource_code(title, doi=row.get("doi"), url=row.get("url"))
        pipeline_input = to_pipeline_input(row)
        run_id = str(row.get("resource_id") or resource_code)
        try:
            logger.info("[%d/%d] pipeline %s — %s", idx, len(rows), resource_code, title[:50])
            result = run_pipeline(pipeline_input, pipeline_run_id=run_id)
            outcomes[result.get("routing", "unknown")] += 1
            processed += 1

            rid = row.get("resource_id") or row.get("compendium_id")
            if rid:
                link = {
                    "compendium_id": rid,
                    "compendium_url": row.get("compendium_url") or row.get("public_url"),
                    "compendium_source": "live_reprocess",
                }
                db.collection("draft_records").document(resource_code).set(link, merge=True)

            for coll in ("resources", "draft_records"):
                doc = db.collection(coll).document(resource_code).get()
                if doc.exists:
                    patch = reprocess_record_fields(doc.to_dict() or {})
                    if patch:
                        db.collection(coll).document(resource_code).update(patch)

            for qdoc in (
                db.collection("review_queue")
                .where("resource_code", "==", resource_code)
                .where("status", "==", "pending")
                .limit(1)
                .stream()
            ):
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
        "Reprocess done: processed=%d failed=%d outcomes=%s",
        processed,
        failed,
        dict(outcomes),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
