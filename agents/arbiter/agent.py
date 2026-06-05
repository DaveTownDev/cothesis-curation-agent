"""
Arbiter agent — composite scoring + routing gate.

Model: Pro (final routing decision; quality matters).
Routes on 0-1 signals (classification_confidence, relevance_score) AND
0-100 signals (quality_score, ai_confidence). Do NOT conflate.
"""
from __future__ import annotations

import json
import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.arbiter.tools import compute_routing_decision, compute_panel_agreement
from agents.shared.hitl import write_review_queue_item, get_review_status

logger = logging.getLogger(__name__)
MODEL = os.environ.get("MODEL_PRO", "gemini-2.5-pro")

_PROMPT_PATH = "agents/prompts/arbiter.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Arbiter agent — see agents/prompts/arbiter.md"


def route(routing_input_json: str) -> dict:
    """
    Compute routing decision from classification + appraisal + panel signals.

    routing_input_json fields:
      relevance_score: float (0-1)
      classification_confidence: float (0-1)
      quality_score: float (0-100)
      ai_confidence: float (0-100)
      panel_scores: list[{dimension, score, pass, reasoning}]
      skip_reason: str | null
    """
    data = json.loads(routing_input_json)
    panel_agreement = compute_panel_agreement(data.get("panel_scores", []))
    return compute_routing_decision(
        relevance_score=float(data.get("relevance_score") or 0),
        classification_confidence=float(data.get("classification_confidence") or 0),
        quality_score=float(data.get("quality_score") or 0),
        ai_confidence=float(data.get("ai_confidence") or 0),
        panel_agreement=panel_agreement,
        skip_reason=data.get("skip_reason"),
    )


def write_review_queue(queue_item_json: str) -> str:
    """
    Write a review_needed item to the Firestore review_queue.
    Returns the Firestore document ID.
    """
    data = json.loads(queue_item_json)
    resource_code = data.get("resource_code", "unknown")
    draft_record = data.get("draft_record") or {}

    # If the orchestrator didn't thread the assembled record through, read it
    # back from Firestore (reconciliation persisted it keyed by resource_code).
    if not draft_record or not draft_record.get("title"):
        try:
            from agents.shared.firestore_utils import get_firestore_collection
            doc = get_firestore_collection("draft_records").document(resource_code).get()
            if doc.exists:
                draft_record = doc.to_dict() or draft_record
                logger.info("Recovered draft_record from Firestore for %s", resource_code)
        except Exception as exc:
            logger.warning("Could not recover draft_record for %s: %s", resource_code, exc)

    return write_review_queue_item(
        resource_code=resource_code,
        routing=data.get("routing", "review_needed"),
        reason=data.get("reason", ""),
        panel_result=data.get("panel_result", {}),
        draft_record=draft_record,
    )


def check_review_status(resource_code: str) -> dict:
    """Check if a resource has been reviewed by a human."""
    status = get_review_status(resource_code)
    return {"resource_code": resource_code, "status": status}


arbiter_agent = LlmAgent(
    model=MODEL,
    name="arbiter_agent",
    description=(
        "Routes a resource to auto_accept, review_needed, or auto_exclude "
        "based on classification signals (0-1), quality signals (0-100), "
        "and QC panel agreement. Writes review_needed items to the review queue."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=route),
        FunctionTool(func=write_review_queue),
        FunctionTool(func=check_review_status),
    ],
)
