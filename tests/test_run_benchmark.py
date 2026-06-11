"""Tests for scripts/run_benchmark.py (mocked adk subprocess)."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestRunBenchmark:
    def test_check_thresholds_fail_on_low_rubric(self):
        from scripts.run_benchmark import check_thresholds, load_thresholds

        failures = check_thresholds(
            {"response_match_score": 0.5, "rubric_pass_rate": 0.4, "exit_code": 0},
            load_thresholds(),
        )
        assert any("rubric_pass_rate" in f for f in failures)

    def test_check_regression_detects_drop(self, tmp_path):
        from scripts.run_benchmark import check_regression

        baseline = tmp_path / "baseline.json"
        baseline.write_text(json.dumps({
            "cases_passed": 19,
            "rubric_pass_rate": 0.95,
            "response_match_score": 0.15,
        }), encoding="utf-8")
        failures = check_regression(
            {"cases_passed": 18, "rubric_pass_rate": 0.95, "response_match_score": 0.15},
            baseline,
        )
        assert any("cases_passed" in f for f in failures)

    @patch("scripts.run_benchmark.run_adk_eval")
    @patch("scripts.run_benchmark.run_pytest")
    def test_run_benchmark_writes_summary(self, mock_pytest, mock_adk, tmp_path):
        mock_pytest.return_value = (0, 42)
        mock_adk.return_value = (0, {
            "response_match_score": 0.2,
            "rubric_pass_rate": 0.9,
            "cases_passed": 20,
            "cases_total": 20,
            "exit_code": 0,
        })

        summary_path = tmp_path / "eval-summary.json"
        with patch("scripts.run_benchmark.SUMMARY_PATH", summary_path):
            from scripts.run_benchmark import run_benchmark

            rc = run_benchmark(skip_adk=False, skip_pytest=False)

        assert rc == 0
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["unit_tests"] == 42
        assert summary["cases_passed"] == 20

    def test_parse_adk_eval_output_from_eval_result_json(self):
        from scripts.run_benchmark import _metrics_from_eval_result, parse_adk_eval_output

        result_path = (
            ROOT
            / "agents"
            / "pipeline"
            / ".adk"
            / "eval_history"
            / "pipeline_cothesis_pipeline_gold_1781192495.3983831.evalset_result.json"
        )
        if not result_path.is_file():
            pytest.skip("no local adk eval history")

        direct = _metrics_from_eval_result(result_path)
        assert direct["cases_total"] == 2
        assert direct["cases_passed"] == 2
        assert direct["response_match_score"] is not None
        assert direct["rubric_pass_rate"] is not None

        stderr = f"Writing eval result to file: {result_path}\n"
        stdout = "Eval Run Summary\ncothesis_pipeline_gold:\n  Tests passed: 2\n  Tests failed: 0\n"
        parsed = parse_adk_eval_output(stdout, stderr)
        assert parsed["cases_passed"] == 2
        assert parsed["cases_total"] == 2

    @patch("scripts.run_benchmark.subprocess.run")
    def test_run_adk_eval_invokes_cli(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="response_match_score: 0.18\n19/20 pass",
            stderr="",
        )
        from scripts.run_benchmark import run_adk_eval

        rc, metrics = run_adk_eval()
        assert rc == 0
        cmd = mock_run.call_args[0][0]
        assert cmd[0].endswith("adk")
        assert cmd[1] == "eval"
        assert metrics.get("cases_passed") == 19
        assert metrics.get("cases_total") == 20

    @patch("scripts.run_benchmark.run_adk_eval")
    @patch("scripts.run_benchmark.run_pytest")
    def test_pytest_failure_short_circuits(self, mock_pytest, mock_adk, tmp_path):
        mock_pytest.return_value = (1, None)

        summary_path = tmp_path / "eval-summary.json"
        with patch("scripts.run_benchmark.SUMMARY_PATH", summary_path):
            from scripts.run_benchmark import run_benchmark

            rc = run_benchmark()

        assert rc == 1
        mock_adk.assert_not_called()
