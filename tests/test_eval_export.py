"""Gold eval case export contract (mirrors console/lib/eval-export.ts)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestEvalExport:
    def test_build_hitl_case_has_required_fields(self):
        from eval.build_gold_case import build_gold_eval_case, validate_gold_case

        draft = {
            "title": "PRISMA checklist",
            "url": "https://example.org/prisma",
            "resource_type_code": "reporting_guideline",
            "methodology_codes": ["SYN-01"],
            "stage_codes": ["HI"],
            "discipline_codes": ["GENMED"],
            "skill_codes": ["literature_search"],
            "quality_score": 88,
            "ai_confidence": 82,
            "editorial_status": "proposed",
        }
        case = build_gold_eval_case(
            resource_code="hitl-test-001",
            draft=draft,
            origin="hitl",
            pipeline_run_id="run-abc",
        )
        assert validate_gold_case(case) == []
        assert case["eval_id"] == "hitl-test-001"
        assert case["source"]["origin"] == "hitl"
        assert case["expected_classification"]["resource_type_code"] == "reporting_guideline"
        assert "SYN-01" in case["expected_classification"]["methodology_codes"]
        assert len(case["conversation"]) == 1
        assert case["conversation"][0]["user_content"]["parts"][0]["text"]

    def test_hitl_case_aggregate_round_trip(self, tmp_path):
        from eval.build_gold_case import build_gold_eval_case
        from scripts.aggregate_gold_set import write_gold_set

        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()
        case = build_gold_eval_case(
            resource_code="roundtrip_hitl",
            draft={
                "title": "Test",
                "url": "https://example.org",
                "resource_type_code": "article",
                "methodology_codes": ["SYN-02"],
                "editorial_status": "proposed",
            },
            origin="hitl",
        )
        (cases_dir / "roundtrip_hitl.json").write_text(
            json.dumps(case, indent=2) + "\n",
            encoding="utf-8",
        )
        out = tmp_path / "gold_set.json"
        doc = write_gold_set(out, cases_dir)
        assert len(doc["eval_cases"]) == 1
        assert doc["eval_cases"][0]["eval_id"] == "roundtrip_hitl"
        assert "source" not in doc["eval_cases"][0]

    def test_schema_file_loads(self):
        schema_path = ROOT / "eval" / "schemas" / "gold_case.schema.json"
        if not schema_path.is_file():
            pytest.skip("gold_case.schema.json not present")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["required"] == ["eval_id", "source", "conversation"]
        assert "hitl" in schema["properties"]["source"]["properties"]["origin"]["enum"]
