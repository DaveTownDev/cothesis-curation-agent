"""
Typed Firestore document shapes for the prompt-improvement loop.

Source of truth: docs/SCHEMA.md (eval_failure_bucket, prompt_proposals, prompt_lab_runs).
Console mirrors these in console/lib/firestore.ts (WS-B).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Collection names (also exported from firestore_utils)
# ---------------------------------------------------------------------------

COLLECTION_EVAL_FAILURE_BUCKET = "eval_failure_bucket"
COLLECTION_PROMPT_PROPOSALS = "prompt_proposals"
COLLECTION_PROMPT_LAB_RUNS = "prompt_lab_runs"


# ---------------------------------------------------------------------------
# eval_failure_bucket — HITL-captured eval / taxonomy failures
# ---------------------------------------------------------------------------

FailureOrigin = Literal["hitl_flag", "qa_requeue", "send_to_lab", "benchmark"]


class EvalFailureBucketDoc(BaseModel):
    """Structured failure for the offline prompt lab analyst.

    Written by the HITL console (flag taxonomy, send to lab, QA requeue).
    Read by prompt_eval_loop.py / prompt_analyst; never auto-merged into prompts.
    """

    resource_code: str = Field(..., min_length=1)
    agent: str = Field(
        ...,
        min_length=1,
        description="Pipeline agent stage, e.g. classification, editorial, appraisal",
    )
    field: str = Field(
        ...,
        min_length=1,
        description="Draft field under dispute, e.g. methodology_codes, discipline_codes",
    )
    human_label: str = Field(
        ...,
        min_length=1,
        description="Reviewer-facing description of the error",
    )
    prompt_version: str = Field(
        ...,
        min_length=1,
        description="Prompt registry version at time of failure (e.g. classification@1.0.0)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    origin: FailureOrigin = "hitl_flag"
    pipeline_run_id: Optional[str] = None
    review_queue_id: Optional[str] = None
    consumed_by_lab_run_id: Optional[str] = Field(
        default=None,
        description="Set when a prompt-lab Job has picked up this failure",
    )


# ---------------------------------------------------------------------------
# prompt_proposals — proposed prompt diffs (human merge gate)
# ---------------------------------------------------------------------------

class ProposalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    merged = "merged"


class EvalDelta(BaseModel):
    """Subset benchmark comparison attached to a proposal."""

    baseline_path: str = "eval/baseline.json"
    subset_cases: int = 0
    passed: bool = False
    rubric_scores: dict[str, float] = Field(default_factory=dict)
    response_match_score: Optional[float] = None
    notes: str = ""


class PromptProposalDoc(BaseModel):
    """Offline prompt lab output — unified diff for one agents/prompts/*.md file.

    Approve/reject in console updates status only; merge to repo is always a human PR.
    """

    status: ProposalStatus = ProposalStatus.pending
    target_prompt_file: str = Field(
        ...,
        min_length=1,
        description="Repo-relative path, e.g. agents/prompts/classification.md",
    )
    unified_diff: str = Field(
        ...,
        min_length=1,
        description="Unified diff text; never auto-applied",
    )
    rationale: str = ""
    failure_bucket_ids: list[str] = Field(default_factory=list)
    eval_delta: Optional[EvalDelta] = None
    lab_run_id: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# prompt_lab_runs — Cloud Run Job execution audit
# ---------------------------------------------------------------------------

class LabRunStatus(str, Enum):
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class PromptLabRunDoc(BaseModel):
    """Audit record for one prompt-lab-run Cloud Run Job execution."""

    status: LabRunStatus = LabRunStatus.running
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    completed_at: Optional[datetime] = None
    failure_bucket_ids: list[str] = Field(default_factory=list)
    max_cases: int = Field(
        default=10,
        ge=1,
        description="Cost cap — mirrors PROMPT_LAB_MAX_CASES env",
    )
    proposal_ids: list[str] = Field(default_factory=list)
    model_version: Optional[str] = None
    error: Optional[str] = None


def eval_failure_bucket_to_firestore(doc: EvalFailureBucketDoc) -> dict:
    """Serialize for Firestore .set() / .add()."""
    return doc.model_dump(mode="json")


def prompt_proposal_to_firestore(doc: PromptProposalDoc) -> dict:
    data = doc.model_dump(mode="json")
    data["status"] = doc.status.value
    return data


def prompt_lab_run_to_firestore(doc: PromptLabRunDoc) -> dict:
    data = doc.model_dump(mode="json")
    data["status"] = doc.status.value
    return data
