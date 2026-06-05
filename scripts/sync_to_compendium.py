"""
CLI: sync approved Firestore records to the Compendium.

Usage:
  # Dry-run (no writes):
  python -m scripts.sync_to_compendium --dry-run

  # Live run (reads from Secret Manager):
  python -m scripts.sync_to_compendium

  # Override batch size:
  python -m scripts.sync_to_compendium --batch-size 20

Environment variables (or Secret Manager at runtime):
  GOOGLE_CLOUD_PROJECT       GCP project ID
  COMPENDIUM_IMPORT_URL      Base URL of the live Compendium (e.g. https://cothesis.ai)
  IMPORT_API_KEY             Bearer token for /api/import/json
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync approved resources to Compendium")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without writing")
    parser.add_argument("--batch-size", type=int, default=50, help="Records per POST request (default: 50)")
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    compendium_url = os.environ.get("COMPENDIUM_IMPORT_URL", "")
    api_key = os.environ.get("IMPORT_API_KEY", "")

    if not compendium_url:
        logger.error("COMPENDIUM_IMPORT_URL not set — cannot sync")
        return 1
    if not api_key and not args.dry_run:
        logger.error("IMPORT_API_KEY not set — cannot sync")
        return 1

    from google.cloud.firestore import Client as FirestoreClient
    from scripts.sync import run_sync

    db = FirestoreClient(project=project)
    result = run_sync(
        db=db,
        compendium_url=compendium_url,
        api_key=api_key,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        logger.info("dry-run complete — no records written")
    else:
        logger.info("sync complete: synced=%d errors=%d batches=%s",
                    result.synced, result.errors, result.batch_ids)

    return 1 if result.errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
