"""
Code-mapping tests — explicitly required by docs/EVAL.md:
"code-mapping (RS->SYN etc.)"

Verifies the classifier correctly emits platform codes and that the
legacy-code crosswalk from docs/TAXONOMY.md is enforced.

Platform codes (agents emit): SYN-01, SYN-02, OBS-01, EVAL-01
Legacy display codes (must be rejected): RS-01, RS-04, OD-01, OD-06
"""
import pytest
from pydantic import ValidationError


VALID_BASE = {
    "resource_type_code": "article",
    "relevance_score": 0.8,
    "classification_confidence": 0.85,
    "access_type": "free",
}


class TestLegacyCodeRejection:
    """The classifier must NEVER emit legacy RS-/OD-/EI-/QI- codes."""

    def test_rejects_rs01_narrative_systematic_review(self):
        """RS-01 → should be SYN-01."""
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="RS-01"):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["RS-01"]})

    def test_rejects_rs04_scoping_review(self):
        """RS-04 → should be SYN-02."""
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="RS-04"):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["RS-04"]})

    def test_rejects_od01_chart_review(self):
        """OD-01 → should be OBS-01."""
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="OD-01"):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["OD-01"]})

    def test_rejects_od06_clinical_audit(self):
        """OD-06 → should be EVAL-01."""
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="OD-06"):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["OD-06"]})

    def test_rejects_ei_prefix(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["EI-03"]})

    def test_rejects_qi_prefix(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["QI-01"]})

    def test_rejects_mixed_legacy_and_platform(self):
        """Even one legacy code in a mixed list must be rejected."""
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["SYN-01", "RS-04"]})


class TestPlatformCodeAcceptance:
    """MVP and live platform codes must be accepted."""

    def test_accepts_syn01_narrative_systematic_review(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["SYN-01"]})
        assert "SYN-01" in r.methodology_codes

    def test_accepts_syn02_scoping_review(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["SYN-02"]})
        assert "SYN-02" in r.methodology_codes

    def test_accepts_obs01_chart_review(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["OBS-01"]})
        assert "OBS-01" in r.methodology_codes

    def test_accepts_eval01_clinical_audit(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["EVAL-01"]})
        assert "EVAL-01" in r.methodology_codes

    def test_accepts_multiple_platform_codes(self):
        """A resource may be tagged with multiple MVP codes."""
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["SYN-01", "SYN-02"]})
        assert set(r.methodology_codes) == {"SYN-01", "SYN-02"}

    def test_accepts_empty_codes_for_non_methodology_resources(self):
        """Funding / community resources may have no methodology codes."""
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "resource_type_code": "funding",
                                    "methodology_codes": []})
        assert r.methodology_codes == []

    def test_accepts_live_non_mvp_platform_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "methodology_codes": ["CASE-01"]})
        assert r.methodology_codes == ["CASE-01"]


class TestCrossWalkDocumented:
    """Verify the crosswalk table from docs/TAXONOMY.md is in LEGACY_METHODOLOGY_PREFIXES."""

    def test_rs_prefix_in_legacy_set(self):
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        assert "RS-" in LEGACY_METHODOLOGY_PREFIXES

    def test_od_prefix_in_legacy_set(self):
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        assert "OD-" in LEGACY_METHODOLOGY_PREFIXES

    def test_ei_prefix_in_legacy_set(self):
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        assert "EI-" in LEGACY_METHODOLOGY_PREFIXES

    def test_qi_prefix_in_legacy_set(self):
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        assert "QI-" in LEGACY_METHODOLOGY_PREFIXES
