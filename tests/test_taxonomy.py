"""Live taxonomy JSON loader and classifier validation."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
METH_PATH = ROOT / "data" / "taxonomy" / "live_methodologies.json"
SPEC_PATH = ROOT / "data" / "taxonomy" / "live_specialties.json"

VALID_BASE = {
    "resource_type_code": "article",
    "relevance_score": 0.8,
    "classification_confidence": 0.85,
    "access_type": "free",
}


class TestLiveTaxonomyFiles:
    def test_json_files_exist_and_parse(self):
        meth = json.loads(METH_PATH.read_text())
        spec = json.loads(SPEC_PATH.read_text())
        assert meth["count"] == len(meth["methodologies"])
        assert spec["count"] == len(spec["specialties"])
        assert "fetched_at" in meth
        assert "fetched_at" in spec

    def test_mvp_codes_are_subset_of_live(self):
        from agents.taxonomy import MVP_METHODOLOGY_CODES, methodology_codes
        live = methodology_codes()
        assert MVP_METHODOLOGY_CODES <= live
        assert len(live) >= 140

    def test_loader_matches_json_count(self):
        from agents.taxonomy import methodology_codes, specialty_slugs
        meth = json.loads(METH_PATH.read_text())
        spec = json.loads(SPEC_PATH.read_text())
        assert len(methodology_codes()) == meth["count"]
        assert len(specialty_slugs()) == spec["count"]


class TestClassifierLiveCodeValidation:
    def test_accepts_live_non_mvp_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["CASE-01"]})
        assert r.methodology_codes == ["CASE-01"]

    def test_normalizes_lowercase_slug_to_uppercase_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["syn-02"]})
        assert r.methodology_codes == ["SYN-02"]

    def test_rejects_unknown_methodology_code(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="Invalid methodology code"):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["FAKE-99"]})

    def test_accepts_live_specialty_slug(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "discipline_codes": ["cardiology"]})
        assert r.discipline_codes == ["cardiology"]

    def test_rejects_unknown_discipline_slug(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="Invalid discipline slug"):
            ClassificationResult(**{**VALID_BASE, "discipline_codes": ["psychiatry"]})
