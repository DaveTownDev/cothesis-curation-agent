"""
Tests for agents/shared/compendium_bridge.py

Committed before implementation — all tests must fail initially.
Never weaken these tests to make them pass; fix the code instead.

The bridge translates an approved Firestore `resources` record into
an ImportCandidate dict for POST /api/import/json.
"""
import pytest
from agents.shared.compendium_bridge import to_compendium_record


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_RESOURCE = {
    "resource_code": "syn01-article-test-001",
    "title": "PRISMA 2020 statement: updated guidelines for systematic reviews",
    "url": "https://doi.org/10.1136/bmj.n71",
    "resource_type_code": "article",
    "editorial_description": "An updated reporting guideline for systematic reviews.",
    "editorial_description_plain": "A checklist that helps researchers report their literature reviews clearly.",
    "methodology_codes": ["SYN-01"],
    "access_type": "open_access",
    "editorial_status": "published",
}

FULL_RESOURCE = {
    **MINIMAL_RESOURCE,
    "resource_subtype_code": "meta_analysis",
    "stage_codes": ["SY", "RE"],
    "discipline_codes": ["cardiology", "Adult-Psychiatry"],
    "skill_codes": ["SYN-01-S01"],
    "quality_score": 88.0,
    "ai_confidence": 91.0,
    "relevance_score": 0.92,
    "classification_confidence": 0.95,
    "proposed_badges": ["editors_choice", "best_free"],
    "difficulty_level": "intermediate",
    "summary": "The PRISMA 2020 statement provides 27 items for reporting systematic reviews.",
    "editorial_reviewed_by": "david@cothesis.ai",
    "editorial_reviewed_at": "2026-06-05T12:00:00Z",
    "doi": "10.1136/bmj.n71",
    "pmid": "33782057",
    "requires_human_review": False,
}


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

class TestRequiredFields:
    def test_title_mapped(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["title"] == MINIMAL_RESOURCE["title"]

    def test_url_mapped(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["url"] == MINIMAL_RESOURCE["url"]

    def test_resource_type_mapped(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["resource_type"] == "article"

    def test_description_is_editorial_description(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["description"] == MINIMAL_RESOURCE["editorial_description"]

    def test_source_tool_is_claude(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["source_tool"] == "claude"


# ---------------------------------------------------------------------------
# Methodology codes — platform codes pass through unchanged
# ---------------------------------------------------------------------------

class TestMethodologyCodes:
    def test_syn_codes_pass_through(self):
        r = {**MINIMAL_RESOURCE, "methodology_codes": ["SYN-01", "SYN-02"]}
        out = to_compendium_record(r)
        assert out["methodology_tags"] == ["SYN-01", "SYN-02"]

    def test_obs_codes_pass_through(self):
        r = {**MINIMAL_RESOURCE, "methodology_codes": ["OBS-01"]}
        out = to_compendium_record(r)
        assert out["methodology_tags"] == ["OBS-01"]

    def test_eval_codes_pass_through(self):
        r = {**MINIMAL_RESOURCE, "methodology_codes": ["EVAL-01"]}
        out = to_compendium_record(r)
        assert out["methodology_tags"] == ["EVAL-01"]

    def test_empty_methodology_codes(self):
        r = {**MINIMAL_RESOURCE, "methodology_codes": []}
        out = to_compendium_record(r)
        assert out["methodology_tags"] == []


# ---------------------------------------------------------------------------
# Access type normalisation
# ---------------------------------------------------------------------------

class TestAccessType:
    @pytest.mark.parametrize("agent_val,expected", [
        ("free", "free"),
        ("open_access", "free"),          # open_access normalises to free
        ("freemium", "freemium"),
        ("paid", "paid"),
        ("subscription", "subscription"),
        ("institutional", "institutional"),
    ])
    def test_access_type_normalisation(self, agent_val, expected):
        r = {**MINIMAL_RESOURCE, "access_type": agent_val}
        out = to_compendium_record(r)
        assert out["access_type"] == expected

    def test_missing_access_type_defaults_to_free(self):
        r = {k: v for k, v in MINIMAL_RESOURCE.items() if k != "access_type"}
        out = to_compendium_record(r)
        assert out["access_type"] == "free"


# ---------------------------------------------------------------------------
# Discipline codes → specialty_tags
# ---------------------------------------------------------------------------

class TestSpecialtyTags:
    def test_discipline_codes_mapped_to_specialty_tags(self):
        out = to_compendium_record(FULL_RESOURCE)
        assert out["specialty_tags"] == ["cardiology", "adult-psychiatry"]

    def test_empty_discipline_codes(self):
        r = {**MINIMAL_RESOURCE, "discipline_codes": []}
        out = to_compendium_record(r)
        assert out["specialty_tags"] == []

    def test_missing_discipline_codes(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["specialty_tags"] == []


# ---------------------------------------------------------------------------
# Subtype
# ---------------------------------------------------------------------------

class TestSubtype:
    def test_subtype_mapped(self):
        out = to_compendium_record(FULL_RESOURCE)
        assert out["subtype"] == "meta_analysis"

    def test_missing_subtype_is_absent_or_none(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out.get("subtype") is None


# ---------------------------------------------------------------------------
# Plain description in discovery_context
# ---------------------------------------------------------------------------

class TestDiscoveryContext:
    def test_plain_description_in_discovery_context(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["discovery_context"] == MINIMAL_RESOURCE["editorial_description_plain"]

    def test_missing_plain_description_omits_discovery_context(self):
        r = {k: v for k, v in MINIMAL_RESOURCE.items() if k != "editorial_description_plain"}
        out = to_compendium_record(r)
        assert out.get("discovery_context") is None


# ---------------------------------------------------------------------------
# Identifiers (DOI, PMID, ISBN)
# ---------------------------------------------------------------------------

class TestIdentifiers:
    def test_doi_mapped(self):
        out = to_compendium_record(FULL_RESOURCE)
        assert out["doi"] == "10.1136/bmj.n71"

    def test_pmid_mapped(self):
        out = to_compendium_record(FULL_RESOURCE)
        assert out["pmid"] == "33782057"

    def test_missing_identifiers_absent(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out.get("doi") is None
        assert out.get("pmid") is None
        assert out.get("isbn") is None


# ---------------------------------------------------------------------------
# Output shape — no unexpected fields, no internal pipeline fields leaked
# ---------------------------------------------------------------------------

ALLOWED_OUTPUT_KEYS = {
    "title", "url", "description", "resource_type", "subtype",
    "methodology_tags", "specialty_tags", "access_type", "doi", "isbn", "pmid",
    "github_url", "authors", "publisher", "journal_name",
    "platform", "year", "language", "source_tool", "discovery_context",
}

class TestOutputShape:
    def test_no_internal_fields_leaked(self):
        out = to_compendium_record(FULL_RESOURCE)
        internal_fields = {
            "resource_code", "editorial_status", "quality_score", "ai_confidence",
            "relevance_score", "classification_confidence", "requires_human_review",
            "stage_codes", "skill_codes", "discipline_codes", "proposed_badges", "summary",
            "editorial_reviewed_by", "editorial_reviewed_at",
        }
        leaked = set(out.keys()) & internal_fields
        assert not leaked, f"Internal fields leaked into Compendium record: {leaked}"

    def test_output_keys_are_allowed(self):
        out = to_compendium_record(FULL_RESOURCE)
        unexpected = set(out.keys()) - ALLOWED_OUTPUT_KEYS
        assert not unexpected, f"Unexpected keys in output: {unexpected}"

    def test_minimal_record_produces_valid_output(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["title"]
        assert out["url"]
        assert out["resource_type"]
        assert out["description"]
        assert out["source_tool"] == "claude"

    def test_difficulty_level_not_in_import_candidate(self):
        # difficulty_level is not an ImportCandidate field — should not appear
        out = to_compendium_record(FULL_RESOURCE)
        assert "difficulty_level" not in out


# ---------------------------------------------------------------------------
# Resource type passthrough (all 14 valid types)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rtype", [
    "article", "book", "book_chapter", "video", "podcast", "software",
    "reporting_guideline", "course", "web_guide", "template",
    "visual_reference", "dataset", "community", "funding",
])
def test_all_resource_types_pass_through(rtype):
    r = {**MINIMAL_RESOURCE, "resource_type_code": rtype}
    out = to_compendium_record(r)
    assert out["resource_type"] == rtype
