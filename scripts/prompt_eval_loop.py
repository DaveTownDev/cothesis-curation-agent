"""
Prompt lab Cloud Run Job — offline prompt improvement cycle.

  python -m scripts.prompt_eval_loop
  python -m scripts.prompt_eval_loop --dry-run
  python -m scripts.prompt_eval_loop --max-cases 5

Reads eval_failure_bucket, writes prompt_proposals + prompt_lab_runs.
Never writes to agents/prompts/ on disk.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Optional

from agents.prompt_lab.tools import (
    analyze_failures,
    complete_lab_run,
    create_lab_run,
    default_max_cases,
    draft_unified_diff,
    fetch_pending_failures,
    mark_failures_consumed,
    read_eval_summary,
    set_active_lab_run_id,
    write_proposal_doc,
)
from agents.shared.firestore_schemas import (
    EvalDelta,
    LabRunStatus,
    PromptProposalDoc,
    ProposalStatus,
)

logger = logging.getLogger(__name__)


def run_lab_cycle(
    *,
    max_cases: Optional[int] = None,
    dry_run: bool = False,
    check_regression: bool = True,
    db=None,
    benchmark_runner=None,
) -> dict[str, Any]:
    """
    Deterministic prompt-lab cycle (Job path + integration tests).

    benchmark_runner: optional callable(subset, check_regression) -> dict with
        exit_code and eval_delta fields; defaults to run_benchmark_gate.
    """
    cap = max_cases if max_cases is not None else default_max_cases()
    failures = fetch_pending_failures(cap, db=db)
    if not failures:
        return {"ok": True, "skipped": True, "reason": "no pending failures"}

    failure_ids = [f["id"] for f in failures if f.get("id")]
    if dry_run:
        analysis = analyze_failures(
            json.dumps({"failures": failures}),
            json.dumps(read_eval_summary()),
        )
        return {
            "ok": True,
            "dry_run": True,
            "failure_count": len(failures),
            "analysis": analysis,
        }

    lab_run_id = create_lab_run(failure_ids, max_cases=cap, db=db)
    set_active_lab_run_id(lab_run_id)

    try:
        eval_summary_payload = read_eval_summary()
        analysis = analyze_failures(
            json.dumps({"failures": failures}),
            json.dumps(eval_summary_payload),
        )
        if not analysis.get("ok"):
            raise RuntimeError(analysis.get("error", "analysis failed"))

        diff_result = draft_unified_diff(
            analysis["target_prompt_file"],
            json.dumps(analysis),
        )
        if not diff_result.get("ok"):
            raise RuntimeError(diff_result.get("error", "diff failed"))

        subset = min(len(failures), cap)
        if benchmark_runner is not None:
            gate = benchmark_runner(subset, check_regression)
        else:
            from agents.prompt_lab.tools import run_benchmark_gate

            gate = run_benchmark_gate(subset, check_regression=check_regression)

        eval_delta = EvalDelta(**gate.get("eval_delta", {}))
        proposal = PromptProposalDoc(
            status=ProposalStatus.pending,
            target_prompt_file=diff_result["target_prompt_file"],
            unified_diff=diff_result["unified_diff"],
            rationale=diff_result.get("rationale", analysis.get("rationale", "")),
            failure_bucket_ids=analysis.get("failure_bucket_ids", failure_ids),
            eval_delta=eval_delta,
            lab_run_id=lab_run_id,
        )
        proposal_id = write_proposal_doc(proposal, db=db)
        mark_failures_consumed(failure_ids, lab_run_id, db=db)

        status = LabRunStatus.succeeded if gate.get("exit_code", 1) == 0 else LabRunStatus.failed
        error = None if status == LabRunStatus.succeeded else "benchmark gate failed"
        complete_lab_run(
            lab_run_id,
            status=status,
            proposal_ids=[proposal_id],
            error=error,
            db=db,
        )

        return {
            "ok": status == LabRunStatus.succeeded,
            "lab_run_id": lab_run_id,
            "proposal_id": proposal_id,
            "failure_count": len(failures),
            "benchmark_exit_code": gate.get("exit_code"),
            "analysis": analysis,
        }
    except Exception as exc:
        logger.exception("prompt lab cycle failed")
        complete_lab_run(
            lab_run_id,
            status=LabRunStatus.failed,
            proposal_ids=[],
            error=str(exc),
            db=db,
        )
        return {"ok": False, "lab_run_id": lab_run_id, "error": str(exc)}
    finally:
        set_active_lab_run_id(None)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run offline prompt lab Job cycle")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only; no Firestore writes")
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help=f"Cap failures (default env PROMPT_LAB_MAX_CASES={default_max_cases()})",
    )
    parser.add_argument(
        "--no-check-regression",
        action="store_true",
        help="Skip baseline regression check in benchmark gate",
    )
    args = parser.parse_args()

    result = run_lab_cycle(
        max_cases=args.max_cases,
        dry_run=args.dry_run,
        check_regression=not args.no_check_regression,
    )
    print(json.dumps(result, indent=2, default=str))
    if result.get("skipped"):
        return 0
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
