"""Unit tests for prompt lab agents and tools."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestPromptLabAgents:
    def test_sequential_agent_structure(self):
        from agents.prompt_lab.agent import root_agent

        assert root_agent.name == "prompt_lab"
        assert len(root_agent.sub_agents) == 3
        names = {a.name for a in root_agent.sub_agents}
        assert names == {
            "prompt_analyst_agent",
            "prompt_editor_agent",
            "prompt_eval_arbiter_agent",
        }

    def test_analyst_tools_registered(self):
        from agents.prompt_lab.analyst import prompt_analyst_agent

        tool_names = {t.name for t in prompt_analyst_agent.tools}
        assert "load_failures" in tool_names
        assert "read_eval_summary" in tool_names
        assert "analyze_failures" in tool_names


class TestPromptLabTools:
    def test_resolve_target_prompt(self):
        from agents.prompt_lab.tools import resolve_target_prompt

        assert resolve_target_prompt("classification") == "agents/prompts/classification.md"

    def test_resolve_unknown_agent_raises(self):
        from agents.prompt_lab.tools import resolve_target_prompt

        with pytest.raises(KeyError):
            resolve_target_prompt("unknown_stage")

    def test_analyze_failures_clusters_by_agent(self):
        from agents.prompt_lab.tools import analyze_failures

        failures = [
            {
                "id": "fb1",
                "agent": "classification",
                "field": "methodology_codes",
                "human_label": "Wrong SYN on software",
            },
            {
                "id": "fb2",
                "agent": "classification",
                "field": "discipline_codes",
                "human_label": "Use PSYCH code",
            },
        ]
        result = analyze_failures(json.dumps({"failures": failures}), "{}")
        assert result["ok"] is True
        assert result["target_agent"] == "classification"
        assert result["target_prompt_file"] == "agents/prompts/classification.md"
        assert set(result["failure_bucket_ids"]) == {"fb1", "fb2"}

    def test_read_current_prompt_rejects_path_traversal(self):
        from agents.prompt_lab.tools import read_current_prompt

        result = read_current_prompt("../../etc/passwd")
        assert result["ok"] is False

    def test_read_current_prompt_loads_classification(self):
        from agents.prompt_lab.tools import read_current_prompt

        result = read_current_prompt("agents/prompts/classification.md")
        assert result["ok"] is True
        assert "resource_type_code" in result["content"] or len(result["content"]) > 0

    def test_draft_unified_diff_heuristic(self):
        from agents.prompt_lab.tools import analyze_failures, draft_unified_diff

        failures = [
            {
                "id": "fb1",
                "agent": "classification",
                "field": "methodology_codes",
                "human_label": "Optional methodology for software",
                "prompt_version": "classification@1.0.0",
            },
        ]
        analysis = analyze_failures(json.dumps({"failures": failures}), "{}")
        diff = draft_unified_diff(
            analysis["target_prompt_file"],
            json.dumps(analysis),
        )
        assert diff["ok"] is True
        assert diff["unified_diff"].startswith("--- a/agents/prompts/")
        assert "prompt-lab-proposal" in diff["unified_diff"]

    def test_save_prompt_proposal_never_writes_prompt_files(self, tmp_path, monkeypatch):
        from agents.prompt_lab import tools as pl_tools
        from agents.prompt_lab.tools import save_prompt_proposal

        class _FakeColl:
            def add(self, data):
                return (None, type("Ref", (), {"id": "prop-1"})())

        monkeypatch.setattr(pl_tools, "_proposal_collection", lambda db=None: _FakeColl())

        target = ROOT / "agents/prompts/classification.md"
        before_mtime = target.stat().st_mtime
        before_text = target.read_text(encoding="utf-8")

        result = save_prompt_proposal(
            "agents/prompts/classification.md",
            "--- a/agents/prompts/classification.md\n+++ b/...\n",
            "test rationale",
            json.dumps(["fb1"]),
            "{}",
            "run-1",
        )

        assert result["ok"] is True
        assert result["proposal_id"] == "prop-1"
        assert target.read_text(encoding="utf-8") == before_text
        assert target.stat().st_mtime == before_mtime

    def test_default_max_cases_env(self, monkeypatch):
        from agents.prompt_lab.tools import default_max_cases

        monkeypatch.setenv("PROMPT_LAB_MAX_CASES", "7")
        assert default_max_cases() == 7

    @pytest.mark.parametrize("raw,expected", [("0", 1), ("bad", 10), ("-3", 1)])
    def test_default_max_cases_invalid_env(self, monkeypatch, raw, expected):
        from agents.prompt_lab.tools import default_max_cases

        monkeypatch.setenv("PROMPT_LAB_MAX_CASES", raw)
        assert default_max_cases() == expected
