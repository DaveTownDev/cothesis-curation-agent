"""
Grounding agent — VertexAiSearchTool ONLY.

HARD RULE (CLAUDE.md): VertexAiSearchTool cannot share an agent with other
tools. This agent is isolated and accessed via AgentTool from other agents.
"""
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool

MODEL = os.environ.get("MODEL_FLASH", "gemini-3.5-flash")
DATASTORE_ID = os.environ.get(
    "VERTEX_DATASTORE_ID",
    "projects/cothesis-curation-agent/locations/global"
    "/collections/default_collection/dataStores/cothesis-methodology-grounding",
)

grounding_agent = LlmAgent(
    model=MODEL,
    name="grounding_agent",
    description=(
        "Retrieves grounded methodology definitions and research context "
        "from the CoThesis Vertex AI Search datastore. "
        "Use for: confirming a resource's methodology alignment, "
        "checking quality standards, or retrieving reporting guidelines."
    ),
    instruction=(
        "You are a grounded research assistant. "
        "Use the search tool to retrieve relevant methodology definitions, "
        "reporting standards, and quality indicators from the CoThesis knowledge base. "
        "Always cite the source document in your response."
    ),
    tools=[
        VertexAiSearchTool(data_store_id=DATASTORE_ID),
    ],
)
