"""
CoThesis Curation Pipeline — root orchestrator (Day 3).

Pipeline: Discovery → Appraisal → Classification → Editorial → Reconciliation
QC Panel + Arbiter added Day 4.
"""
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

from agents.grounding.agent import grounding_agent
from agents.discovery.agent import discovery_agent
from agents.appraisal.agent import appraisal_agent
from agents.classification.agent import classification_agent
from agents.editorial.agent import editorial_agent
from agents.reconciliation.agent import reconciliation_agent

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
        "and an optional resource type, run the full pipeline:\n"
        "1. discovery_agent: find candidates.\n"
        "2. For each processable candidate (skip_reason is null):\n"
        "   a. appraisal_agent: score quality, write draft AIAssessment.\n"
        "   b. classification_agent: assign type/methodology/stage/access.\n"
        "   c. editorial_agent: write descriptions + propose badges.\n"
        "   d. reconciliation_agent: dedup + assemble final draft record.\n"
        "3. grounding_agent: verify methodology alignment when uncertain.\n"
        "Report: candidates found, drafted, skipped, Firestore doc IDs written."
    ),
    tools=[
        AgentTool(agent=grounding_agent),
        AgentTool(agent=discovery_agent),
        AgentTool(agent=appraisal_agent),
        AgentTool(agent=classification_agent),
        AgentTool(agent=editorial_agent),
        AgentTool(agent=reconciliation_agent),
    ],
)
