"""Tests for scripts/aggregate_gold_set.py."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestAggregateGoldSet:
    def test_strips_metadata_and_sorts_by_eval_id(self, tmp_path):
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()
        (cases_dir / "b_case.json").write_text(
            json.dumps({
                "eval_id": "b_case",
                "source": {"resource_code": "res-b", "origin": "seed"},
                "expected_classification": {"resource_type_code": "article"},
                "conversation": [{"user_content": {"parts": [{"text": "hi"}]}}],
            }),
            encoding="utf-8",
        )
        (cases_dir / "a_case.json").write_text(
            json.dumps({
                "eval_id": "a_case",
                "source": {"resource_code": "res-a", "origin": "hitl"},
                "conversation": [{"user_content": {"parts": [{"text": "hello"}]}}],
            }),
            encoding="utf-8",
        )

        from scripts.aggregate_gold_set import write_gold_set

        out = tmp_path / "gold_set.json"
        doc = write_gold_set(out, cases_dir)

        assert [c["eval_id"] for c in doc["eval_cases"]] == ["a_case", "b_case"]
        assert "source" not in doc["eval_cases"][0]
        assert "expected_classification" not in doc["eval_cases"][1]
        assert doc["eval_set_id"] == "cothesis_pipeline_gold"

        roundtrip = json.loads(out.read_text(encoding="utf-8"))
        assert roundtrip == doc

    def test_rejects_missing_source(self, tmp_path):
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()
        (cases_dir / "bad.json").write_text(
            json.dumps({"eval_id": "x", "conversation": []}),
            encoding="utf-8",
        )
        from scripts.aggregate_gold_set import write_gold_set

        with pytest.raises(ValueError, match="missing source"):
            write_gold_set(tmp_path / "out.json", cases_dir)

    def test_repo_cases_aggregate_to_thirty_with_hitl(self):
        cases_dir = ROOT / "eval" / "cases"
        if not cases_dir.is_dir() or not list(cases_dir.glob("*.json")):
            pytest.skip("seed cases not migrated yet")

        from scripts.aggregate_gold_set import aggregate_cases

        paths = sorted(cases_dir.glob("*.json"))
        doc = aggregate_cases(paths)
        assert len(doc["eval_cases"]) >= 30
        origins = [
            json.loads(p.read_text(encoding="utf-8"))["source"]["origin"]
            for p in paths
        ]
        assert set(origins) >= {"seed", "hitl", "synthetic"}
        assert sum(1 for o in origins if o == "hitl") >= 5
