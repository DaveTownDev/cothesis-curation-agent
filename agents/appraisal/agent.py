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

def _fetch_openalex(doi: str = "", title: str = "") -> dict:
    """Fetch structured metadata from OpenAlex by DOI or title."""
    return fetch_openalex_metadata(doi=doi or None, title=title or None)


def _fetch_pubmed(pmid: str = "") -> dict:
    """Fetch PubMed summary for a PMID."""
    return fetch_pubmed_metadata(pmid=pmid or None)


def _write_assessment(assessment_json: str, resource_code: str) -> str:
    """
    Parse the LLM's appraisal JSON and write a draft AIAssessment to Firestore.
    Returns the Firestore document ID.
    assessment_json: the full appraisal JSON string from the LLM output.
    resource_code: the resource's stable code (kebab-case).
    """
    data = json.loads(assessment_json)
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
        FunctionTool(func=_fetch_openalex),
        FunctionTool(func=_fetch_pubmed),
        FunctionTool(func=_write_assessment),
    ],
)
