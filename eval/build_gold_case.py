"""
Build ADK-shaped gold eval cases — Python mirror of console/lib/eval-export.ts.

Used by tests/test_eval_export.py for schema contract validation and aggregate round-trip.
"""
from __future__ import annotations

from typing import Any

PROMPT_VERSIONS: dict[str, str] = {
    "appraisal": "appraisal@1.0.0",
    "classification": "classification@1.0.0",
    "discovery": "discovery@1.0.0",
    "editorial": "editorial@1.0.0",
    "reconciliation": "reconciliation@1.0.0",
    "qc_panel": "qc_panel@1.0.0",
    "arbiter": "arbiter@1.0.0",
}

STANDARD_RUBRIC_COUNT = 5


def _text_part(text: str) -> dict[str, Any]:
    return {"text": text, "role": None}


def build_gold_eval_case(
    *,
    resource_code: str,
    draft: dict[str, Any],
    origin: str = "hitl",
    failure_mode: str | None = None,
    pipeline_run_id: str | None = None,
    assessment_prompt_version: str | None = None,
) -> dict[str, Any]:
    """Build a gold case dict matching eval/schemas/gold_case.schema.json."""
    title = draft.get("title", resource_code)
    rtype = draft.get("resource_type_code", "article")
    url = draft.get("url", "")
    meth = ", ".join(draft.get("methodology_codes") or []) or "none specified"
    user_text = (
        f'Curate one {rtype} resource titled "{title}". '
        f"URL: {url or 'n/a'}. Focus methodologies: {meth}."
    )
    quality = draft.get("quality_score", 0)
    ai_conf = draft.get("ai_confidence", 0)
    meth_out = ", ".join(draft.get("methodology_codes") or []) or "none"
    stages = ", ".join(draft.get("stage_codes") or []) or "none"
    editorial_status = draft.get("editorial_status", "proposed")
    final_text = (
        f'Processed {rtype} "{title}". Quality score {quality}, AI confidence {ai_conf}. '
        f"Methodology codes: {meth_out}. Thesis stages: {stages}. "
        f"Draft record created with editorial_status={editorial_status}."
    )

    prompt_versions = dict(PROMPT_VERSIONS)
    if assessment_prompt_version:
        prompt_versions["appraisal"] = assessment_prompt_version

    source: dict[str, Any] = {
        "resource_code": resource_code,
        "origin": origin,
        "prompt_versions": prompt_versions,
    }
    if failure_mode:
        source["failure_mode"] = failure_mode

    expected: dict[str, Any] = {
        "resource_type_code": rtype,
        "resource_subtype_code": draft.get("resource_subtype_code"),
        "methodology_codes": list(draft.get("methodology_codes") or []),
        "skill_codes": list(draft.get("skill_codes") or []),
        "stage_codes": list(draft.get("stage_codes") or []),
        "discipline_codes": list(draft.get("discipline_codes") or []),
        "tags": [],
    }
    if draft.get("domain_codes"):
        expected["domain_codes"] = list(draft["domain_codes"])

    return {
        "eval_id": resource_code,
        "source": source,
        "expected_classification": expected,
        "conversation": [
            {
                "user_content": {"parts": [_text_part(user_text)]},
                "final_response": {"parts": [_text_part(final_text)]},
                "rubrics": [{"rubric_id": f"r{i}"} for i in range(STANDARD_RUBRIC_COUNT)],
            }
        ],
        "conversation_scenario": None,
        "session_input": None,
        "creation_timestamp": 0.0,
        "rubrics": None,
        "final_session_state": {
            "resource_code": resource_code,
            "pipeline_run_id": pipeline_run_id,
        },
    }


def validate_gold_case(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not doc.get("eval_id"):
        errors.append("eval_id is required")
    source = doc.get("source") or {}
    if not source.get("resource_code"):
        errors.append("source.resource_code is required")
    if source.get("origin") not in {"seed", "hitl", "synthetic"}:
        errors.append("invalid source.origin")
    if not doc.get("conversation"):
        errors.append("conversation is required")
    exp = doc.get("expected_classification") or {}
    if not exp.get("resource_type_code"):
        errors.append("expected_classification.resource_type_code is required")
    return errors
