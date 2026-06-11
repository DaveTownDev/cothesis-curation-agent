"""
Prompt lab root — ADK SequentialAgent for offline prompt improvement.

Run locally: adk web agents/prompt_lab
Job entrypoint: python -m scripts.prompt_eval_loop

Note: ADK 2.x deprecates SequentialAgent in favour of explicit orchestration;
keep SequentialAgent here until Context7 documents a drop-in migration path.
"""
from __future__ import annotations

from google.adk.agents import SequentialAgent

from agents.prompt_lab.analyst import prompt_analyst_agent
from agents.prompt_lab.editor import prompt_editor_agent
from agents.prompt_lab.eval_arbiter import prompt_eval_arbiter_agent

root_agent = SequentialAgent(
    name="prompt_lab",
    description=(
        "Offline prompt improvement loop: analyst clusters eval_failure_bucket "
        "failures → editor drafts unified diff → arbiter runs subset benchmark "
        "and writes prompt_proposals (human PR merge gate)."
    ),
    sub_agents=[
        prompt_analyst_agent,
        prompt_editor_agent,
        prompt_eval_arbiter_agent,
    ],
)
