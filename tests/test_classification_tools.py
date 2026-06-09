"""
Deterministic tests for Classification tools.
Committed BEFORE implementation per docs/EVAL.md.
"""
import pytest
from pydantic import ValidationError


VALID_CLASSIFICATION = {
    "resource_type_code": "article",
    "resource_subtype_code": "seminal_paper",
    "methodology_codes": ["SYN-01"],
    "stage_codes": ["HI", "IN"],
    "relevance_score": 0.85,
    "classification_confidence": 0.9,
    "access_type": "open_access",
    "skip_reason": None,
    "discipline_codes": ["adult-psychiatry"],
    "difficulty_level": "intermediate",
}


class TestClassificationResult:

    def test_parse_valid_classification(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**VALID_CLASSIFICATION)
        assert r.resource_type_code == "article"
        assert r.relevance_score == 0.85

    def test_rejects_legacy_rs_code(self):
        """RS-01 is a legacy display code — must be rejected."""
        from agents.shared.schema import ClassificationResult
        bad = {**VALID_CLASSIFICATION, "methodology_codes": ["RS-01"]}
        with pytest.raises(ValidationError, match="RS-"):
            ClassificationResult(**bad)

    def test_rejects_legacy_od_code(self):
        """OD-06 is a legacy display code — must be rejected."""
        from agents.shared.schema import ClassificationResult
        bad = {**VALID_CLASSIFICATION, "methodology_codes": ["OD-06"]}
        with pytest.raises(ValidationError, match="OD-"):
            ClassificationResult(**bad)

    def test_rejects_invalid_resource_type(self):
        """'journal' is not one of the 14 canonical types."""
        from agents.shared.schema import ClassificationResult
        bad = {**VALID_CLASSIFICATION, "resource_type_code": "journal"}
        with pytest.raises(ValidationError):
            ClassificationResult(**bad)

    def test_accepts_all_14_resource_types(self):
        """All 14 canonical types must be accepted."""
        from agents.shared.schema import ClassificationResult
        from agents.shared.codes import RESOURCE_TYPES
        for rtype in RESOURCE_TYPES:
            r = ClassificationResult(**{**VALID_CLASSIFICATION, "resource_type_code": rtype})
            assert r.resource_type_code == rtype

    def test_rejects_invalid_stage_code(self):
        """Stage codes must be the 6 THESIS codes only."""
        from agents.shared.schema import ClassificationResult
        bad = {**VALID_CLASSIFICATION, "stage_codes": ["XX"]}
        with pytest.raises(ValidationError):
            ClassificationResult(**bad)

    def test_relevance_score_must_be_0_to_1(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError):
            ClassificationResult(**{**VALID_CLASSIFICATION, "relevance_score": 1.5})

    def test_classification_confidence_must_be_0_to_1(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError):
            ClassificationResult(**{**VALID_CLASSIFICATION, "classification_confidence": -0.1})

    def test_skip_reason_marks_non_resource(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{
            **VALID_CLASSIFICATION,
            "skip_reason": "homepage — not a discrete citable resource",
        })
        assert r.skip_reason is not None

    def test_empty_methodology_codes_allowed(self):
        """Some resource types (funding, community) may have no methodology."""
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_CLASSIFICATION, "methodology_codes": []})
        assert r.methodology_codes == []


class TestParseClassificationJson:

    def test_parse_valid_json(self):
        from agents.classification.tools import parse_classification_json
        result = parse_classification_json(VALID_CLASSIFICATION)
        assert result.resource_type_code == "article"
        assert result.classification_confidence == 0.9

    def test_parse_rejects_legacy_code(self):
        from agents.classification.tools import parse_classification_json
        with pytest.raises((ValidationError, ValueError)):
            parse_classification_json({**VALID_CLASSIFICATION, "methodology_codes": ["RS-04"]})

    def test_parse_retry_signal_on_bad_json(self):
        """Returns None (retry signal) for unparseable input."""
        from agents.classification.tools import parse_classification_json
        result = parse_classification_json("not a dict at all")
        assert result is None
