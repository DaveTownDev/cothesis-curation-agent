"""
Publish checklist tests — explicitly required by docs/EVAL.md.

Checklist from docs/SCHEMA.md:
  editorial_description present
  ≥1 methodology_code (platform)
  quality_score present
  link verified (url present)
  human-ratified (editorial_reviewed_by + editorial_reviewed_at on Resource.editorial)
"""
import pytest


def _make_valid_record(**overrides) -> dict:
    base = {
        "resource_code": "prisma-2020",
        "title": "PRISMA 2020 Statement",
        "url": "https://doi.org/10.1136/bmj.n71",
        "resource_type_code": "reporting_guideline",
        "editorial_description": "The reporting standard for systematic reviews.",
        "editorial_description_plain": "A checklist for writing up research.",
        "quality_score": 95.0,
        "methodology_codes": ["SYN-01", "SYN-02"],
        "editorial_status": "in_review",
        "editorial_reviewed_by": "user-reviewer-001",
        "editorial_reviewed_at": "2026-06-04T12:00:00Z",
    }
    base.update(overrides)
    return base


class TestPublishChecklist:

    def test_valid_record_passes(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record()
        errors = validate_publish_checklist(record)
        assert errors == []

    def test_missing_editorial_description_fails(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(editorial_description="")
        errors = validate_publish_checklist(record)
        assert any("editorial_description" in e for e in errors)

    def test_no_methodology_codes_fails(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(methodology_codes=[])
        errors = validate_publish_checklist(record)
        assert any("methodology_code" in e for e in errors)

    def test_missing_quality_score_fails(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(quality_score=None)
        errors = validate_publish_checklist(record)
        assert any("quality_score" in e for e in errors)

    def test_missing_url_fails(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(url="")
        errors = validate_publish_checklist(record)
        assert any("url" in e for e in errors)

    def test_missing_reviewer_fails(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(editorial_reviewed_by=None)
        errors = validate_publish_checklist(record)
        assert any("editorial_reviewed_by" in e or "ratif" in e for e in errors)

    def test_missing_reviewed_at_fails(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(editorial_reviewed_at=None)
        errors = validate_publish_checklist(record)
        assert any("editorial_reviewed_at" in e or "ratif" in e for e in errors)

    def test_multiple_violations_reported(self):
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(
            editorial_description="",
            methodology_codes=[],
            quality_score=None,
        )
        errors = validate_publish_checklist(record)
        assert len(errors) >= 3

    def test_low_quality_score_below_60_fails(self):
        """Records with quality_score < 60 are not publishable (hidden on card)."""
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(quality_score=45.0)
        errors = validate_publish_checklist(record)
        assert any("quality_score" in e or "60" in e for e in errors)

    def test_legacy_methodology_code_fails(self):
        """Legacy codes must never reach the publish gate."""
        from agents.shared.checklist import validate_publish_checklist
        record = _make_valid_record(methodology_codes=["RS-01"])
        errors = validate_publish_checklist(record)
        assert any("platform" in e or "legacy" in e.lower() or "RS-" in e for e in errors)
