"""
Reconciliation agent — dedup + draft record assembly.

Model: Flash (dedup is deterministic; Flash for assembly reasoning).
For MVP: on probable duplicate → STOP (no merge). Flag it.
"""
from __future__ import annotations

import json
import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.reconciliation.tools import (
    assemble_draft_record,
    fetch_existing_titles,
    is_duplicate,
    title_similarity,
)

logger = logging.getLogger(__name__)
MODEL = os.environ.get("MODEL_FLASH", "gemini-flash-latest")

_PROMPT_PATH = "agents/prompts/reconciliation.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Reconciliation agent — see agents/prompts/reconciliation.md"


def _check_duplicate(candidate_title: str) -> dict:
    """
    Check if a resource title already exists in the Compendium.
    Returns {"is_duplicate": bool, "duplicate_of": str | null}.
    """
    existing = fetch_existing_titles()
    match = is_duplicate(candidate_title, existing)
    if match:
        return {"is_duplicate": True, "duplicate_of": match["resource_code"]}
    return {"is_duplicate": False, "duplicate_of": None}


def _assemble_record(assembly_json: str) -> dict:
    """
    Assemble the final draft record from Classification + Editorial + Appraisal JSON.
    assembly_json: {"resource_code", "title", "url", "classification", "editorial", "appraisal"}
    Returns the assembled draft record dict.
    """
    from agents.shared.schema import (
        AIAssessmentDraft, ClassificationResult, EditorialOutput, QualityDimensions
    )
    data = json.loads(assembly_json)

    classification = ClassificationResult(**data["classification"])
    editorial = EditorialOutput(**data["editorial"])

    ap = data["appraisal"]
    raw_dims = ap.pop("quality_dimensions", {})
    dims_kwargs = {}
    for dim in ("relevance", "accuracy", "authority", "currency",
                "accessibility", "practical_utility"):
        if dim in raw_dims:
            dims_kwargs[dim] = raw_dims[dim]
    if "ebm_level" in raw_dims:
        dims_kwargs["ebm_level"] = raw_dims["ebm_level"]
    quality_dimensions = QualityDimensions(**dims_kwargs) if dims_kwargs else QualityDimensions.make_stub()
    appraisal = AIAssessmentDraft(quality_dimensions=quality_dimensions, **ap)

    return assemble_draft_record(
        resource_code=data["resource_code"],
        title=data["title"],
        url=data["url"],
        classification=classification,
        editorial=editorial,
        appraisal=appraisal,
    )


reconciliation_agent = LlmAgent(
    model=MODEL,
    name="reconciliation_agent",
    description=(
        "Deduplicates a candidate against existing Compendium resources "
        "(title similarity >= 0.9 = duplicate; stop and flag). "
        "On no duplicate: assembles the final draft Resource record "
        "from Classification + Editorial + Appraisal outputs."
    ),
    instruction=_prompt_text,
    tools=[
        FunctionTool(func=_check_duplicate),
        FunctionTool(func=_assemble_record),
    ],
)
