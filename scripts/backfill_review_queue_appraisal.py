"""
Copy appraisal fields from `drafts` onto review_queue.draft_record (and draft_records).

Use after a batch reprocess that wrote drafts but omitted ai_confidence /
quality_dimensions on the embedded queue copy.

  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.backfill_review_queue_appraisal
  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.backfill_review_queue_appraisal --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

from agents.shared.review_queue_backfill import appraisal_patch_from_draft, latest_draft_for_resource


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill appraisal fields on review_queue docs")
    parser.add_argument("--dry-run", action="store_true", help="Print patches without writing")
    args = parser.parse_args()

    project = os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    from google.cloud import firestore

    db = firestore.Client(project=project)

    by_rc: dict[str, list[dict]] = defaultdict(list)
    for doc in db.collection("drafts").stream():
        data = doc.to_dict() or {}
        rc = data.get("resource_code")
        if rc:
            by_rc[rc].append(data)

    queue_patched = 0
    records_patched = 0
    for qdoc in db.collection("review_queue").stream():
        data = qdoc.to_dict() or {}
        rc = data.get("resource_code")
        if not rc:
            continue
        draft = latest_draft_for_resource(by_rc.get(rc, []))
        if not draft:
            continue
        draft_record = data.get("draft_record") or {}
        if not isinstance(draft_record, dict):
            continue
        patch = appraisal_patch_from_draft(draft, draft_record)
        if not patch:
            continue
        merged = {**draft_record, **patch}
        if args.dry_run:
            print(f"review_queue/{qdoc.id} ({rc}): +{list(patch.keys())}")
        else:
            qdoc.reference.update({"draft_record": merged})
        queue_patched += 1

        rec_ref = db.collection("draft_records").document(rc)
        rec = rec_ref.get()
        if rec.exists:
            rec_data = rec.to_dict() or {}
            rec_patch = appraisal_patch_from_draft(draft, rec_data)
            if rec_patch:
                if args.dry_run:
                    print(f"  draft_records/{rc}: +{list(rec_patch.keys())}")
                else:
                    rec_ref.update(rec_patch)
                records_patched += 1

    action = "Would patch" if args.dry_run else "Patched"
    print(f"{action} {queue_patched} review_queue docs, {records_patched} draft_records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
