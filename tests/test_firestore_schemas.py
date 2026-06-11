"""Unit tests for prompt-improvement Firestore document models."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agents.shared.firestore_schemas import (
    EvalDelta,
    EvalFailureBucketDoc,
    ProposalStatus,
    PromptLabRunDoc,
    PromptProposalDoc,
    eval_failure_bucket_to_firestore,
    prompt_lab_run_to_firestore,
    prompt_proposal_to_firestore,
)


def test_eval_failure_bucket_required_fields():
    doc = EvalFailureBucketDoc(
        resource_code="RES-001",
        agent="classification",
        field="methodology_codes",
        human_label="Wrong SYN code for software resource",
        prompt_version="classification@1.0.0",
    )
    assert doc.origin == "hitl_flag"
    assert doc.pipeline_run_id is None


def test_eval_failure_bucket_rejects_empty_resource_code():
    with pytest.raises(ValidationError):
        EvalFailureBucketDoc(
            resource_code="",
            agent="classification",
            field="methodology_codes",
            human_label="x",
            prompt_version="classification@1.0.0",
        )


def test_eval_failure_bucket_firestore_round_trip():
    ts = datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
    doc = EvalFailureBucketDoc(
        resource_code="L07zC93w",
        agent="classification",
        field="discipline_codes",
        human_label="Should be PSYCH not slug",
        prompt_version="classification@1.0.0",
        created_at=ts,
        origin="qa_requeue",
        pipeline_run_id="run-abc",
    )
    payload = eval_failure_bucket_to_firestore(doc)
    assert payload["resource_code"] == "L07zC93w"
    assert payload["origin"] == "qa_requeue"
    assert payload["created_at"].startswith("2026-06-11")


def test_prompt_proposal_status_serialization():
    doc = PromptProposalDoc(
        target_prompt_file="agents/prompts/classification.md",
        unified_diff="--- a/agents/prompts/classification.md\n+++ b/...",
        rationale="Failures on software methodology optional rule",
        failure_bucket_ids=["fb1", "fb2"],
        eval_delta=EvalDelta(subset_cases=5, passed=True, rubric_scores={"type_methodology_correct": 0.9}),
    )
    payload = prompt_proposal_to_firestore(doc)
    assert payload["status"] == "pending"
    assert payload["eval_delta"]["passed"] is True


def test_prompt_proposal_merged_status():
    doc = PromptProposalDoc(
        status=ProposalStatus.merged,
        target_prompt_file="agents/prompts/editorial.md",
        unified_diff="diff",
        reviewed_by="curator@example.com",
    )
    assert prompt_proposal_to_firestore(doc)["status"] == "merged"


def test_prompt_lab_run_max_cases_guard():
    with pytest.raises(ValidationError):
        PromptLabRunDoc(max_cases=0)


def test_prompt_lab_run_firestore_round_trip():
    doc = PromptLabRunDoc(
        failure_bucket_ids=["a", "b"],
        max_cases=10,
        proposal_ids=["p1"],
        model_version="gemini-3.1-flash-lite",
    )
    payload = prompt_lab_run_to_firestore(doc)
    assert payload["status"] == "running"
    assert payload["max_cases"] == 10
