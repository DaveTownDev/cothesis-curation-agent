"""
Deterministic tests for Appraisal tools (Firestore write, schema validation).
Committed BEFORE implementation per docs/EVAL.md.
Uses a Firestore emulator or mocked client — no live GCP calls.
"""
import json
import pytest
from unittest.mock import MagicMock, patch


class TestFirestoreWrite:
    """Appraisal must write a valid AIAssessment document to Firestore drafts."""

    def test_write_draft_returns_document_id(self):
        """write_draft_assessment() must return the Firestore document ID."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions
        from agents.appraisal.tools import write_draft_assessment

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="strobe-2007",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-test-001",
            quality_score=88,
            ai_confidence=82,
            quality_dimensions=dims,
        )

        mock_col = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "auto-generated-id-123"
        mock_col.add.return_value = (None, mock_doc_ref)

        with patch("agents.appraisal.tools.get_firestore_collection",
                   return_value=mock_col):
            doc_id = write_draft_assessment(draft)

        assert doc_id == "auto-generated-id-123"
        mock_col.add.assert_called_once()
        written_data = mock_col.add.call_args[0][0]
        assert written_data["resource_code"] == "strobe-2007"
        assert written_data["quality_score"] == 88
        assert written_data["requires_human_review"] is False

    def test_write_draft_includes_assessed_at(self):
        """Written document must include assessed_at timestamp."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions
        from agents.appraisal.tools import write_draft_assessment

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="test-002",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-test-002",
            quality_score=75,
            ai_confidence=60,
            quality_dimensions=dims,
        )

        mock_col = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "doc-456"
        mock_col.add.return_value = (None, mock_doc_ref)

        with patch("agents.appraisal.tools.get_firestore_collection",
                   return_value=mock_col):
            write_draft_assessment(draft)

        written_data = mock_col.add.call_args[0][0]
        assert "assessed_at" in written_data
        assert written_data["requires_human_review"] is True  # confidence 60 < 70

    def test_write_draft_sets_six_dimensions(self):
        """Written document must have all 6 canonical quality dimensions."""
        from agents.shared.schema import AIAssessmentDraft, QualityDimensions
        from agents.appraisal.tools import write_draft_assessment

        dims = QualityDimensions.make_stub()
        draft = AIAssessmentDraft(
            resource_code="test-003",
            model_version="gemini-flash-latest",
            pipeline_run_id="run-test-003",
            quality_score=80,
            ai_confidence=75,
            quality_dimensions=dims,
        )

        mock_col = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "doc-789"
        mock_col.add.return_value = (None, mock_doc_ref)

        with patch("agents.appraisal.tools.get_firestore_collection",
                   return_value=mock_col):
            write_draft_assessment(draft)

        written_data = mock_col.add.call_args[0][0]
        qdims = written_data["quality_dimensions"]
        for dim_name in ("relevance", "accuracy", "authority", "currency",
                         "accessibility", "practical_utility"):
            assert dim_name in qdims, f"Missing dimension: {dim_name}"


class TestAppraisalOutputParsing:
    """parse_appraisal_json() must produce a valid AIAssessmentDraft."""

    def test_parse_valid_appraisal_json(self):
        """A well-formed LLM appraisal JSON must parse to AIAssessmentDraft."""
        from agents.appraisal.tools import parse_appraisal_json

        llm_output = {
            "quality_score": 88,
            "quality_dimensions": {
                "relevance": {"score": 90, "weight": 0.25, "reasoning": "Highly relevant"},
                "accuracy": {"score": 88, "weight": 0.20, "reasoning": "Well-cited"},
                "authority": {"score": 92, "weight": 0.20, "reasoning": "High-impact journal"},
                "currency": {"score": 85, "weight": 0.15, "reasoning": "Published 2022"},
                "accessibility": {"score": 80, "weight": 0.10, "reasoning": "Open access"},
                "practical_utility": {"score": 90, "weight": 0.10, "reasoning": "Directly applicable"},
            },
            "methodology_codes": ["SYN-01"],
            "thesis_stage_signals": ["HI", "IN"],
            "difficulty_level": "intermediate",
            "relevance_to_discipline_codes": ["psychiatry"],
            "proposed_badges": ["best_beginners"],
            "ai_subtype_signal": "seminal_paper",
            "ai_confidence": 82,
            "trainee_suitability_score": 85,
            "strengths": ["Systematic methods", "PRISMA compliant"],
            "limitations": ["Older studies"],
            "pipeline_run_id": "run-abc",
            "requires_human_review": False,
        }

        draft = parse_appraisal_json(
            llm_output,
            resource_code="test-article",
            model_version="gemini-flash-latest",
        )
        assert draft.quality_score == 88
        assert draft.ai_confidence == 82
        assert draft.requires_human_review is False
        assert "SYN-01" in draft.relevance_to_methodology_codes

    def test_parse_rejects_missing_dimensions(self):
        """Missing a required quality dimension must raise ValueError."""
        from agents.appraisal.tools import parse_appraisal_json

        incomplete = {
            "quality_score": 80,
            "quality_dimensions": {
                "relevance": {"score": 80, "weight": 0.25, "reasoning": "ok"},
                # missing accuracy, authority, currency, accessibility, practical_utility
            },
            "ai_confidence": 75,
            "pipeline_run_id": "run-fail",
        }
        with pytest.raises((ValueError, Exception)):
            parse_appraisal_json(incomplete, resource_code="test", model_version="gemini")
