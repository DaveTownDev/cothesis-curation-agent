"""Prompt lab failure analyst — clusters eval_failure_bucket records."""
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.prompt_lab.tools import (
    analyze_failures,
    default_max_cases,
    read_eval_summary,
    read_failure_bucket,
)

MODEL = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")

_PROMPT_PATH = "agents/prompts/prompt_lab_analyst.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Prompt lab analyst — see agents/prompts/prompt_lab_analyst.md"


def load_failures(max_cases: int | None = None) -> dict:
    """Load pending failure bucket records (capped)."""
    cap = max_cases if max_cases is not None else default_max_cases()
    return read_failure_bucket(cap)


prompt_analyst_agent = LlmAgent(
    model=MODEL,
    name="prompt_analyst_agent",
    description=(
        "Clusters HITL eval failures from eval_failure_bucket and eval-summary.json. "
        "Outputs target agent, prompt file, and failure patterns for the editor."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=load_failures),
        FunctionTool(func=read_eval_summary),
        FunctionTool(func=analyze_failures),
    ],
)
