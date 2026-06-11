"""
Prompt version registry — semver strings for prompt-improvement loop audit trail.

Bump the version in this dict and the matching `<!-- prompt-version: … -->` comment
in agents/prompts/{agent}.md when merging prompt changes (see docs/PROMPT_IMPROVEMENT_LOOP.md).
"""
from __future__ import annotations

PROMPT_VERSIONS: dict[str, str] = {
    "appraisal": "appraisal@1.0.0",
    "classification": "classification@1.0.0",
    "discovery": "discovery@1.0.0",
    "editorial": "editorial@1.0.0",
    "reconciliation": "reconciliation@1.0.0",
    "qc_panel": "qc_panel@1.0.0",
    "arbiter": "arbiter@1.0.0",
}


def get_prompt_version(agent: str) -> str:
    """Return the semver string for an agent prompt, e.g. appraisal@1.0.0."""
    key = agent.strip().lower().removesuffix("_agent")
    try:
        return PROMPT_VERSIONS[key]
    except KeyError as exc:
        known = ", ".join(sorted(PROMPT_VERSIONS))
        raise KeyError(f"Unknown prompt agent {agent!r}; known: {known}") from exc
