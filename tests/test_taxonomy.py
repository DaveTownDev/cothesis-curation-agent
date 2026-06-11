"""Live taxonomy JSON loader and classifier validation."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
METH_PATH = ROOT / "data" / "taxonomy" / "live_methodologies.json"
SPEC_PATH = ROOT / "data" / "taxonomy" / "live_specialties.json"
SUB_PATH = ROOT / "data" / "taxonomy" / "live_subtypes.json"
SKILL_PATH = ROOT / "data" / "taxonomy" / "live_skills.json"
VOCAB_PATH = ROOT / "data" / "taxonomy" / "tag_vocabulary.json"

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

    def test_vocabulary_file_exists(self):
        doc = json.loads(VOCAB_PATH.read_text())
        assert "taxonomies" in doc

    def test_mvp_codes_are_subset_of_vocabulary_leaves(self):
        from agents.taxonomy import MVP_METHODOLOGY_CODES, methodology_codes
        live = methodology_codes()
        assert MVP_METHODOLOGY_CODES <= live
        assert len(live) == 140

    def test_loader_matches_vocabulary_leaf_count(self):
        from agents.shared.tag_vocabulary import methodology_leaf_codes, specialty_codes, subtype_codes, skill_codes
        assert len(methodology_leaf_codes()) == 140
        assert len(specialty_codes()) == 78
        assert len(subtype_codes()) == 74
        assert len(skill_codes()) == 16

    def test_skills_json_has_sixteen_canonical_codes(self):
        skill = json.loads(SKILL_PATH.read_text())
        codes = {e["code"] for e in skill["skills"]}
        assert skill["count"] == 16
        assert codes == {f"FS-{i:02d}" for i in range(1, 17)}

    def test_subtypes_include_chapter_from_vocabulary(self):
        from agents.shared.tag_vocabulary import subtype_codes
        assert "chapter" in subtype_codes()

    def test_build_skill_guide_lists_all_codes(self):
        from agents.taxonomy import build_skill_guide, skill_codes
        guide = build_skill_guide()
        for code in sorted(skill_codes()):
            assert code in guide


class TestClassifierLiveCodeValidation:
    def test_accepts_vocabulary_leaf_code(self):
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

    def test_rejects_parent_category_methodology(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="Invalid methodology code"):
            ClassificationResult(**{**VALID_BASE, "methodology_codes": ["EXP"]})

    def test_accepts_specialty_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "discipline_codes": ["PSYCH"]})
        assert r.discipline_codes == ["PSYCH"]

    def test_accepts_legacy_specialty_slug_normalized_to_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "discipline_codes": ["cardiology"]})
        assert r.discipline_codes == ["CARDIO"]

    def test_rejects_unknown_specialty(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="Invalid specialty code"):
            ClassificationResult(**{**VALID_BASE, "discipline_codes": ["psychiatry"]})

    def test_accepts_thesis_stage_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "stage_codes": ["IN-02", "EV-03"]})
        assert r.stage_codes == ["IN-02", "EV-03"]

    def test_accepts_domain_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "domain_codes": ["DIGHEALTH"]})
        assert r.domain_codes == ["DIGHEALTH"]

    def test_accepts_live_subtype_for_type(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{
            **VALID_BASE,
            "resource_subtype_code": "seminal_paper",
        })
        assert r.resource_subtype_code == "seminal_paper"

    def test_accepts_book_chapter_subtype_pair(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{
            **VALID_BASE,
            "resource_type_code": "book",
            "resource_subtype_code": "chapter",
        })
        assert r.resource_subtype_code == "chapter"

    def test_rejects_unknown_subtype_code(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="Invalid resource_subtype_code"):
            ClassificationResult(**{**VALID_BASE, "resource_subtype_code": "journal_article"})

    def test_rejects_subtype_type_mismatch(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="belongs to"):
            ClassificationResult(**{
                **VALID_BASE,
                "resource_type_code": "book",
                "resource_subtype_code": "seminal_paper",
            })

    def test_book_chapter_requires_null_subtype(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="book_chapter"):
            ClassificationResult(**{
                **VALID_BASE,
                "resource_type_code": "book_chapter",
                "resource_subtype_code": "textbook",
            })
        ok = ClassificationResult(**{
            **VALID_BASE,
            "resource_type_code": "book_chapter",
            "resource_subtype_code": None,
        })
        assert ok.resource_subtype_code is None

    def test_accepts_live_skill_code(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "skill_codes": ["FS-02"]})
        assert r.skill_codes == ["FS-02"]

    def test_normalizes_skill_code_padding(self):
        from agents.shared.schema import ClassificationResult
        r = ClassificationResult(**{**VALID_BASE, "skill_codes": ["fs-2"]})
        assert r.skill_codes == ["FS-02"]

    def test_rejects_unknown_skill_code(self):
        from agents.shared.schema import ClassificationResult
        with pytest.raises(ValidationError, match="Invalid skill code"):
            ClassificationResult(**{**VALID_BASE, "skill_codes": ["FS-99"]})
