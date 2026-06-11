"""Prompt lab editor — drafts unified diffs for human PR merge."""
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.prompt_lab.tools import draft_unified_diff, read_current_prompt

MODEL = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")

_PROMPT_PATH = "agents/prompts/prompt_lab_editor.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Prompt lab editor — see agents/prompts/prompt_lab_editor.md"


prompt_editor_agent = LlmAgent(
    model=MODEL,
    name="prompt_editor_agent",
    description=(
        "Drafts a minimal unified diff for one agents/prompts/*.md file. "
        "Never writes to disk — output is a Firestore proposal only."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=read_current_prompt),
        FunctionTool(func=draft_unified_diff),
    ],
)
