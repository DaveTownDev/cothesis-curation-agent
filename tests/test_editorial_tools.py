"""
Deterministic tests for Editorial tools.
Committed BEFORE implementation per docs/EVAL.md.
"""
import pytest
from pydantic import ValidationError


VALID_EDITORIAL = {
    "editorial_description": "A checklist for reporting systematic reviews.",
    "summary": (
        "PRISMA 2020 specifies what a systematic review should report. "
        "It pairs with a flow diagram and an abstract checklist. "
        "Adopting it early shapes documentation decisions. "
        "The 2020 update added items on search reproducibility."
    ),
    "editorial_description_plain": (
        "A checklist for writing up a study where you gather all existing "
        "research on a question. Going through it ensures you've spelled out "
        "exactly how you searched and what you found."
    ),
    "proposed_badges": ["essential"],
    "difficulty_level": "beginner",
}


class TestEditorialOutput:

    def test_parse_valid_editorial(self):
        from agents.shared.schema import EditorialOutput
        out = EditorialOutput(**VALID_EDITORIAL)
        assert out.editorial_description
        assert out.summary
        assert out.editorial_description_plain

    def test_all_four_fields_required(self):
        from agents.shared.schema import EditorialOutput
        for field in ("editorial_description", "summary",
                      "editorial_description_plain", "difficulty_level"):
            bad = {k: v for k, v in VALID_EDITORIAL.items() if k != field}
            with pytest.raises(ValidationError):
                EditorialOutput(**bad)

    def test_editorial_note_not_a_field(self):
        """editorial_note must not be part of EditorialOutput (human-only)."""
        from agents.shared.schema import EditorialOutput
        out = EditorialOutput(**VALID_EDITORIAL)
        assert not hasattr(out, "editorial_note")

    def test_badges_must_be_from_canonical_set(self):
        from agents.shared.schema import EditorialOutput
        bad = {**VALID_EDITORIAL, "proposed_badges": ["not_a_real_badge"]}
        with pytest.raises(ValidationError):
            EditorialOutput(**bad)

    def test_badges_max_3(self):
        from agents.shared.schema import EditorialOutput
        too_many = {**VALID_EDITORIAL,
                    "proposed_badges": ["essential", "best_free", "best_beginners", "expert_pick"]}
        with pytest.raises(ValidationError):
            EditorialOutput(**too_many)

    def test_difficulty_level_valid_values(self):
        from agents.shared.schema import EditorialOutput
        for level in ("beginner", "intermediate", "advanced"):
            out = EditorialOutput(**{**VALID_EDITORIAL, "difficulty_level": level})
            assert out.difficulty_level == level

    def test_difficulty_level_rejects_invalid(self):
        from agents.shared.schema import EditorialOutput
        with pytest.raises(ValidationError):
            EditorialOutput(**{**VALID_EDITORIAL, "difficulty_level": "expert"})


class TestJargonCheck:

    def test_flags_systematic_review_in_plain(self):
        from agents.editorial.tools import check_plain_for_jargon
        violations = check_plain_for_jargon("This is a systematic review resource.")
        assert len(violations) > 0

    def test_flags_risk_of_bias_in_plain(self):
        from agents.editorial.tools import check_plain_for_jargon
        violations = check_plain_for_jargon("Uses risk-of-bias assessment tools.")
        assert len(violations) > 0

    def test_flags_observational_in_plain(self):
        from agents.editorial.tools import check_plain_for_jargon
        violations = check_plain_for_jargon("Covers observational study design.")
        assert len(violations) > 0

    def test_clean_plain_passes(self):
        from agents.editorial.tools import check_plain_for_jargon
        violations = check_plain_for_jargon(
            "A checklist that helps you write up a study where you gather "
            "existing research on a question."
        )
        assert violations == []

    def test_flags_reporting_guideline_in_plain(self):
        from agents.editorial.tools import check_plain_for_jargon
        violations = check_plain_for_jargon("A reporting guideline for studies.")
        assert len(violations) > 0
