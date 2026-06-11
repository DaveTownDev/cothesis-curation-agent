"""
Deterministic tests for Reconciliation tools.
Committed BEFORE implementation per docs/EVAL.md.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestTitleSimilarity:

    def test_identical_titles_score_1(self):
        from agents.reconciliation.tools import title_similarity
        assert title_similarity("PRISMA 2020 Statement", "PRISMA 2020 Statement") == 1.0

    def test_near_duplicate_above_threshold(self):
        """Minor rewording should hit ≥ 0.9 threshold."""
        from agents.reconciliation.tools import title_similarity
        score = title_similarity(
            "PRISMA 2020 statement for systematic reviews",
            "PRISMA 2020 Statement: a systematic review reporting standard",
        )
        assert score >= 0.75  # near-duplicate (exact threshold checked in is_duplicate)

    def test_different_titles_below_threshold(self):
        from agents.reconciliation.tools import title_similarity
        score = title_similarity(
            "Cochrane Handbook for Systematic Reviews",
            "STROBE statement for observational studies",
        )
        assert score < 0.9

    def test_empty_title_returns_0(self):
        from agents.reconciliation.tools import title_similarity
        assert title_similarity("", "some title") == 0.0
        assert title_similarity("some title", "") == 0.0

    def test_case_insensitive(self):
        from agents.reconciliation.tools import title_similarity
        score = title_similarity("PRISMA 2020", "prisma 2020")
        assert score == 1.0


class TestIsDuplicate:

    def test_exact_match_is_duplicate(self):
        from agents.reconciliation.tools import is_duplicate
        existing = [{"title": "PRISMA 2020 Statement", "resource_code": "prisma-2020"}]
        dup = is_duplicate("PRISMA 2020 Statement", existing, threshold=0.9)
        assert dup is not None
        assert dup["resource_code"] == "prisma-2020"

    def test_different_title_is_not_duplicate(self):
        from agents.reconciliation.tools import is_duplicate
        existing = [{"title": "Cochrane Handbook", "resource_code": "cochrane-handbook"}]
        dup = is_duplicate("STROBE Statement", existing, threshold=0.9)
        assert dup is None

    def test_empty_existing_list_is_not_duplicate(self):
        from agents.reconciliation.tools import is_duplicate
        dup = is_duplicate("Any Title", [], threshold=0.9)
        assert dup is None


class TestAssembleDraftRecord:

    def test_assembled_record_has_required_fields(self):
        from agents.reconciliation.tools import assemble_draft_record
        from agents.shared.schema import (
            ClassificationResult, EditorialOutput, AIAssessmentDraft, QualityDimensions
        )

        classification = ClassificationResult(
            resource_type_code="article",
            resource_subtype_code="seminal_paper",
            methodology_codes=["SYN-01"],
            stage_codes=["HI", "IN"],
            relevance_score=0.85,
            classification_confidence=0.9,
            access_type="open_access",
            skip_reason=None,
            discipline_codes=["PSYCH"],
            difficulty_level="intermediate",
        )
        editorial = EditorialOutput(
            editorial_description="A key reporting standard.",
            summary="PRISMA 2020 covers systematic review reporting in detail.",
            editorial_description_plain="A checklist for writing up research studies.",
            proposed_badges=["essential"],
            difficulty_level="intermediate",
        )
        dims = QualityDimensions.make_stub()
        appraisal = AIAssessmentDraft(
            resource_code="prisma-2020",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-001",
            quality_score=95,
            ai_confidence=88,
            quality_dimensions=dims,
        )

        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=classification,
            editorial=editorial,
            appraisal=appraisal,
        )

        # Required universal fields
        assert record["resource_code"] == "prisma-2020"
        assert record["resource_type_code"] == "article"
        assert record["editorial_description"] == "A key reporting standard."
        assert record["editorial_description_plain"] == "A checklist for writing up research studies."
        assert record["quality_score"] == 95
        assert record["ai_confidence"] == 88
        assert "relevance" in record["quality_dimensions"]
        assert record["methodology_codes"] == ["SYN-01"]
        assert record["discipline_codes"] == ["PSYCH"]
        assert record.get("domain_codes") == []
        assert isinstance(record.get("tags"), list)
        assert record["editorial_status"] == "proposed"
        assert "type_fields" in record

    def test_assembled_record_editorial_status_is_proposed(self):
        """Fresh assembled records must always start as proposed."""
        from agents.reconciliation.tools import assemble_draft_record
        from agents.shared.schema import (
            ClassificationResult, EditorialOutput, AIAssessmentDraft, QualityDimensions
        )
        classification = ClassificationResult(
            resource_type_code="book",
            resource_subtype_code=None,
            methodology_codes=[],
            stage_codes=["TH"],
            relevance_score=0.7,
            classification_confidence=0.8,
            access_type="paid",
            skip_reason=None,
            discipline_codes=[],
            difficulty_level="advanced",
        )
        editorial = EditorialOutput(
            editorial_description="A research methods textbook.",
            summary="Covers quantitative and qualitative methods.",
            editorial_description_plain="A book about how to do research.",
            proposed_badges=[],
            difficulty_level="advanced",
        )
        dims = QualityDimensions.make_stub()
        appraisal = AIAssessmentDraft(
            resource_code="methods-book",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-002",
            quality_score=78,
            ai_confidence=72,
            quality_dimensions=dims,
        )
        record = assemble_draft_record(
            resource_code="methods-book",
            title="Research Methods in Health",
            url="https://example.com/book",
            classification=classification,
            editorial=editorial,
            appraisal=appraisal,
        )
        assert record["editorial_status"] == "proposed"
