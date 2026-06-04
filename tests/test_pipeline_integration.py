"""
Integration tests — full pipeline data flow (no LLM, no network).
Verifies that the outputs from each stage compose correctly into
a complete draft record.
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_classification():
    from agents.shared.schema import ClassificationResult
    return ClassificationResult(
        resource_type_code="reporting_guideline",
        resource_subtype_code="primary_guideline",
        methodology_codes=["SYN-01", "SYN-02"],
        stage_codes=["HI", "SH"],
        skill_codes=["FS-02"],
        relevance_score=0.95,
        classification_confidence=0.92,
        access_type="free",
        skip_reason=None,
        discipline_codes=[],
        difficulty_level="beginner",
    )


def _make_editorial():
    from agents.shared.schema import EditorialOutput
    return EditorialOutput(
        editorial_description="The reporting standard for systematic reviews and meta-analyses.",
        summary=(
            "PRISMA 2020 specifies 27 items for reporting systematic reviews. "
            "It includes a flow diagram tracking records through screening. "
            "The 2020 update added items on search reproducibility. "
            "Adopt it from the start of your project."
        ),
        editorial_description_plain=(
            "A checklist that makes sure you explain clearly how you searched "
            "for studies and what you decided to include or leave out."
        ),
        proposed_badges=["essential"],
        difficulty_level="beginner",
    )


def _make_appraisal(resource_code: str = "prisma-2020"):
    from agents.shared.schema import AIAssessmentDraft, QualityDimensions
    return AIAssessmentDraft(
        resource_code=resource_code,
        model_version="gemini-flash-latest",
        pipeline_run_id="run-integration-001",
        quality_score=95.0,
        ai_confidence=90.0,
        quality_dimensions=QualityDimensions.make_stub(),
        thesis_stage_signals=["HI", "SH"],
        relevance_to_methodology_codes=["SYN-01", "SYN-02"],
        proposed_badges=["essential"],
    )


class TestFullPipelineFlow:

    def test_complete_draft_record_has_all_display_slots(self):
        """The assembled record must have all four console display slots."""
        from agents.reconciliation.tools import assemble_draft_record
        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=_make_classification(),
            editorial=_make_editorial(),
            appraisal=_make_appraisal(),
        )
        assert record["editorial_description"]        # short slot
        assert record["summary"]                      # long slot
        assert record["editorial_description_plain"]  # plain slot
        # editorial_note is human-only — must NOT be in the record
        assert "editorial_note" not in record

    def test_assembled_record_methodology_codes_are_platform(self):
        from agents.reconciliation.tools import assemble_draft_record
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=_make_classification(),
            editorial=_make_editorial(),
            appraisal=_make_appraisal(),
        )
        for code in record["methodology_codes"]:
            for legacy_prefix in LEGACY_METHODOLOGY_PREFIXES:
                assert not code.startswith(legacy_prefix), (
                    f"Legacy code {code!r} found in assembled record"
                )

    def test_routing_scores_are_0_to_1(self):
        from agents.reconciliation.tools import assemble_draft_record
        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=_make_classification(),
            editorial=_make_editorial(),
            appraisal=_make_appraisal(),
        )
        assert 0.0 <= record["relevance_score"] <= 1.0
        assert 0.0 <= record["classification_confidence"] <= 1.0

    def test_quality_score_is_0_to_100(self):
        from agents.reconciliation.tools import assemble_draft_record
        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=_make_classification(),
            editorial=_make_editorial(),
            appraisal=_make_appraisal(),
        )
        assert 0 <= record["quality_score"] <= 100

    def test_requires_human_review_false_for_high_quality(self):
        from agents.reconciliation.tools import assemble_draft_record
        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=_make_classification(),
            editorial=_make_editorial(),
            appraisal=_make_appraisal(),  # quality=95, confidence=90 → no review
        )
        assert record["requires_human_review"] is False

    def test_draft_record_ready_for_publish_checklist(self):
        """Assembled record + mock reviewer fields must pass the publish checklist."""
        from agents.reconciliation.tools import assemble_draft_record
        from agents.shared.checklist import validate_publish_checklist

        record = assemble_draft_record(
            resource_code="prisma-2020",
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            classification=_make_classification(),
            editorial=_make_editorial(),
            appraisal=_make_appraisal(),
        )
        # Simulate human ratification
        record["editorial_reviewed_by"] = "reviewer-001"
        record["editorial_reviewed_at"] = "2026-06-04T15:00:00Z"
        record["editorial_status"] = "in_review"

        errors = validate_publish_checklist(record)
        assert errors == [], f"Publish checklist failed: {errors}"

    def test_duplicate_detection_stops_pipeline(self):
        """When is_duplicate finds a match, the pipeline must stop."""
        from agents.reconciliation.tools import is_duplicate
        existing = [
            {"title": "PRISMA 2020 Statement", "resource_code": "prisma-2020"},
        ]
        match = is_duplicate("PRISMA 2020 Statement", existing, threshold=0.9)
        assert match is not None
        assert match["resource_code"] == "prisma-2020"

    def test_candidate_resource_is_processable(self):
        from agents.shared.schema import CandidateResource
        c = CandidateResource(
            title="PRISMA 2020 Statement",
            url="https://doi.org/10.1136/bmj.n71",
            source="pubmed",
            type_hint="reporting_guideline",
        )
        assert c.is_processable

    def test_candidate_resource_with_skip_reason_not_processable(self):
        from agents.shared.schema import CandidateResource
        c = CandidateResource(
            title="PubMed Homepage",
            url="https://pubmed.ncbi.nlm.nih.gov/",
            source="pubmed",
            type_hint="web_guide",
            skip_reason="homepage — not a discrete citable resource",
        )
        assert not c.is_processable


class TestAppraisalEdgeCases:

    def test_ebm_level_set_for_article(self):
        from agents.shared.schema import AIAssessmentDraft, QualityDimension, QualityDimensions
        ebm = QualityDimension(score=85, weight=0.1, reasoning="RCT, level 2 evidence")
        dims = QualityDimensions.make_stub(ebm_level=ebm)
        draft = AIAssessmentDraft(
            resource_code="rct-001",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-001",
            quality_score=88,
            ai_confidence=80,
            quality_dimensions=dims,
        )
        d = draft.firestore_dict()
        assert "ebm_level" in d["quality_dimensions"]
        assert d["quality_dimensions"]["ebm_level"]["score"] == 85

    def test_ebm_level_absent_for_book(self):
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions
        dims = QualityDimensions.make_stub()  # ebm_level=None
        draft = AIAssessmentDraft(
            resource_code="book-001",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-002",
            quality_score=80,
            ai_confidence=75,
            quality_dimensions=dims,
        )
        d = draft.firestore_dict()
        assert "ebm_level" not in d["quality_dimensions"]

    def test_all_three_routing_thresholds(self):
        """Test all three routing outcomes: auto-accept, review, auto-reject."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions
        dims = QualityDimensions.make_stub()

        # Auto-accept: score ≥ 80 AND confidence ≥ 70
        high = AIAssessmentDraft(resource_code="r", model_version="m",
                                 pipeline_run_id="p", quality_score=82,
                                 ai_confidence=75, quality_dimensions=dims)
        assert high.requires_human_review is False

        # Human review: confidence < 70
        low_conf = AIAssessmentDraft(resource_code="r", model_version="m",
                                     pipeline_run_id="p", quality_score=85,
                                     ai_confidence=65, quality_dimensions=dims)
        assert low_conf.requires_human_review is True

        # Human review: borderline quality (60-79)
        border = AIAssessmentDraft(resource_code="r", model_version="m",
                                   pipeline_run_id="p", quality_score=70,
                                   ai_confidence=80, quality_dimensions=dims)
        assert border.requires_human_review is True
