"""Canonical tag vocabulary loader — demo retag key and synonym resolution."""
from __future__ import annotations

import pytest

from agents.shared import tag_vocabulary as tv


class TestVocabularyCounts:
    def test_methodology_leaf_count(self):
        assert len(tv.methodology_leaf_codes()) == 140

    def test_specialty_count(self):
        assert len(tv.specialty_codes()) == 78

    def test_thesis_count(self):
        assert len(tv.thesis_codes()) == 31

    def test_subtype_count(self):
        assert len(tv.subtype_codes()) == 74

    def test_skill_count(self):
        assert len(tv.skill_codes()) == 16

    def test_domain_count(self):
        assert len(tv.domain_codes()) == 11


class TestDemoRetagKey:
    def test_fourteen_demo_resources(self):
        assert len(tv.demo_retag_resources()) == 14

    @pytest.mark.parametrize("resource_id", [
        "demo-article-001",
        "demo-book-001",
        "demo-chapter-001",
        "demo-video-001",
        "demo-podcast-001",
        "demo-software-001",
        "demo-guideline-001",
        "demo-course-001",
        "demo-webguide-001",
        "demo-template-001",
        "demo-visual-001",
        "demo-dataset-001",
        "demo-community-001",
        "demo-funding-001",
    ])
    def test_demo_tags_validate_against_vocabulary(self, resource_id: str):
        item = tv.demo_retag_by_id(resource_id)
        assert item is not None
        for t in item["tags"]:
            taxonomy = t["taxonomy"]
            code = t["code"]
            assert code in tv.valid_codes(taxonomy), (
                f"{resource_id}: {taxonomy}:{code} not in vocabulary"
            )


class TestSpecialtyResolution:
    def test_code_to_slug_cardio(self):
        assert tv.specialty_code_to_slug("CARDIO") == "cardiology"

    def test_slug_to_code_cardiology(self):
        assert tv.specialty_slug_to_code("cardiology") == "CARDIO"

    def test_normalize_psych_code(self):
        assert tv.normalize_specialty_code("PSYCH") == "PSYCH"

    def test_normalize_legacy_slug(self):
        assert tv.normalize_specialty_code("cardiology") == "CARDIO"


class TestThesisStages:
    def test_accepts_phase_code(self):
        assert tv.is_valid_thesis_code("HI")

    def test_accepts_stage_code(self):
        assert tv.is_valid_thesis_code("EV-03")

    def test_accepts_in_02(self):
        assert tv.is_valid_thesis_code("IN-02")


class TestSynonymIndex:
    def test_prisma_resolves_primary_guideline(self):
        hit = tv.resolve_match_term("PRISMA")
        assert hit == ("resource_type", "primary_guideline")

    def test_zotero_resolves_reference_manager(self):
        hit = tv.resolve_match_term("Zotero")
        assert hit == ("resource_type", "reference_manager")


class TestMethodologySubset:
    def test_live_mvp_codes_are_vocabulary_leaves(self):
        from agents.taxonomy import MVP_METHODOLOGY_CODES
        leaves = tv.methodology_leaf_codes()
        assert MVP_METHODOLOGY_CODES <= leaves

    def test_leaf_pattern_matches_syn_04(self):
        assert tv.is_leaf_methodology_code("SYN-04")

    def test_category_exp_not_leaf_pattern(self):
        assert not tv.is_leaf_methodology_code("EXP")


class TestGuideBuilders:
    def test_classification_guide_includes_rules_and_sections(self):
        guide = tv.build_classification_vocabulary_guide()
        assert "Canonical tagging rules" in guide
        assert "Allowed methodology codes" in guide
        assert "Allowed specialty codes" in guide
        assert "THESIS phases and stages" in guide or "thesis" in guide.lower()
