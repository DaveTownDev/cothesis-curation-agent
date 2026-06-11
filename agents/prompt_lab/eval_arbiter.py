"""Prompt lab eval arbiter — subset benchmark gate + proposal persistence."""
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.prompt_lab.tools import run_benchmark_gate, save_prompt_proposal

MODEL = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")

_PROMPT_PATH = "agents/prompts/prompt_lab_eval_arbiter.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Prompt lab eval arbiter — see agents/prompts/prompt_lab_eval_arbiter.md"


prompt_eval_arbiter_agent = LlmAgent(
    model=MODEL,
    name="prompt_eval_arbiter_agent",
    description=(
        "Runs scripts.run_benchmark subset gate and saves a prompt_proposals doc. "
        "Never auto-applies diffs to agents/prompts/."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=run_benchmark_gate),
        FunctionTool(func=save_prompt_proposal),
    ],
)
