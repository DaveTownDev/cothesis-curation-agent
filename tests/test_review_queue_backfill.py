"""Tests for review_queue appraisal backfill helpers."""
from agents.shared.review_queue_backfill import appraisal_patch_from_draft, latest_draft_for_resource


def test_appraisal_patch_fills_missing_fields_only():
    draft = {
        "ai_confidence": 65,
        "quality_dimensions": {"relevance": {"score": 90, "weight": 0.1, "reasoning": "x"}},
        "strengths": ["solid"],
        "assessed_at": "2026-06-10T12:00:00+00:00",
    }
    record = {"quality_score": 85, "ai_confidence": None}
    patch = appraisal_patch_from_draft(draft, record)
    assert patch["ai_confidence"] == 65
    assert "quality_dimensions" in patch
    assert patch["strengths"] == ["solid"]


def test_appraisal_patch_skips_when_record_already_has_values():
    draft = {"ai_confidence": 65, "strengths": ["solid"]}
    record = {"ai_confidence": 80, "strengths": ["existing"]}
    assert appraisal_patch_from_draft(draft, record) == {}


def test_latest_draft_for_resource_picks_newest():
    older = {"assessed_at": "2026-06-09T10:00:00+00:00", "ai_confidence": 50}
    newer = {"assessed_at": "2026-06-10T10:00:00+00:00", "ai_confidence": 70}
    assert latest_draft_for_resource([older, newer])["ai_confidence"] == 70
