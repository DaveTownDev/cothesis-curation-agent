"""
Prompt lab tools — Firestore I/O, benchmark gate, proposal writer.

Never writes to agents/prompts/ on disk; proposals land in prompt_proposals only.
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from agents.shared.firestore_schemas import (
    EvalDelta,
    EvalFailureBucketDoc,
    LabRunStatus,
    PromptLabRunDoc,
    PromptProposalDoc,
    ProposalStatus,
    prompt_lab_run_to_firestore,
    prompt_proposal_to_firestore,
)
from agents.shared.firestore_utils import (
    COLLECTION_EVAL_FAILURE_BUCKET,
    COLLECTION_PROMPT_LAB_RUNS,
    COLLECTION_PROMPT_PROPOSALS,
    collection_name_for,
    get_firestore_client,
    get_firestore_collection,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
EVAL_SUMMARY_PATH = ROOT / "console" / "data" / "eval-summary.json"
BASELINE_PATH = ROOT / "eval" / "baseline.json"

AGENT_PROMPT_MAP: dict[str, str] = {
    "appraisal": "agents/prompts/appraisal.md",
    "classification": "agents/prompts/classification.md",
    "discovery": "agents/prompts/discovery.md",
    "editorial": "agents/prompts/editorial.md",
    "reconciliation": "agents/prompts/reconciliation.md",
    "qc_panel": "agents/prompts/qc_panel.md",
    "arbiter": "agents/prompts/arbiter.md",
}

# Set by prompt_eval_loop before agent tools run in a Job context.
_ACTIVE_LAB_RUN_ID: Optional[str] = None


def set_active_lab_run_id(lab_run_id: Optional[str]) -> None:
    global _ACTIVE_LAB_RUN_ID
    _ACTIVE_LAB_RUN_ID = lab_run_id


def get_active_lab_run_id() -> Optional[str]:
    return _ACTIVE_LAB_RUN_ID


def default_max_cases() -> int:
    raw = os.environ.get("PROMPT_LAB_MAX_CASES", "10")
    try:
        return max(1, int(raw))
    except ValueError:
        return 10


def resolve_target_prompt(agent: str) -> str:
    key = agent.strip().lower().removesuffix("_agent")
    try:
        return AGENT_PROMPT_MAP[key]
    except KeyError as exc:
        known = ", ".join(sorted(AGENT_PROMPT_MAP))
        raise KeyError(f"Unknown agent {agent!r}; known: {known}") from exc


def _failure_collection(db=None):
    if db is not None:
        return db.collection(collection_name_for(COLLECTION_EVAL_FAILURE_BUCKET))
    return get_firestore_collection(COLLECTION_EVAL_FAILURE_BUCKET)


def _proposal_collection(db=None):
    if db is not None:
        return db.collection(collection_name_for(COLLECTION_PROMPT_PROPOSALS))
    return get_firestore_collection(COLLECTION_PROMPT_PROPOSALS)


def _lab_run_collection(db=None):
    if db is not None:
        return db.collection(collection_name_for(COLLECTION_PROMPT_LAB_RUNS))
    return get_firestore_collection(COLLECTION_PROMPT_LAB_RUNS)


def fetch_pending_failures(
    max_cases: Optional[int] = None,
    *,
    db=None,
) -> list[dict[str, Any]]:
    """Return pending failure bucket docs as {id, ...fields}."""
    cap = max_cases if max_cases is not None else default_max_cases()
    coll = _failure_collection(db)
    query = (
        coll.where("consumed_by_lab_run_id", "==", None)
        .order_by("created_at", direction="DESCENDING")
        .limit(cap)
    )
    out: list[dict[str, Any]] = []
    for snap in query.stream():
        data = snap.to_dict() or {}
        data["id"] = snap.id
        out.append(data)
    return out


def read_failure_bucket(max_cases: Optional[int] = None) -> dict:
    """Tool: load pending eval_failure_bucket records."""
    failures = fetch_pending_failures(max_cases)
    return {
        "count": len(failures),
        "max_cases": max_cases if max_cases is not None else default_max_cases(),
        "failures": failures,
    }


def read_eval_summary() -> dict:
    """Tool: load console/data/eval-summary.json."""
    if not EVAL_SUMMARY_PATH.is_file():
        return {"found": False, "path": str(EVAL_SUMMARY_PATH), "summary": {}}
    summary = json.loads(EVAL_SUMMARY_PATH.read_text(encoding="utf-8"))
    return {"found": True, "path": str(EVAL_SUMMARY_PATH), "summary": summary}


def analyze_failures(failures_json: str, eval_summary_json: str = "{}") -> dict:
    """Tool: cluster failures and pick a target prompt file."""
    try:
        payload = json.loads(failures_json)
    except (json.JSONDecodeError, TypeError):
        payload = {}
    failures = payload if isinstance(payload, list) else payload.get("failures", [])
    if not failures:
        return {"ok": False, "error": "no failures to analyze"}

    try:
        eval_payload = json.loads(eval_summary_json) if eval_summary_json else {}
    except (json.JSONDecodeError, TypeError):
        eval_payload = {}
    eval_summary = (
        eval_payload.get("summary", eval_payload)
        if isinstance(eval_payload, dict)
        else {}
    )

    agent_counts = Counter(str(f.get("agent", "classification")) for f in failures)
    target_agent = agent_counts.most_common(1)[0][0]
    target_prompt_file = resolve_target_prompt(target_agent)

    field_counts = Counter(str(f.get("field", "unknown")) for f in failures)
    patterns = [
        {
            "agent": target_agent,
            "field": field,
            "count": count,
            "failure_ids": [
                f["id"]
                for f in failures
                if f.get("field") == field and f.get("agent") == target_agent
            ],
            "labels": [
                f.get("human_label", "")
                for f in failures
                if f.get("field") == field and f.get("agent") == target_agent
            ][:5],
        }
        for field, count in field_counts.most_common(3)
    ]

    labels = [f.get("human_label", "") for f in failures[:3] if f.get("human_label")]
    rationale = (
        f"Cluster of {len(failures)} failure(s) on {target_agent} "
        f"(top field: {field_counts.most_common(1)[0][0]}). "
        + ("; ".join(labels) if labels else "See failure bucket for details.")
    )

    return {
        "ok": True,
        "target_agent": target_agent,
        "target_prompt_file": target_prompt_file,
        "failure_bucket_ids": [f.get("id") for f in failures if f.get("id")],
        "failure_patterns": patterns,
        "rationale": rationale,
        "eval_summary_snapshot": {
            "response_match_score": eval_summary.get("response_match_score"),
            "rubric_pass_rate": eval_summary.get("rubric_pass_rate"),
            "cases_passed": eval_summary.get("cases_passed"),
        },
    }


def read_current_prompt(prompt_file: str) -> dict:
    """Tool: read agents/prompts/*.md (read-only)."""
    rel = prompt_file.strip()
    if not rel.startswith("agents/prompts/") or ".." in rel:
        return {"ok": False, "error": f"invalid prompt path: {prompt_file!r}"}
    path = ROOT / rel
    if not path.is_file():
        return {"ok": False, "error": f"missing file: {rel}"}
    return {"ok": True, "path": rel, "content": path.read_text(encoding="utf-8")}


def build_heuristic_diff(prompt_file: str, analysis: dict) -> tuple[str, str]:
    """Deterministic diff for tests / dry-run — comment block only."""
    rel = prompt_file
    path = ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    original = path.read_text(encoding="utf-8")
    note_lines = [
        "<!-- prompt-lab-proposal: pending human PR merge -->",
        f"<!-- failures: {len(analysis.get('failure_bucket_ids', []))} -->",
    ]
    for pattern in analysis.get("failure_patterns", [])[:2]:
        for label in pattern.get("labels", [])[:2]:
            if label:
                note_lines.append(f"<!-- {label} -->")
    unified = f"--- a/{rel}\n+++ b/{rel}\n@@ -1,0 +1,{len(note_lines)} @@\n"
    for line in note_lines:
        unified += f"+{line}\n"
    rationale = analysis.get("rationale", "Heuristic prompt-lab proposal")
    return unified, rationale


def draft_unified_diff(
    prompt_file: str,
    analysis_json: str,
    proposed_diff: str = "",
) -> dict:
    """Tool: validate diff text or build heuristic placeholder."""
    try:
        analysis = json.loads(analysis_json)
    except (json.JSONDecodeError, TypeError):
        return {"ok": False, "error": "invalid analysis_json"}

    target = analysis.get("target_prompt_file") or prompt_file
    if proposed_diff.strip():
        if not proposed_diff.lstrip().startswith("---"):
            return {"ok": False, "error": "diff must be unified diff format (--- a/...)"}
        return {
            "ok": True,
            "target_prompt_file": target,
            "unified_diff": proposed_diff,
            "rationale": analysis.get("rationale", ""),
        }

    try:
        unified, rationale = build_heuristic_diff(target, analysis)
    except FileNotFoundError as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "target_prompt_file": target,
        "unified_diff": unified,
        "rationale": rationale,
    }


def run_benchmark_gate(subset: int, check_regression: bool = True) -> dict:
    """Tool: subprocess wrapper — never imports deterministic.py."""
    from scripts.run_benchmark import BASELINE_PATH as bench_baseline
    from scripts.run_benchmark import run_benchmark

    cap = max(1, min(subset, default_max_cases()))
    exit_code = run_benchmark(
        skip_pytest=True,
        skip_adk=False,
        subset=cap,
        check_regression_flag=check_regression,
    )
    summary = read_eval_summary().get("summary", {})
    eval_delta = EvalDelta(
        baseline_path=str(bench_baseline.relative_to(ROOT)),
        subset_cases=cap,
        passed=exit_code == 0,
        rubric_scores={},
        response_match_score=summary.get("response_match_score"),
        notes="subset benchmark gate",
    )
    return {
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "subset": cap,
        "eval_delta": eval_delta.model_dump(),
    }


def create_lab_run(
    failure_bucket_ids: list[str],
    *,
    max_cases: Optional[int] = None,
    db=None,
) -> str:
    cap = max_cases if max_cases is not None else default_max_cases()
    doc = PromptLabRunDoc(
        failure_bucket_ids=failure_bucket_ids,
        max_cases=cap,
        model_version=os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite"),
    )
    coll = _lab_run_collection(db)
    _ref = coll.add(prompt_lab_run_to_firestore(doc))
    return _ref[1].id


def complete_lab_run(
    lab_run_id: str,
    *,
    status: LabRunStatus,
    proposal_ids: Optional[list[str]] = None,
    error: Optional[str] = None,
    db=None,
) -> None:
    coll = _lab_run_collection(db)
    update: dict[str, Any] = {
        "status": status.value,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    if proposal_ids is not None:
        update["proposal_ids"] = proposal_ids
    if error is not None:
        update["error"] = error
    coll.document(lab_run_id).update(update)


def mark_failures_consumed(
    failure_ids: list[str],
    lab_run_id: str,
    *,
    db=None,
) -> dict:
    coll = _failure_collection(db)
    for fid in failure_ids:
        coll.document(fid).update({"consumed_by_lab_run_id": lab_run_id})
    return {"updated": len(failure_ids), "lab_run_id": lab_run_id}


def save_prompt_proposal(
    target_prompt_file: str,
    unified_diff: str,
    rationale: str,
    failure_bucket_ids_json: str,
    eval_delta_json: str = "{}",
    lab_run_id: str = "",
) -> dict:
    """Tool: write prompt_proposals doc — never touches agents/prompts/."""
    try:
        failure_ids = json.loads(failure_bucket_ids_json)
        if not isinstance(failure_ids, list):
            failure_ids = []
    except (json.JSONDecodeError, TypeError):
        failure_ids = []

    eval_delta_data: Optional[dict] = None
    if eval_delta_json.strip():
        try:
            eval_delta_data = json.loads(eval_delta_json)
        except (json.JSONDecodeError, TypeError):
            eval_delta_data = None

    eval_delta = EvalDelta(**eval_delta_data) if eval_delta_data else None
    run_id = lab_run_id or get_active_lab_run_id()

    doc = PromptProposalDoc(
        status=ProposalStatus.pending,
        target_prompt_file=target_prompt_file,
        unified_diff=unified_diff,
        rationale=rationale,
        failure_bucket_ids=failure_ids,
        eval_delta=eval_delta,
        lab_run_id=run_id,
    )
    coll = _proposal_collection()
    ref = coll.add(prompt_proposal_to_firestore(doc))
    return {"ok": True, "proposal_id": ref[1].id, "status": "pending"}


def write_proposal_doc(
    proposal: PromptProposalDoc,
    *,
    db=None,
) -> str:
    """Programmatic proposal write (used by prompt_eval_loop)."""
    coll = _proposal_collection(db)
    ref = coll.add(prompt_proposal_to_firestore(proposal))
    return ref[1].id


def validate_failure_doc(data: dict) -> EvalFailureBucketDoc:
    return EvalFailureBucketDoc(
        resource_code=data["resource_code"],
        agent=data["agent"],
        field=data["field"],
        human_label=data["human_label"],
        prompt_version=data["prompt_version"],
        created_at=data.get("created_at", datetime.now(timezone.utc)),
        origin=data.get("origin", "hitl_flag"),
        pipeline_run_id=data.get("pipeline_run_id"),
        review_queue_id=data.get("review_queue_id"),
        consumed_by_lab_run_id=data.get("consumed_by_lab_run_id"),
    )


def get_firestore_db():
    return get_firestore_client()
