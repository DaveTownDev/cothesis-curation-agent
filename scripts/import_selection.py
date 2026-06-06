"""
Import a hand-selected, diverse batch from the enrichment queue.

Unlike run_batch (FIFO front of the queue, which is duplicate-heavy), this
selects a judge-illustrative spread: deduplicated by title, a quota per
resource type, preferring items with a real DOI (better enrichment).

  # Preview the selection (Postgres only, no ADC/LLM):
  DATABASE_PUBLIC_URL=... .venv/bin/python -m scripts.import_selection --dry-run
  # Run it (needs ADC for Vertex + Firestore):
  DATABASE_PUBLIC_URL=... GOOGLE_CLOUD_PROJECT=cothesis-curation-agent \
      .venv/bin/python -m scripts.import_selection --count 50
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("import-selection")

# Target spread across the 8 resource types present in the queue (sums to 50)
QUOTAS = {
    "article": 18,
    "software": 9,
    "reporting_guideline": 10,
    "book": 5,
    "dataset": 3,
    "video": 2,
    "book_chapter": 2,
    "funding": 1,
}


def _snake(s: str) -> str:
    import re
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s or "").lower()


def select_diverse(conn, count: int) -> list[dict]:
    """Pick a deduped, type-balanced, DOI-preferring selection of `count` items."""
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT eq.id AS queue_id, eq.resource_id, eq.resource_type,
                   ic.title, ic.url, ic.description, ic.methodology_tags,
                   ic.doi, ic.pmid, ic.isbn, ic.access_type
            FROM compendium.enrichment_queue eq
            JOIN compendium.import_candidates ic ON ic.resource_id = eq.resource_id
            WHERE eq.status = 'pending'
            ORDER BY (ic.doi IS NOT NULL AND ic.doi != '') DESC, eq.scheduled_at ASC
        """)
        rows = cur.fetchall()

    seen_titles: set[str] = set()
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        title_key = (r["title"] or "").strip().lower()
        if not title_key or title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        buckets[_snake(r["resource_type"])].append(r)

    selected: list[dict] = []
    # First pass: fill each type up to its quota
    for rtype, quota in QUOTAS.items():
        selected.extend(buckets.get(rtype, [])[:quota])
    # Top up to `count` from leftovers (any type) if quotas under-fill
    if len(selected) < count:
        chosen_ids = {r["queue_id"] for r in selected}
        for rtype, items in buckets.items():
            for r in items:
                if len(selected) >= count:
                    break
                if r["queue_id"] not in chosen_ids:
                    selected.append(r); chosen_ids.add(r["queue_id"])
    return selected[:count]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true", help="Preview selection only")
    parser.add_argument("--quotas", type=str, default="",
                        help="Override type quotas, e.g. 'reporting_guideline:6,book:5,dataset:3'")
    args = parser.parse_args()

    if args.quotas:
        QUOTAS.clear()
        for pair in args.quotas.split(","):
            k, v = pair.split(":")
            QUOTAS[k.strip()] = int(v)

    db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
    if not db_url:
        logger.error("DATABASE_PUBLIC_URL not set")
        return 1

    import psycopg2
    conn = psycopg2.connect(db_url)
    try:
        selection = select_diverse(conn, args.count)
        from collections import Counter
        spread = Counter(_snake(r["resource_type"]) for r in selection)
        logger.info("Selected %d items: %s", len(selection), dict(spread))
        for i, r in enumerate(selection, 1):
            doi = "DOI" if r["doi"] else "   "
            logger.info("  %2d. [%s][%s] %s", i, doi, _snake(r["resource_type"])[:12], str(r["title"])[:60])

        if args.dry_run:
            logger.info("dry-run — nothing processed")
            return 0

        from scripts.batch import build_resource_input, mark_item_processing, mark_item_complete, mark_item_failed
        from agents.pipeline.deterministic import run_pipeline

        outcomes = Counter()
        for i, row in enumerate(selection, 1):
            qid = row["queue_id"]; rid = row.get("resource_id")
            try:
                mark_item_processing(conn, qid)
                out = run_pipeline(build_resource_input(row), pipeline_run_id=str(rid))
                mark_item_complete(conn, qid)
                outcomes[out.get("routing", "?")] += 1
                logger.info("[%2d/%d] %-50s -> %s", i, len(selection), str(row["title"])[:50], out.get("routing"))
            except Exception as exc:
                outcomes["error"] += 1
                try:
                    mark_item_failed(conn, qid, str(exc)[:500])
                except Exception:
                    pass
                logger.error("[%2d/%d] %-50s -> ERROR %s", i, len(selection), str(row["title"])[:50], exc)
        logger.info("Import complete: %s", dict(outcomes))

        # Per-run metrics (observability without Cloud Trace)
        try:
            import os
            from datetime import datetime, timezone
            from google.cloud import firestore as _fs
            run_id = f"import-{len(selection)}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
            db = _fs.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent"))
            db.collection("pipeline_runs").document(run_id).set({
                "run_id": run_id,
                "kind": "import_selection",
                "count": len(selection),
                "outcomes": dict(outcomes),
                "models": {"flash": os.environ.get("MODEL_FLASH"), "flash_lite": os.environ.get("MODEL_FLASH_LITE")},
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info("Wrote pipeline_runs/%s", run_id)
        except Exception as exc:
            logger.warning("pipeline_runs write failed: %s", exc)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
