"""
Reconcile pipeline_state after bulk HITL rejects.

Reject updates review_queue + resources but older rejects may have left
pipeline_state stuck at arbiter/editorial. This script marks those rows
hitl_rejected so dashboard and /pipeline match the empty review queue.

Dry-run (default):
  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.reconcile_pipeline_state

Apply writes:
  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.reconcile_pipeline_state --apply
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from google.cloud import firestore

logger = logging.getLogger(__name__)

TERMINAL_STAGES = frozenset({"hitl_rejected", "published"})


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reconcile(*, apply: bool) -> dict:
    db = firestore.Client()
    rejected_codes: set[str] = set()
    for doc in db.collection("review_queue").where("status", "==", "rejected").stream():
        rc = doc.get("resource_code")
        if rc:
            rejected_codes.add(rc)

    archived_codes: set[str] = set()
    for doc in db.collection("resources").where("editorial_status", "==", "archived").stream():
        archived_codes.add(doc.id)

    targets = rejected_codes | archived_codes
    updated = 0
    skipped = 0

    for rc in sorted(targets):
        ref = db.collection("pipeline_state").document(rc)
        snap = ref.get()
        if not snap.exists:
            skipped += 1
            continue
        data = snap.to_dict() or {}
        stage = data.get("current_stage") or data.get("state") or ""
        if stage in TERMINAL_STAGES:
            skipped += 1
            continue
        patch = {
            "resource_code": rc,
            "state": "hitl_rejected",
            "current_stage": "hitl_rejected",
            "updated_at": _now(),
            "hitl_outcome": "rejected",
        }
        logger.info("%s %s -> hitl_rejected (was %r)", "APPLY" if apply else "DRY", rc, stage)
        if apply:
            ref.set(patch, merge=True)
        updated += 1

    return {
        "rejected_queue_resources": len(rejected_codes),
        "archived_resources": len(archived_codes),
        "targets": len(targets),
        "updated": updated,
        "skipped": skipped,
        "applied": apply,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Mark stale pipeline_state rows as hitl_rejected")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    args = parser.parse_args()
    summary = reconcile(apply=args.apply)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
