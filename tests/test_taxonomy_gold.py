"""Validate eval/taxonomy_gold.json against tag_vocabulary (or live taxonomies)."""
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "eval" / "taxonomy_gold.json"

from agents.shared.codes import RESOURCE_TYPES
from agents.shared import tag_vocabulary


def _load_cases() -> list[dict]:
    doc = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    return list(doc.get("cases", []))


@pytest.fixture(scope="module")
def cases():
    return _load_cases()


class TestTaxonomyGoldCoverage:
    def test_at_least_thirty_cases(self, cases):
        assert len(cases) >= 30

    def test_unique_resource_codes(self, cases):
        codes = [c["resource_code"] for c in cases]
        assert len(codes) == len(set(codes))

    def test_stratified_by_type_and_methodology(self, cases):
        strata = Counter()
        for case in cases:
            exp = case.get("expected", {})
            rt = exp.get("resource_type_code", "unknown")
            has_meth = bool(exp.get("methodology_codes"))
            strata[(rt, has_meth)] += 1
        types = {case.get("expected", {}).get("resource_type_code") for case in cases}
        types.discard(None)
        assert len(types) >= 8
        assert any(has_m for _, has_m in strata)
        assert any(not has_m for _, has_m in strata)


class TestTaxonomyGoldValidity:
    def test_resource_types(self, cases):
        for case in cases:
            exp = case["expected"]
            rt = exp.get("resource_type_code")
            assert rt in RESOURCE_TYPES, f"{case['resource_code']}: bad type {rt}"

    def test_subtypes_and_parents(self, cases):
        subtypes = tag_vocabulary.subtype_codes()
        for case in cases:
            exp = case["expected"]
            sub = exp.get("resource_subtype_code")
            rt = exp.get("resource_type_code")
            if not sub:
                continue
            assert sub in subtypes, f"{case['resource_code']}: unknown subtype {sub}"
            parent = tag_vocabulary.subtype_parent(sub)
            assert parent == rt, (
                f"{case['resource_code']}: subtype {sub} parent {parent} != type {rt}"
            )

    def test_methodology_codes(self, cases):
        allowed = tag_vocabulary.methodology_leaf_codes()
        for case in cases:
            for code in case["expected"].get("methodology_codes") or []:
                assert code in allowed, f"{case['resource_code']}: bad methodology {code}"

    def test_skill_codes(self, cases):
        allowed = tag_vocabulary.skill_codes()
        for case in cases:
            for code in case["expected"].get("skill_codes") or []:
                assert code in allowed, f"{case['resource_code']}: bad skill {code}"

    def test_stage_codes(self, cases):
        allowed = tag_vocabulary.thesis_codes()
        for case in cases:
            for code in case["expected"].get("stage_codes") or []:
                assert code in allowed, f"{case['resource_code']}: bad stage {code}"

    def test_specialty_codes(self, cases):
        allowed = tag_vocabulary.specialty_codes()
        for case in cases:
            for code in case["expected"].get("discipline_codes") or []:
                assert code in allowed, f"{case['resource_code']}: bad specialty {code}"

    def test_domain_codes(self, cases):
        allowed = tag_vocabulary.domain_codes()
        for case in cases:
            for code in case["expected"].get("domain_codes") or []:
                assert code in allowed, f"{case['resource_code']}: bad domain {code}"
