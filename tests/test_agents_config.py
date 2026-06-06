"""
Agent configuration tests — verify every agent has the right structure.
Fast, no LLM, no network.
"""
import os
import pytest


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "global")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
    monkeypatch.setenv("MODEL_PRO", "gemini-3.1-pro-preview")
    monkeypatch.setenv("MODEL_FLASH", "gemini-3.5-flash")
    monkeypatch.setenv("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")
    monkeypatch.setenv(
        "VERTEX_DATASTORE_ID",
        "projects/test-project/locations/global/collections/default_collection"
        "/dataStores/test-datastore",
    )
    monkeypatch.setenv("MCP_SERVER_URL", "")  # no MCP in tests


import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "agents"))


class TestGroundingAgent:
    def test_has_exactly_one_tool(self):
        from grounding.agent import grounding_agent
        assert len(grounding_agent.tools) == 1

    def test_tool_is_vertex_ai_search(self):
        from grounding.agent import grounding_agent
        from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool
        assert isinstance(grounding_agent.tools[0], VertexAiSearchTool)

    def test_name(self):
        from grounding.agent import grounding_agent
        assert grounding_agent.name == "grounding_agent"


class TestDiscoveryAgent:
    def test_has_function_tools(self):
        from discovery.agent import discovery_agent
        from google.adk.tools import FunctionTool
        for tool in discovery_agent.tools:
            assert isinstance(tool, FunctionTool)

    def test_uses_flash_lite_model(self):
        from discovery.agent import discovery_agent, MODEL
        assert MODEL == "gemini-3.1-flash-lite"

    def test_name(self):
        from discovery.agent import discovery_agent
        assert discovery_agent.name == "discovery_agent"

    def test_no_vertex_search_tool(self):
        """Discovery must NOT have VertexAiSearchTool — grounding is isolated."""
        from discovery.agent import discovery_agent
        from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool
        for tool in discovery_agent.tools:
            assert not isinstance(tool, VertexAiSearchTool)


class TestAppraisalAgent:
    def test_has_three_tools(self):
        from appraisal.agent import appraisal_agent
        assert len(appraisal_agent.tools) == 3

    def test_uses_flash_model(self):
        from appraisal.agent import MODEL
        assert MODEL == "gemini-3.5-flash"

    def test_name(self):
        from appraisal.agent import appraisal_agent
        assert appraisal_agent.name == "appraisal_agent"

    def test_no_vertex_search_tool(self):
        from appraisal.agent import appraisal_agent
        from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool
        for tool in appraisal_agent.tools:
            assert not isinstance(tool, VertexAiSearchTool)


class TestClassificationAgent:
    def test_uses_flash_lite_model(self):
        from classification.agent import MODEL
        assert MODEL == "gemini-3.1-flash-lite"

    def test_name(self):
        from classification.agent import classification_agent
        assert classification_agent.name == "classification_agent"


class TestEditorialAgent:
    def test_uses_flash_model(self):
        # Tiering (Gemini 3.x upgrade): editorial runs on Flash, not Pro
        from editorial.agent import MODEL
        assert MODEL == "gemini-3.5-flash"

    def test_has_two_tools(self):
        from editorial.agent import editorial_agent
        assert len(editorial_agent.tools) == 2

    def test_name(self):
        from editorial.agent import editorial_agent
        assert editorial_agent.name == "editorial_agent"


class TestReconciliationAgent:
    def test_has_two_tools(self):
        from reconciliation.agent import reconciliation_agent
        assert len(reconciliation_agent.tools) == 2

    def test_name(self):
        from reconciliation.agent import reconciliation_agent
        assert reconciliation_agent.name == "reconciliation_agent"


class TestPipelineAgent:
    def test_has_eight_agent_tools(self):
        from pipeline.agent import root_agent
        from google.adk.tools import AgentTool
        assert len(root_agent.tools) == 8
        for tool in root_agent.tools:
            assert isinstance(tool, AgentTool)

    def test_uses_pro_model(self):
        from pipeline.agent import MODEL
        assert MODEL == "gemini-3.1-pro-preview"

    def test_name(self):
        from pipeline.agent import root_agent
        assert root_agent.name == "cothesis_curation_pipeline"

    def test_wires_grounding_first(self):
        """Grounding agent must be accessible (isolation check)."""
        from pipeline.agent import root_agent
        from google.adk.tools import AgentTool
        agent_names = [t.agent.name for t in root_agent.tools if isinstance(t, AgentTool)]
        assert "grounding_agent" in agent_names

    def test_all_eight_sub_agents_wired(self):
        from pipeline.agent import root_agent
        from google.adk.tools import AgentTool
        expected = {
            "grounding_agent", "discovery_agent", "appraisal_agent",
            "classification_agent", "editorial_agent", "reconciliation_agent",
            "qc_panel_agent", "arbiter_agent",
        }
        wired = {t.agent.name for t in root_agent.tools if isinstance(t, AgentTool)}
        assert wired == expected
