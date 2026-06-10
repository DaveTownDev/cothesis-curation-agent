#!/usr/bin/env python3
"""
Export the live Compendium catalog and sync into Postgres ``enrichment_queue``.

Sources (public library backing stores):
  - Postgres ``import_candidates`` (preferred metadata)
  - Neo4j ``CompendiumResource`` nodes (adds any on-site resources missing from PG)

Usage:
  # Preview:
  doppler run --project dave-ai-stack --config prd -- \\
    python3 -m scripts.sync_live_to_enrichment_queue --dry-run

  # Insert missing + reset complete/failed/processing → pending:
  doppler run --project dave-ai-stack --config prd -- \\
    python3 -m scripts.sync_live_to_enrichment_queue --confirm
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync live Compendium resources to enrichment_queue")
    parser.add_argument("--dry-run", action="store_true", help="Preview counts only")
    parser.add_argument("--confirm", action="store_true", help="Required to write to Postgres")
    parser.add_argument(
        "--source",
        choices=["merge", "postgres", "neo4j", "auto"],
        default="merge",
        help="Catalog source (default: merge postgres + neo4j)",
    )
    parser.add_argument("--limit", type=int, default=0, help="Cap catalog size (0 = all)")
    parser.add_argument(
        "--no-reset-existing",
        action="store_true",
        help="Only insert missing rows; leave complete/failed rows unchanged",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Also write merged catalog JSON (e.g. data/live_resources/export.json)",
    )
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
    if not db_url and args.source in ("merge", "postgres", "auto"):
        logger.error("DATABASE_PUBLIC_URL not set")
        return 1

    from agents.shared.enrichment_queue_sync import (
        fetch_live_catalog,
        preview_sync,
        sync_to_enrichment_queue,
    )

    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor) if db_url else None
    try:
        catalog = fetch_live_catalog(conn, source=args.source, limit=args.limit)
    finally:
        if conn is not None:
            conn.close()

    logger.info("Live catalog: %d resources (source=%s)", len(catalog), args.source)

    if args.export:
        from agents.shared.live_compendium_export import write_export_json

        write_export_json(args.export, list(catalog.values()), source=args.source)
        logger.info("Wrote catalog → %s", args.export)

    if not db_url:
        logger.error("DATABASE_PUBLIC_URL required for queue sync")
        return 1

    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        preview = preview_sync(conn, catalog)
        logger.info("Queue sync preview: %s", preview)

        if args.dry_run:
            return 0

        if not args.confirm:
            logger.error("Refusing to write without --confirm (use --dry-run to preview)")
            return 1

        stats = sync_to_enrichment_queue(
            conn,
            catalog,
            reset_existing=not args.no_reset_existing,
        )
        logger.info("Queue sync complete: %s", stats)
        print(json.dumps({"preview": preview, "result": stats}, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
