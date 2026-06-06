"""Interactive (adk web) assembly robustness: normalize out-of-enum resource_type_code
and backfill a missing editorial_description, instead of dropping to all-defaults/stubs.
Both were surfaced by the ADK gold eval.
"""
import json

from agents.shared.codes import normalize_resource_type, RESOURCE_TYPES
from agents.reconciliation.agent import assemble_record


def test_normalize_resource_type_aliases():
    assert normalize_resource_type("guideline") == "reporting_guideline"
    assert normalize_resource_type("Guidelines") == "reporting_guideline"
    assert normalize_resource_type("methodological_article") == "article"
    assert normalize_resource_type("research article") == "article"
    assert normalize_resource_type("registry") == "dataset"
    assert normalize_resource_type("GitHub repo") is None or normalize_resource_type("repository") == "software"
    assert normalize_resource_type("article") == "article"   # already canonical
    assert normalize_resource_type("totally unknown xyz") is None
    assert normalize_resource_type(None) is None


def test_assemble_normalizes_bad_type_and_keeps_methodology():
    payload = json.dumps({
        "resource_code": "x-123456", "title": "Guidelines for X", "url": "https://e/x",
        "classification": {
            "resource_type_code": "guideline",          # invalid enum -> should normalize
            "methodology_codes": ["SYN-02"], "relevance_score": 0.8,
            "classification_confidence": 0.8, "access_type": "open_access",
        },
        "editorial": {
            "summary": "A scoping review style overview of X.",  # no editorial_description
            "editorial_description_plain": "A simple guide to X.",
        },
        "appraisal": {"quality_score": 80, "ai_confidence": 70},
    })
    rec = assemble_record(payload)
    # type normalized, not defaulted to 'article'
    assert rec["resource_type_code"] == "reporting_guideline"
    assert rec["resource_type_code"] in RESOURCE_TYPES
    # methodology survived (not wiped by an all-defaults fallback)
    assert "SYN-02" in rec.get("methodology_codes", [])
    # missing editorial_description backfilled from summary (non-empty)
    assert rec["editorial_description"]
