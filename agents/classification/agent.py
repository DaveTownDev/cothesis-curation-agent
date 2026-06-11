"""
Classification agent — type / subtype / methodology / stage / difficulty / access.

Model: Flash-Lite (JSON-only; retry once at temp 0, else route review_needed).
"""
from __future__ import annotations

import json
import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.classification.tools import parse_classification_json

logger = logging.getLogger(__name__)
MODEL = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")

_PROMPT_PATH = "agents/prompts/classification.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Classification agent — see agents/prompts/classification.md"

from agents.shared.codes import get_classification_vocabulary_guide

_prompt_text = _prompt_text + "\n\n" + get_classification_vocabulary_guide()


def validate_classification(classification_json: str) -> dict:
    """
    Validate a classification JSON string against the canonical schema.
    Returns {"valid": true, "result": {...}} or {"valid": false, "error": "..."}.
    """
    import json as _json
    try:
        data = _json.loads(classification_json)
        result = parse_classification_json(data)
        if result is None:
            return {"valid": False, "error": "Unparseable JSON — retry"}
        return {"valid": True, "result": result.model_dump()}
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


classification_agent = LlmAgent(
    model=MODEL,
    name="classification_agent",
    description=(
        "Classifies a resource: resource_type_code, resource_subtype_code, "
        "methodology_codes (platform SYN/OBS/EVAL), stage_codes, "
        "relevance_score (0-1), classification_confidence (0-1), access_type, "
        "discipline_codes, difficulty_level. "
        "JSON-only output; retries once on parse failure."
    ),
    instruction=_prompt_text,
    tools=[FunctionTool(func=validate_classification)],
)
