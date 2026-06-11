"""Taxonomy audit scoring and validation logic (no Firestore)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestValidateTaxonomyDraft:
    def test_optional_type_empty_methodology_warns_not_fail(self):
        from agents.shared.taxonomy_rules import validate_taxonomy_draft
        issues = validate_taxonomy_draft({
            "resource_type_code": "software",
            "resource_subtype_code": "project_management",
            "methodology_codes": [],
        })
        assert not any(i["sev"] == "fail" for i in issues)
        assert not any(i["field"] == "methodology_codes" for i in issues)

    def test_article_empty_methodology_warns(self):
        from agents.shared.taxonomy_rules import validate_taxonomy_draft
        issues = validate_taxonomy_draft({
            "resource_type_code": "article",
            "resource_subtype_code": "methodology_paper",
            "methodology_codes": [],
        })
        assert any(
            i["field"] == "methodology_codes" and "required" in i["msg"]
            for i in issues
        )

    def test_subtype_parent_mismatch_fails(self):
        from agents.shared.taxonomy_rules import validate_taxonomy_draft
        issues = validate_taxonomy_draft({
            "resource_type_code": "article",
            "resource_subtype_code": "project_management",
            "methodology_codes": ["SYN-01"],
        })
        assert any(i["sev"] == "fail" and i["field"] == "resource_subtype_code" for i in issues)


class TestScoreAgainstGold:
    def test_detects_methodology_set_mismatch(self):
        from scripts.taxonomy_audit import score_against_gold
        mm = score_against_gold(
            {"methodology_codes": ["OBS-01"]},
            {"methodology_codes": ["SYN-01"]},
        )
        assert mm and mm[0]["field"] == "methodology_codes"

    def test_empty_methodology_match_for_software(self):
        from scripts.taxonomy_audit import score_against_gold
        mm = score_against_gold(
            {"resource_type_code": "software", "methodology_codes": []},
            {"resource_type_code": "software", "methodology_codes": []},
        )
        assert mm == []


class TestRunAuditFixture:
    def test_fixture_run_aggregates_by_type(self, tmp_path):
        from scripts.taxonomy_audit import load_gold_cases, run_audit
        gold = load_gold_cases()
        fixture = [
            {
                "resource_code": "gold-covidence",
                "draft": {
                    "resource_type_code": "software",
                    "resource_subtype_code": "project_management",
                    "methodology_codes": [],
                    "skill_codes": ["FS-03"],
                },
            }
        ]
        report = run_audit(fixture, gold)
        assert report["aggregate"]["n"] == 1
        assert report["aggregate"]["gold_matched"] == 1
        assert "software" in report["aggregate"]["by_type"]
