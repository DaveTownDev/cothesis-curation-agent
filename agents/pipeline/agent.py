"""
CoThesis Curation Pipeline — root agent (Day 1 skeleton).

This is the orchestrator for the multi-agent enrichment pipeline:
  Discovery -> Appraisal -> Classification -> Editorial ->
  Reconciliation -> QC Panel -> Arbiter

Day 1: skeleton only. Sub-agents are added per BUILD_PLAN.md Day 2+.
"""

import os
from google.adk.agents import Agent

MODEL = os.environ.get("MODEL_PRO", "gemini-2.5-pro")

root_agent = Agent(
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
        "and an optional resource type, coordinate the enrichment pipeline "
        "to discover and curate high-quality medical research training resources. "
        "Day 1 skeleton — sub-agents not yet wired."
    ),
)
