"""Backfill appraisal fields onto review_queue.draft_record from `drafts`."""
from __future__ import annotations

from typing import Any, Optional


_APPRAISAL_FIELDS = (
    "ai_confidence",
    "quality_dimensions",
    "trainee_suitability_score",
    "language_detected",
    "strengths",
    "limitations",
)


def appraisal_patch_from_draft(draft: dict, draft_record: dict) -> dict[str, Any]:
    """Return fields to merge into draft_record when missing on the queue copy."""
    patch: dict[str, Any] = {}
    for key in _APPRAISAL_FIELDS:
        if draft_record.get(key) not in (None, [], {}):
            continue
        val = draft.get(key)
        if val in (None, [], {}):
            continue
        patch[key] = val
    return patch


def latest_draft_for_resource(drafts: list[dict]) -> Optional[dict]:
    if not drafts:
        return None
    drafts.sort(key=lambda d: d.get("assessed_at") or "", reverse=True)
    return drafts[0]
