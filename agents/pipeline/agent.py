"""
CoThesis Curation Pipeline — root orchestrator (Day 4 — full pipeline).

Pipeline: Discovery → Appraisal → Classification → Editorial →
          Reconciliation → QC Panel → Arbiter

Arbiter routes to: auto_accept (publish checklist) |
                   review_needed (HITL review queue) | auto_exclude.
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
from agents.qc_panel.agent import qc_panel_agent
from agents.arbiter.agent import arbiter_agent

MODEL = os.environ.get("MODEL_PRO", "gemini-3.1-pro-preview")

root_agent = LlmAgent(
    model=MODEL,
    name="cothesis_curation_pipeline",
    description=(
        "Orchestrates the CoThesis research-resource curation pipeline: "
        "discovers, appraises, classifies, edits, QC-evaluates, and routes "
        "medical research training resources for the CoThesis Compendium."
    ),
    instruction=(
        "You are the CoThesis Curation Pipeline orchestrator. You operate in TWO modes.\n\n"
        "MODE A — CURATE A SPECIFIC RESOURCE (when the request gives you a concrete "
        "resource with a title and URL, e.g. 'Curate this article: ...'):\n"
        "  SKIP discovery entirely. The resource is already given. You MUST run EVERY "
        "step below in order, calling each tool exactly once, and you MUST NOT stop "
        "or summarise until arbiter_agent has been called:\n"
        "  1. appraisal_agent: score quality, then call write_assessment to persist the "
        "draft AIAssessment to Firestore. Derive a kebab-case resource_code from the title.\n"
        "  2. classification_agent: assign type/methodology/stage/access. Map free-text "
        "methodology hints to vocabulary leaf methodology codes from its injected "
        "classification guide (e.g. SYN-04, OBS-11); use [] when none genuinely apply.\n"
        "  3. editorial_agent: write short + long + plain descriptions, propose badges.\n"
        "  4. reconciliation_agent: assemble the final draft record (use assemble_record).\n"
        "  5. qc_panel_agent: run deterministic + LLM quality checks on the draft record.\n"
        "  6. arbiter_agent: compute routing. When routing is 'review_needed', the arbiter "
        "ITSELF writes the item to the review queue — so you MUST pass arbiter_agent the "
        "COMPLETE assembled draft_record AND resource_code. Do NOT try to call "
        "write_review_queue yourself; you don't have that tool — only arbiter_agent does.\n"
        "  Use the SAME resource_code across every step.\n\n"
        "MODE B — DISCOVER THEN CURATE (when given only a methodology code + type):\n"
        "  1. discovery_agent: find candidates, then run steps 1-6 of Mode A for each "
        "processable candidate (skip_reason is null).\n\n"
        "CRITICAL: never end your turn after only discovery or only appraisal. The job is "
        "not done until arbiter_agent has routed the resource (and, for review_needed, "
        "written it to the review queue). Report the resource_code, routing decision, "
        "and Firestore doc IDs written."
    ),
    tools=[
        AgentTool(agent=grounding_agent),
        AgentTool(agent=discovery_agent),
        AgentTool(agent=appraisal_agent),
        AgentTool(agent=classification_agent),
        AgentTool(agent=editorial_agent),
        AgentTool(agent=reconciliation_agent),
        AgentTool(agent=qc_panel_agent),
        AgentTool(agent=arbiter_agent),
    ],
)
