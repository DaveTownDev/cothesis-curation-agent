"""
Editorial agent — write the four description fields and propose badges.

Model: Pro (quality matters here; this is the public-facing copy).
Style anchor: data/editorial_examples/editorial_examples.md
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.editorial.tools import parse_editorial_json, check_plain_for_jargon

logger = logging.getLogger(__name__)
MODEL = os.environ.get("MODEL_FLASH", "gemini-3.5-flash")

_PROMPT_PATH = "agents/prompts/editorial.md"
_EXAMPLES_PATH = "data/editorial_examples/editorial_examples.md"

try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Editorial agent — see agents/prompts/editorial.md"

try:
    _examples = Path(_EXAMPLES_PATH).read_text()
except FileNotFoundError:
    _examples = ""


def check_jargon(plain_text: str) -> dict:
    """Check editorial_description_plain for banned research terms. Returns violations list."""
    violations = check_plain_for_jargon(plain_text)
    return {"violations": violations, "clean": len(violations) == 0}


def validate_editorial(editorial_json: str) -> dict:
    """
    Validate editorial JSON against the canonical schema.
    Returns {"valid": true, "result": {...}} or {"valid": false, "error": "...", "violations": [...]}.
    """
    try:
        data = json.loads(editorial_json)
        output = parse_editorial_json(data)
        violations = check_plain_for_jargon(output.editorial_description_plain)
        return {
            "valid": True,
            "result": output.model_dump(),
            "jargon_warnings": violations,
        }
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


# Inject style examples into the system instruction
_full_instruction = (
    f"{_prompt_text}\n\n"
    "## Style examples (emulate voice and structure, not these specific resources)\n\n"
    f"{_examples}"
    if _examples else _prompt_text
)

editorial_agent = LlmAgent(
    model=MODEL,
    name="editorial_agent",
    description=(
        "Writes editorial_description (short), summary (long), "
        "editorial_description_plain (jargon-free), and proposes badges. "
        "Never writes editorial_note (human-only field)."
    ),
    instruction=_full_instruction,
    tools=[
        FunctionTool(func=check_jargon),
        FunctionTool(func=validate_editorial),
    ],
)
