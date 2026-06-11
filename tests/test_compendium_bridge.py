"""
Tests for agents/shared/compendium_bridge.py — vocabulary-native tags[] contract.
"""
import pytest

from agents.shared.compendium_bridge import (
    draft_record_to_vocabulary_tags,
    has_trusted_path_methodology,
    to_compendium_record,
)
from agents.shared.tag_vocabulary import demo_retag_resources


MINIMAL_RESOURCE = {
    "resource_code": "syn01-article-test-001",
    "title": "PRISMA 2020 statement: updated guidelines for systematic reviews",
    "url": "https://doi.org/10.1136/bmj.n71",
    "resource_type_code": "article",
    "resource_subtype_code": "primary_guideline",
    "editorial_description": "An updated reporting guideline for systematic reviews.",
    "editorial_description_plain": "A checklist that helps researchers report their literature reviews clearly.",
    "methodology_codes": ["SYN-04"],
    "access_type": "open_access",
    "classification_confidence": 0.95,
    "editorial_status": "published",
}

FULL_RESOURCE = {
    **MINIMAL_RESOURCE,
    "stage_codes": ["SH-01"],
    "discipline_codes": ["CARDIO", "PSYCH"],
    "skill_codes": ["FS-02"],
    "domain_codes": ["DIGHEALTH"],
    "quality_score": 88.0,
    "ai_confidence": 91.0,
    "doi": "10.1136/bmj.n71",
    "pmid": "33782057",
}


def _tags_by_taxonomy(tags: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for t in tags:
        out.setdefault(t["taxonomy"], []).append(t["code"])
    return out


class TestDraftRecordToVocabularyTags:
    def test_methodology_leaf_tags(self):
        tags = draft_record_to_vocabulary_tags(MINIMAL_RESOURCE)
        meth = [t for t in tags if t["taxonomy"] == "methodology"]
        assert meth == [{"taxonomy": "methodology", "code": "SYN-04", "confidence": 0.95}]

    def test_resource_type_subtype_tag(self):
        tags = draft_record_to_vocabulary_tags(MINIMAL_RESOURCE)
        rt = [t for t in tags if t["taxonomy"] == "resource_type"]
        assert rt[0]["code"] == "primary_guideline"

    def test_book_chapter_maps_to_chapter_tag(self):
        r = {**MINIMAL_RESOURCE, "resource_type_code": "book_chapter", "resource_subtype_code": None}
        tags = draft_record_to_vocabulary_tags(r)
        rt = [t for t in tags if t["taxonomy"] == "resource_type"]
        assert rt == [{"taxonomy": "resource_type", "code": "chapter", "confidence": 0.95}]

    def test_specialty_codes_in_tags(self):
        tags = draft_record_to_vocabulary_tags(FULL_RESOURCE)
        spec = [t["code"] for t in tags if t["taxonomy"] == "specialty"]
        assert spec == ["CARDIO", "PSYCH"]

    def test_thesis_stages_in_tags(self):
        tags = draft_record_to_vocabulary_tags(FULL_RESOURCE)
        thesis = [t["code"] for t in tags if t["taxonomy"] == "thesis"]
        assert thesis == ["SH-01"]

    def test_domains_in_tags(self):
        tags = draft_record_to_vocabulary_tags(FULL_RESOURCE)
        domains = [t for t in tags if t["taxonomy"] == "cross_specialty_domain"]
        assert domains[0]["code"] == "DIGHEALTH"

    def test_per_tag_confidence_from_classification_confidence(self):
        tags = draft_record_to_vocabulary_tags(MINIMAL_RESOURCE)
        assert all(t["confidence"] == 0.95 for t in tags)

    def test_default_confidence_when_missing(self):
        r = {k: v for k, v in MINIMAL_RESOURCE.items() if k != "classification_confidence"}
        tags = draft_record_to_vocabulary_tags(r)
        assert all(t["confidence"] == 0.85 for t in tags)


class TestTrustedPath:
    def test_leaf_methodology_enables_trusted_path(self):
        assert has_trusted_path_methodology(MINIMAL_RESOURCE) is True

    def test_no_methodology_fails_trusted_path(self):
        r = {**MINIMAL_RESOURCE, "methodology_codes": []}
        assert has_trusted_path_methodology(r) is False

    def test_parent_category_not_trusted_leaf(self):
        r = {**MINIMAL_RESOURCE, "methodology_codes": ["SYN"]}
        assert has_trusted_path_methodology(r) is False


class TestToCompendiumRecord:
    def test_vocabulary_native_shape(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["title"] == MINIMAL_RESOURCE["title"]
        assert out["url"] == MINIMAL_RESOURCE["url"]
        assert out["editorial_description"] == MINIMAL_RESOURCE["editorial_description"]
        assert out["source_tool"] == "claude"
        assert isinstance(out["tags"], list)
        assert len(out["tags"]) >= 2

    def test_plain_description_maps_to_long_field(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["editorial_description_long"] == MINIMAL_RESOURCE["editorial_description_plain"]

    def test_access_type_normalisation(self):
        out = to_compendium_record(MINIMAL_RESOURCE)
        assert out["access_type"] == "free"

    def test_no_internal_fields_leaked(self):
        out = to_compendium_record(FULL_RESOURCE)
        internal = {
            "resource_code", "quality_score", "ai_confidence", "classification_confidence",
            "methodology_codes", "discipline_codes", "stage_codes", "skill_codes", "domain_codes",
        }
        assert not (set(out.keys()) & internal)

    def test_identifiers_mapped(self):
        out = to_compendium_record(FULL_RESOURCE)
        assert out["doi"] == "10.1136/bmj.n71"
        assert out["pmid"] == "33782057"


class TestDemoRetagAlignment:
    """Spot-check draft shapes that mirror demo retag answer key tags."""

    @pytest.mark.parametrize("resource_id,draft_fields,expected_taxonomy_codes", [
        (
            "demo-dataset-001",
            {
                "resource_type_code": "dataset",
                "resource_subtype_code": "teaching_dataset",
                "methodology_codes": ["OBS-12"],
                "discipline_codes": ["ICU"],
                "domain_codes": ["DIGHEALTH"],
                "stage_codes": ["IN-02"],
            },
            {
                "resource_type": ["teaching_dataset"],
                "methodology": ["OBS-12"],
                "specialty": ["ICU"],
                "cross_specialty_domain": ["DIGHEALTH"],
                "thesis": ["IN-02"],
            },
        ),
        (
            "demo-chapter-001",
            {
                "resource_type_code": "book_chapter",
                "methodology_codes": ["SYN-04"],
                "stage_codes": ["TH-01"],
            },
            {
                "resource_type": ["chapter"],
                "methodology": ["SYN-04"],
                "thesis": ["TH-01"],
            },
        ),
    ])
    def test_draft_tags_match_demo_key_subset(
        self, resource_id, draft_fields, expected_taxonomy_codes,
    ):
        demo = next(r for r in demo_retag_resources() if r["resource_id"] == resource_id)
        draft = {**MINIMAL_RESOURCE, **draft_fields}
        got = _tags_by_taxonomy(draft_record_to_vocabulary_tags(draft))
        for tax, codes in expected_taxonomy_codes.items():
            assert got.get(tax) == codes
        demo_by_tax = _tags_by_taxonomy(demo["tags"])
        for tax, codes in expected_taxonomy_codes.items():
            assert demo_by_tax.get(tax) == codes
