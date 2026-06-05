"""
Appraisal agent — quality assessment + dimension scoring + Firestore write.

Pattern: deterministic API calls first (OpenAlex/PubMed), then Flash for
LLM scoring of what the APIs can't resolve.

IMPORTANT: VertexAiSearchTool is NOT on this agent. Grounding is isolated
to agents/grounding/agent.py and accessed via AgentTool.
"""
from __future__ import annotations

import json
import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.appraisal.tools import (
    fetch_openalex_metadata,
    fetch_pubmed_metadata,
    parse_appraisal_json,
    write_draft_assessment,
)
from agents.shared.schema import AIAssessmentDraft, QualityDimensions

logger = logging.getLogger(__name__)

MODEL = os.environ.get("MODEL_FLASH", "gemini-flash-latest")

# ---------------------------------------------------------------------------
# FunctionTool wrappers — deterministic API lookups
# ---------------------------------------------------------------------------

def fetch_openalex(doi: str = "", title: str = "") -> dict:
    """Fetch structured metadata from OpenAlex by DOI or title."""
    return fetch_openalex_metadata(doi=doi or None, title=title or None)


def fetch_pubmed(pmid: str = "") -> dict:
    """Fetch PubMed summary for a PMID."""
    return fetch_pubmed_metadata(pmid=pmid or None)


_REQUIRED_DIMS = (
    "relevance", "accuracy", "authority",
    "currency", "accessibility", "practical_utility",
)


def _ensure_dimensions(data: dict) -> dict:
    """
    Resilience at the agent boundary: if the LLM omitted quality_dimensions
    (returns [] or {} or partial), synthesise the 6 required dimensions from
    the overall quality_score so the pipeline degrades instead of crashing.
    The strict parser (parse_appraisal_json) still validates the final shape.
    """
    # Ensure the top-level numeric fields the strict parser indexes directly.
    base_score = float(data.get("quality_score", 70) or 70)
    data["quality_score"] = base_score
    data["ai_confidence"] = float(data.get("ai_confidence", 50) or 50)

    raw = data.get("quality_dimensions")
    if not isinstance(raw, dict):
        raw = {}
    for dim in _REQUIRED_DIMS:
        if dim not in raw or not isinstance(raw.get(dim), (dict, int, float)):
            raw[dim] = {
                "score": base_score,
                "weight": 0.1,
                "reasoning": "Synthesised from overall quality_score (LLM omitted this dimension).",
            }
    data["quality_dimensions"] = raw
    return data


def write_assessment(assessment_json: str, resource_code: str) -> str:
    """
    Parse the LLM's appraisal JSON and write a draft AIAssessment to Firestore.
    Returns the Firestore document ID.
    assessment_json: the full appraisal JSON string from the LLM output.
    resource_code: the resource's stable code (kebab-case).
    """
    data = json.loads(assessment_json)
    data = _ensure_dimensions(data)
    draft = parse_appraisal_json(
        data,
        resource_code=resource_code,
        model_version=MODEL,
    )
    return write_draft_assessment(draft)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

_PROMPT_PATH = "agents/prompts/appraisal.md"

try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Appraisal agent — see agents/prompts/appraisal.md"


appraisal_agent = LlmAgent(
    model=MODEL,
    name="appraisal_agent",
    description=(
        "Quality-assesses a candidate resource. "
        "Fetches structured metadata (OpenAlex, PubMed) first, then scores "
        "all 6 quality dimensions. Writes a draft AIAssessment to Firestore."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=fetch_openalex),
        FunctionTool(func=fetch_pubmed),
        FunctionTool(func=write_assessment),
    ],
)
