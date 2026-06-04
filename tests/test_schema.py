"""
Deterministic tests for shared schema (Pydantic models).
Committed BEFORE implementation per docs/EVAL.md.
"""
import pytest
from pydantic import ValidationError


class TestAIAssessmentDraft:
    """Schema contract for the Appraisal agent's output."""

    def test_requires_human_review_when_low_confidence(self):
        """ai_confidence < 70 must force requires_human_review=True."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="test-001",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-001",
            quality_score=85,
            ai_confidence=65,  # < 70 → must force review
            quality_dimensions=dims,
        )
        assert draft.requires_human_review is True

    def test_requires_human_review_when_borderline_quality(self):
        """quality_score 60-79 must force requires_human_review=True."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="test-001",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-001",
            quality_score=72,  # 60-79 → must force review
            ai_confidence=80,
            quality_dimensions=dims,
        )
        assert draft.requires_human_review is True

    def test_auto_accept_when_high_quality_and_confidence(self):
        """quality_score >= 80 and ai_confidence >= 70 → requires_human_review=False."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="test-001",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-001",
            quality_score=82,
            ai_confidence=75,
            quality_dimensions=dims,
        )
        assert draft.requires_human_review is False

    def test_quality_score_range_rejects_over_100(self):
        """quality_score > 100 must raise ValidationError."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions

        dims = QualityDimensions.make_stub()
        with pytest.raises(ValidationError):
            AIAssessmentDraft(
                resource_code="test-001",
                model_version="gemini-flash-latest",
                pipeline_run_id="run-001",
                quality_score=150,
                ai_confidence=80,
                quality_dimensions=dims,
            )

    def test_quality_score_range_rejects_negative(self):
        """quality_score < 0 must raise ValidationError."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions

        dims = QualityDimensions.make_stub()
        with pytest.raises(ValidationError):
            AIAssessmentDraft(
                resource_code="test-001",
                model_version="gemini-flash-latest",
                pipeline_run_id="run-001",
                quality_score=-1,
                ai_confidence=80,
                quality_dimensions=dims,
            )

    def test_six_universal_dimensions_present(self):
        """QualityDimensions must contain all 6 canonical dimensions."""
        from agents.shared.schema import QualityDimensions

        dims = QualityDimensions.make_stub()
        for field in ("relevance", "accuracy", "authority", "currency",
                      "accessibility", "practical_utility"):
            assert hasattr(dims, field), f"Missing dimension: {field}"

    def test_ebm_level_absent_by_default(self):
        """ebm_level must be None for non-article resource types."""
        from agents.shared.schema import QualityDimensions

        dims = QualityDimensions.make_stub()
        assert dims.ebm_level is None

    def test_ebm_level_present_for_articles(self):
        """ebm_level must be set-able for article resource type."""
        from agents.shared.schema import QualityDimension, QualityDimensions

        ebm = QualityDimension(score=70, weight=0.1, reasoning="RCT")
        dims = QualityDimensions.make_stub(ebm_level=ebm)
        assert dims.ebm_level is not None
        assert dims.ebm_level.score == 70

    def test_firestore_dict_shape(self):
        """firestore_dict() must produce a flat dict Firestore can write."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="test-001",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-001",
            quality_score=82,
            ai_confidence=75,
            quality_dimensions=dims,
        )
        d = draft.firestore_dict()
        assert isinstance(d, dict)
        assert d["resource_code"] == "test-001"
        assert d["quality_score"] == 82
        assert "quality_dimensions" in d
        assert "requires_human_review" in d
        assert "assessed_at" in d


class TestCandidateResource:
    """Schema contract for the Discovery agent's output."""

    def test_skip_reason_required_for_non_resource(self):
        """Non-resources (homepages, 404s) must have skip_reason set."""
        from agents.shared.schema import CandidateResource

        candidate = CandidateResource(
            title="PubMed",
            url="https://pubmed.ncbi.nlm.nih.gov/",
            source="pubmed",
            type_hint="web_guide",
            raw_metadata={},
            skip_reason="homepage — not a discrete citable resource",
        )
        assert candidate.skip_reason is not None
        assert not candidate.is_processable

    def test_processable_candidate_has_no_skip_reason(self):
        """A processable candidate has no skip_reason and a real URL."""
        from agents.shared.schema import CandidateResource

        candidate = CandidateResource(
            title="STROBE statement",
            url="https://doi.org/10.1371/journal.pmed.0040297",
            source="pubmed",
            type_hint="article",
            raw_metadata={"pmid": "17941714"},
        )
        assert candidate.skip_reason is None
        assert candidate.is_processable
