"""
Normalize methodology_codes and discipline_codes on Firestore records.

Touches: resources, draft_records, review_queue.draft_record (pending items).

Usage:
  python -m scripts.reprocess_taxonomy --dry-run
  python -m scripts.reprocess_taxonomy
  python -m scripts.reprocess_taxonomy --sync-published   # re-sync published rows after patch
"""
from __future__ import annotations

import argparse
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reprocess taxonomy fields on Firestore records")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument(
        "--sync-published",
        action="store_true",
        help="After patching, POST published resources to Compendium (requires secrets)",
    )
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    from google.cloud.firestore import Client as FirestoreClient

    from agents.shared.taxonomy_reprocess import reprocess_record_fields

    db = FirestoreClient(project=project)
    updated = 0
    scanned = 0

    for doc in db.collection("resources").stream():
        scanned += 1
        data = doc.to_dict() or {}
        patch = reprocess_record_fields(data)
        if not patch:
            continue
        updated += 1
        logger.info("resources/%s %s", doc.id, patch)
        if not args.dry_run:
            db.collection("resources").document(doc.id).update(patch)

    for doc in db.collection("draft_records").stream():
        scanned += 1
        data = doc.to_dict() or {}
        patch = reprocess_record_fields(data)
        if not patch:
            continue
        updated += 1
        logger.info("draft_records/%s %s", doc.id, patch)
        if not args.dry_run:
            db.collection("draft_records").document(doc.id).update(patch)

    for doc in db.collection("review_queue").where("status", "==", "pending").stream():
        scanned += 1
        data = doc.to_dict() or {}
        draft = data.get("draft_record")
        if not isinstance(draft, dict):
            continue
        patch = reprocess_record_fields(draft)
        if not patch:
            continue
        updated += 1
        logger.info("review_queue/%s draft_record %s", doc.id, patch)
        if not args.dry_run:
            db.collection("review_queue").document(doc.id).update(
                {"draft_record": {**draft, **patch}},
            )

    logger.info("Scanned %d docs; %d updated%s", scanned, updated, " (dry-run)" if args.dry_run else "")

    if args.sync_published and not args.dry_run:
        compendium_url = os.environ.get("COMPENDIUM_IMPORT_URL", "")
        api_key = os.environ.get("IMPORT_API_KEY", "")
        if not compendium_url or not api_key:
            logger.error("--sync-published requires COMPENDIUM_IMPORT_URL and IMPORT_API_KEY")
            return 1
        from scripts.sync import run_sync

        result = run_sync(db=db, compendium_url=compendium_url, api_key=api_key, batch_size=50, dry_run=False)
        logger.info("Compendium sync: %s", result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
