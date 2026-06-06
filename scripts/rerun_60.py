"""
Re-run the EXACT same 60 resources (by queue_id) through the FIXED pipeline.

Reads queue_ids from the cached selection (/tmp/cothesis_records.json), pulls
the ORIGINAL rows from Railway (doi/pmid/resource_type intact) so the re-run
faithfully exercises grounding + type-hint + source-check + enrichment, then
runs the deterministic orchestrator and writes a pipeline_runs/{id} metrics doc.

  DATABASE_PUBLIC_URL=... GOOGLE_CLOUD_PROJECT=cothesis-curation-agent \
      .venv/bin/python -m scripts.rerun_60 [--clear] [--cache /tmp/cothesis_records.json]

--clear wipes drafts / draft_records / review_queue / pipeline_state first so the
re-run is a clean before/after (old kebab-only resource_codes won't linger).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rerun-60")

_CLEAR_COLLECTIONS = ["drafts", "draft_records", "review_queue", "pipeline_state"]


def clear_firestore(project: str) -> None:
    from google.cloud import firestore
    db = firestore.Client(project=project)
    for name in _CLEAR_COLLECTIONS:
        deleted = 0
        while True:
            batch = db.batch()
            docs = list(db.collection(name).limit(400).stream())
            if not docs:
                break
            for d in docs:
                batch.delete(d.reference)
            batch.commit()
            deleted += len(docs)
        logger.info("cleared %s: %d docs", name, deleted)


def fetch_by_queue_ids(conn, queue_ids: list[str]) -> list[dict]:
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT eq.id AS queue_id, eq.resource_id, eq.resource_type,
                   ic.title, ic.url, ic.description, ic.methodology_tags,
                   ic.doi, ic.pmid, ic.isbn, ic.access_type
            FROM compendium.enrichment_queue eq
            JOIN compendium.import_candidates ic ON ic.resource_id = eq.resource_id
            WHERE eq.id = ANY(%s)
        """, (queue_ids,))
        rows = {r["queue_id"]: r for r in cur.fetchall()}
    # preserve original order, warn on any missing
    ordered = []
    for qid in queue_ids:
        if qid in rows:
            ordered.append(rows[qid])
        else:
            logger.warning("queue_id not found in Railway: %s", qid)
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true", help="Wipe Firestore collections first")
    parser.add_argument("--cache", default="/tmp/cothesis_records.json")
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
    if not db_url:
        logger.error("DATABASE_PUBLIC_URL not set")
        return 1

    with open(args.cache) as fh:
        cached = json.load(fh)
    queue_ids = [r["queue_id"] for r in cached]
    logger.info("Re-running %d resources from %s", len(queue_ids), args.cache)

    if args.clear:
        clear_firestore(project)

    import psycopg2
    conn = psycopg2.connect(db_url)
    try:
        rows = fetch_by_queue_ids(conn, queue_ids)
    finally:
        conn.close()
    logger.info("Pulled %d original rows from Railway", len(rows))

    from scripts.batch import build_resource_input
    from agents.pipeline.deterministic import run_pipeline

    outcomes = Counter()
    for i, row in enumerate(rows, 1):
        try:
            out = run_pipeline(build_resource_input(row), pipeline_run_id=str(row.get("resource_id")))
            outcomes[out.get("routing", "?")] += 1
            logger.info("[%2d/%d] %-48s -> %s", i, len(rows), str(row["title"])[:48], out.get("routing"))
        except Exception as exc:
            outcomes["error"] += 1
            logger.error("[%2d/%d] %-48s -> ERROR %s", i, len(rows), str(row["title"])[:48], exc)
    logger.info("Re-run complete: %s", dict(outcomes))

    # Metrics doc
    try:
        from datetime import datetime, timezone
        from google.cloud import firestore as _fs
        run_id = f"rerun60-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        _fs.Client(project=project).collection("pipeline_runs").document(run_id).set({
            "run_id": run_id, "kind": "rerun_60", "count": len(rows),
            "outcomes": dict(outcomes),
            "models": {"flash": os.environ.get("MODEL_FLASH"), "flash_lite": os.environ.get("MODEL_FLASH_LITE")},
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Wrote pipeline_runs/%s", run_id)
    except Exception as exc:
        logger.warning("pipeline_runs write failed: %s", exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
