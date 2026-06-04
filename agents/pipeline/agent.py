"""
CoThesis Curation Pipeline — root orchestrator.

Wires the sub-agents (Day 2+): Discovery → Appraisal.
Classification, Editorial, Reconciliation, QC Panel, Arbiter added Day 3-4.

Sub-agents are accessed via AgentTool to preserve tool isolation
(VertexAiSearchTool isolation rule: grounding_agent has only that tool).
"""
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

from agents.grounding.agent import grounding_agent
from agents.discovery.agent import discovery_agent
from agents.appraisal.agent import appraisal_agent

MODEL = os.environ.get("MODEL_PRO", "gemini-2.5-pro")

root_agent = LlmAgent(
    model=MODEL,
    name="cothesis_curation_pipeline",
    description=(
        "Orchestrates the CoThesis research-resource curation pipeline: "
        "discovers, appraises, classifies, and edits medical research "
        "training resources for the CoThesis Compendium."
    ),
    instruction=(
        "You are the CoThesis Curation Pipeline orchestrator. "
        "Given a methodology code (SYN-01, SYN-02, OBS-01, or EVAL-01) "
        "and an optional resource type, run the enrichment pipeline:\n"
        "1. Use discovery_agent to find candidates for the methodology + type.\n"
        "2. For each processable candidate (skip_reason is null), "
        "   use appraisal_agent to score it and write a draft AIAssessment.\n"
        "3. Use grounding_agent to verify methodology alignment when uncertain.\n"
        "Report a summary: how many candidates found, how many drafted, "
        "how many skipped, and the document IDs written."
    ),
    tools=[
        AgentTool(agent=grounding_agent),
        AgentTool(agent=discovery_agent),
        AgentTool(agent=appraisal_agent),
    ],
)
