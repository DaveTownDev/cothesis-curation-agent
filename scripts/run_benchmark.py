"""
Benchmark runner: pytest → adk eval → console/data/eval-summary.json.

  python -m scripts.run_benchmark
  python -m scripts.run_benchmark --skip-pytest --skip-adk
  python -m scripts.run_benchmark --check-regression
  python -m scripts.run_benchmark --subset 8
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_CONFIG = ROOT / "eval" / "eval_config.json"


def _adk_executable() -> str:
    """Prefer venv adk next to the active Python interpreter (do not resolve symlinks)."""
    for candidate in (
        Path(sys.executable).parent / "adk",
        ROOT / ".venv" / "bin" / "adk",
    ):
        if candidate.is_file():
            return str(candidate)
    return "adk"


GOLD_SET = ROOT / "eval" / "gold_set.json"
BASELINE_PATH = ROOT / "eval" / "baseline.json"
SUMMARY_PATH = ROOT / "console" / "data" / "eval-summary.json"
AGENT_DIR = ROOT / "agents" / "pipeline"


def run_pytest(quiet: bool = True) -> tuple[int, int | None]:
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q" if quiet else "-v"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    count = None
    m = re.search(r"(\d+) passed", proc.stdout)
    if m:
        count = int(m.group(1))
    return proc.returncode, count


def _metrics_from_eval_result(path: Path) -> dict:
    """Aggregate scores from ADK 2.x evalset_result JSON."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    cases = doc.get("eval_case_results") or []
    rms_scores: list[float] = []
    rubric_scores: list[float] = []
    per_rubric: dict[str, list[float]] = {}
    passed = sum(1 for case in cases if case.get("final_eval_status") == 1)
    for case in cases:
        for metric in case.get("overall_eval_metric_results") or []:
            name = metric.get("metric_name") or ""
            score = metric.get("score")
            if score is None:
                continue
            val = float(score)
            if name == "response_match_score":
                rms_scores.append(val)
            elif name == "rubric_based_final_response_quality_v1":
                rubric_scores.append(val)
                for rubric in (metric.get("details") or {}).get("rubric_scores") or []:
                    rid = rubric.get("rubric_id")
                    rs = rubric.get("score")
                    if rid and rs is not None:
                        per_rubric.setdefault(rid, []).append(float(rs))
    total = len(cases)
    return {
        "response_match_score": round(sum(rms_scores) / len(rms_scores), 4) if rms_scores else None,
        "rubric_pass_rate": round(sum(rubric_scores) / len(rubric_scores), 4) if rubric_scores else None,
        "cases_passed": passed,
        "cases_total": total,
        "per_rubric": {
            rid: round(sum(scores) / len(scores), 4)
            for rid, scores in per_rubric.items()
        },
        "eval_result_path": str(path),
    }


def parse_adk_eval_output(stdout: str, stderr: str) -> dict:
    """Best-effort parse of adk eval stdout/stderr for summary metrics."""
    text = stdout + "\n" + stderr
    metrics: dict = {
        "response_match_score": None,
        "rubric_pass_rate": None,
        "cases_passed": None,
        "cases_total": None,
        "raw_tail": "\n".join(text.strip().splitlines()[-20:]),
    }
    for pattern, key in (
        (r"response_match_score[:\s]+([0-9.]+)", "response_match_score"),
        (r"rubric.*?([0-9.]+)\s*/\s*1", "rubric_pass_rate"),
        (r"(\d+)\s*/\s*(\d+)\s+pass", "cases_fraction"),
        (r"Tests passed:\s*(\d+)", "tests_passed"),
        (r"Tests failed:\s*(\d+)", "tests_failed"),
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            continue
        if key == "cases_fraction":
            metrics["cases_passed"] = int(m.group(1))
            metrics["cases_total"] = int(m.group(2))
        elif key == "tests_passed":
            metrics["cases_passed"] = int(m.group(1))
        elif key == "tests_failed":
            failed = int(m.group(1))
            if metrics.get("cases_passed") is not None:
                metrics["cases_total"] = metrics["cases_passed"] + failed
        else:
            metrics[key] = float(m.group(1))

    result_match = re.search(
        r"Writing eval result to file:\s*(.+\.evalset_result\.json)",
        stderr,
    )
    if result_match:
        result_path = Path(result_match.group(1).strip())
        if result_path.is_file():
            metrics.update(_metrics_from_eval_result(result_path))
    return metrics


def run_adk_eval(subset: int | None = None) -> tuple[int, dict]:
    if not GOLD_SET.is_file():
        raise FileNotFoundError(f"Missing gold set: {GOLD_SET}")

    eval_path = GOLD_SET
    if subset is not None:
        doc = json.loads(GOLD_SET.read_text(encoding="utf-8"))
        doc["eval_cases"] = doc.get("eval_cases", [])[:subset]
        tmp = ROOT / "eval" / "_benchmark_subset.json"
        tmp.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        eval_path = tmp

    cmd = [
        _adk_executable(), "eval",
        str(AGENT_DIR),
        str(eval_path),
        "--config_file_path", str(EVAL_CONFIG),
    ]
    env = {
        **dict(__import__("os").environ),
        "PYTHONPATH": str(ROOT),
        "FIRESTORE_COLLECTION_PREFIX": "eval_",
        "GRPC_ENABLE_FORK_SUPPORT": "1",
    }
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    metrics = parse_adk_eval_output(proc.stdout, proc.stderr)
    metrics["exit_code"] = proc.returncode
    metrics["stdout"] = proc.stdout
    metrics["stderr"] = proc.stderr
    return proc.returncode, metrics


def load_thresholds() -> dict:
    cfg = json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    criteria = cfg.get("criteria", {})
    rubric = criteria.get("rubric_based_final_response_quality_v1", {})
    return {
        "response_match_score": float(criteria.get("response_match_score", 0.12)),
        "rubric_threshold": float(rubric.get("threshold", 0.6)),
    }


def check_thresholds(metrics: dict, thresholds: dict) -> list[str]:
    failures: list[str] = []
    rms = metrics.get("response_match_score")
    if rms is not None and rms < thresholds["response_match_score"]:
        failures.append(
            f"response_match_score {rms} < {thresholds['response_match_score']}"
        )
    rubric = metrics.get("rubric_pass_rate")
    if rubric is not None and rubric < thresholds["rubric_threshold"]:
        failures.append(
            f"rubric_pass_rate {rubric} < {thresholds['rubric_threshold']}"
        )
    if metrics.get("exit_code", 0) != 0 and not failures:
        failures.append(f"adk eval exit code {metrics.get('exit_code')}")
    return failures


def check_regression(summary: dict, baseline_path: Path = BASELINE_PATH) -> list[str]:
    if not baseline_path.is_file():
        return [f"baseline missing: {baseline_path}"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for key in ("response_match_score", "rubric_pass_rate", "cases_passed"):
        base_val = baseline.get(key)
        cur_val = summary.get(key)
        if base_val is None or cur_val is None:
            continue
        if cur_val < base_val:
            failures.append(f"regression on {key}: {cur_val} < baseline {base_val}")
    return failures


def build_summary(
    *,
    pytest_rc: int,
    unit_tests: int | None,
    adk_rc: int | None,
    adk_metrics: dict | None,
) -> dict:
    thresholds = load_thresholds()
    summary: dict = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pytest_exit_code": pytest_rc,
        "unit_tests": unit_tests,
        "thresholds": thresholds,
    }
    if adk_metrics:
        summary.update({
            "adk_exit_code": adk_rc,
            "response_match_score": adk_metrics.get("response_match_score"),
            "rubric_pass_rate": adk_metrics.get("rubric_pass_rate"),
            "cases_passed": adk_metrics.get("cases_passed"),
            "cases_total": adk_metrics.get("cases_total"),
        })
    return summary


def write_summary(summary: dict, path: Path | None = None) -> None:
    out = path or SUMMARY_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_baseline(summary: dict, adk_metrics: dict | None, path: Path = BASELINE_PATH) -> None:
    """Persist regression gate baseline after a green adk eval run."""
    if not adk_metrics or adk_metrics.get("exit_code", 1) != 0:
        return
    if summary.get("cases_passed") is None:
        return
    baseline = {
        "captured_at": summary.get("updated_at"),
        "note": "Captured by scripts.run_benchmark after green adk eval",
        "response_match_score": summary.get("response_match_score"),
        "rubric_pass_rate": summary.get("rubric_pass_rate"),
        "cases_passed": summary.get("cases_passed"),
        "cases_total": summary.get("cases_total"),
        "per_rubric": adk_metrics.get("per_rubric") or {},
    }
    path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")


def run_benchmark(
    *,
    skip_pytest: bool = False,
    skip_adk: bool = False,
    subset: int | None = None,
    check_regression_flag: bool = False,
) -> int:
    pytest_rc = 0
    unit_tests = None
    if not skip_pytest:
        pytest_rc, unit_tests = run_pytest()
        if pytest_rc != 0:
            summary = build_summary(pytest_rc=pytest_rc, unit_tests=unit_tests, adk_rc=None, adk_metrics=None)
            write_summary(summary)
            print("pytest failed", file=sys.stderr)
            return 1

    adk_rc = 0
    adk_metrics: dict | None = None
    if not skip_adk:
        adk_rc, adk_metrics = run_adk_eval(subset=subset)
        threshold_failures = check_thresholds(adk_metrics, load_thresholds())
        if threshold_failures:
            for msg in threshold_failures:
                print(msg, file=sys.stderr)

    summary = build_summary(
        pytest_rc=pytest_rc,
        unit_tests=unit_tests,
        adk_rc=adk_rc,
        adk_metrics=adk_metrics,
    )
    write_summary(summary)
    if not skip_adk and adk_metrics and adk_rc == 0:
        write_baseline(summary, adk_metrics)

    exit_code = 0
    if not skip_adk and adk_metrics:
        exit_code = adk_rc or (1 if check_thresholds(adk_metrics, load_thresholds()) else 0)
    if check_regression_flag:
        reg_failures = check_regression(summary)
        for msg in reg_failures:
            print(msg, file=sys.stderr)
        if reg_failures:
            exit_code = 1

    print(json.dumps(summary, indent=2))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest + adk eval benchmark")
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-adk", action="store_true")
    parser.add_argument("--subset", type=int, default=None, help="Cap eval cases (CI)")
    parser.add_argument("--check-regression", action="store_true")
    args = parser.parse_args()
    return run_benchmark(
        skip_pytest=args.skip_pytest,
        skip_adk=args.skip_adk,
        subset=args.subset,
        check_regression_flag=args.check_regression,
    )


if __name__ == "__main__":
    sys.exit(main())
