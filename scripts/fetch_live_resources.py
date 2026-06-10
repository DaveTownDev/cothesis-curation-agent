#!/usr/bin/env python3
"""
Export all live Compendium resources to JSON for offline re-processing.

Preferred source: Railway Postgres (DATABASE_PUBLIC_URL).
Fallback: Neo4j HTTP API (NEO4J_HTTP_URL, NEO4J_USERNAME, NEO4J_PASSWORD).

Usage:
  python3 -m scripts.fetch_live_resources --dry-run
  python3 -m scripts.fetch_live_resources --output data/live_resources/export.json
  python3 -m scripts.fetch_live_resources --source neo4j --limit 50
"""
from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export live Compendium resources to JSON")
    parser.add_argument(
        "--source",
        choices=["auto", "postgres", "neo4j"],
        default="auto",
        help="Export backend (default: auto = postgres then neo4j)",
    )
    parser.add_argument("--limit", type=int, default=0, help="Cap number of records (0 = all)")
    parser.add_argument(
        "--output",
        default="data/live_resources/export.json",
        help="Output JSON path",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print count only, do not write file")
    args = parser.parse_args()

    from agents.shared.live_compendium_export import fetch_live_resources, write_export_json

    records = fetch_live_resources(source=args.source, limit=args.limit)
    logger.info("Fetched %d live resources via source=%s", len(records), args.source)

    if args.dry_run:
        if records:
            sample = records[0]
            logger.info("Sample: %s — %s", sample.get("resource_id"), str(sample.get("title"))[:60])
        return 0

    write_export_json(args.output, records, source=args.source)
    logger.info("Wrote %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
