"""
QC evaluator panel agent.

Runs 6 dimension evaluators + 4 specialty reviewers:
  - relevance, accuracy, authority, currency, accessibility, practical_utility
  - ai_pattern_scanner, voice_reviewer, plain_jargon_check, badge_check

Implemented with ADK eval primitives (rubric_based_final_response_quality_v1,
tool_trajectory_avg_score) — see eval/ directory.

For within-pipeline calls the panel is a single LlmAgent that runs all
evaluators as FunctionTools and aggregates the result.
"""
from __future__ import annotations

import json
import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.qc_panel.tools import (
    run_ai_pattern_scan,
    run_voice_review,
    run_plain_jargon_check,
    run_badge_check,
    run_taxonomy_qc_check,
    aggregate_panel_results,
)

logger = logging.getLogger(__name__)
MODEL = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")

_PROMPT_PATH = "agents/prompts/qc_panel.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "QC evaluator panel — see agents/prompts/qc_panel.md"


def run_deterministic_checks(draft_record_json: str) -> dict:
    """
    Run the deterministic QC checks on a draft record.
    draft_record_json: the assembled draft record dict as a JSON string.
    Returns aggregated panel result.
    """
    try:
        record = json.loads(draft_record_json)
    except (json.JSONDecodeError, TypeError):
        logger.warning("run_deterministic_checks: invalid JSON input, using empty record")
        record = {}

    results = []

    # Deterministic checks (no LLM)
    editorial = record.get("editorial_description", "")
    summary = record.get("summary", "")
    plain = record.get("editorial_description_plain", "")
    badges = record.get("proposed_badges", [])

    all_text = f"{editorial}\n{summary}\n{plain}"

    results.append(run_ai_pattern_scan(all_text))
    results.append(run_voice_review(editorial, summary, plain))
    results.append(run_plain_jargon_check(plain))
    results.append(run_badge_check(badges))
    results.append(run_taxonomy_qc_check(record))

    return aggregate_panel_results(results)


def score_dimension(dimension: str, score: float, reasoning: str) -> dict:
    """Score a single quality dimension (called by LLM for each of the 6 dimensions)."""
    from agents.qc_panel.tools import evaluate_dimension
    return evaluate_dimension(dimension, score, reasoning)


def aggregate(panel_scores_json: str) -> dict:
    """Aggregate a list of panel evaluator results."""
    try:
        scores = json.loads(panel_scores_json)
    except (json.JSONDecodeError, TypeError):
        logger.warning("aggregate: invalid JSON input, returning empty panel result")
        scores = []
    if not isinstance(scores, list):
        scores = [scores] if isinstance(scores, dict) else []
    return aggregate_panel_results(scores)


qc_panel_agent = LlmAgent(
    model=MODEL,
    name="qc_panel_agent",
    description=(
        "Runs the QC evaluator panel on a draft record. "
        "Deterministic checks: AI tell scan, brand voice, plain-field jargon, badge validation. "
        "LLM-based: scores all 6 quality dimensions with reasoning. "
        "Returns panel_scores, panel_agreement, and overall_pass."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=run_deterministic_checks),
        FunctionTool(func=score_dimension),
        FunctionTool(func=aggregate),
    ],
)
