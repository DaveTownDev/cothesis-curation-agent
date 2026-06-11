"""Prompt version registry — semver strings aligned with agents/prompts/*.md."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "agents" / "prompts"
_VERSION_COMMENT = re.compile(r"<!--\s*prompt-version:\s*(\S+)\s*-->")


class TestPromptVersions:
    def test_get_prompt_version_returns_semver(self):
        from agents.shared.prompt_versions import get_prompt_version

        v = get_prompt_version("classification")
        assert v == "classification@1.0.0"
        assert "@" in v

    def test_get_prompt_version_normalises_agent_suffix(self):
        from agents.shared.prompt_versions import get_prompt_version

        assert get_prompt_version("appraisal_agent") == get_prompt_version("appraisal")

    def test_unknown_agent_raises(self):
        from agents.shared.prompt_versions import get_prompt_version

        with pytest.raises(KeyError, match="Unknown prompt agent"):
            get_prompt_version("nonexistent")

    def test_registry_matches_prompt_file_comments(self):
        from agents.shared.prompt_versions import PROMPT_VERSIONS

        for agent, expected in PROMPT_VERSIONS.items():
            path = PROMPTS_DIR / f"{agent}.md"
            assert path.is_file(), f"missing prompt file for {agent}"
            text = path.read_text(encoding="utf-8")
            match = _VERSION_COMMENT.search(text)
            assert match, f"{path.name} missing <!-- prompt-version: … --> comment"
            assert match.group(1) == expected
