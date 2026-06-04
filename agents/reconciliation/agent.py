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


def check_duplicate(candidate_title: str) -> dict:
    """
    Check if a resource title already exists in the Compendium.
    Returns {"is_duplicate": bool, "duplicate_of": str | null}.
    """
    existing = fetch_existing_titles()
    match = is_duplicate(candidate_title, existing)
    if match:
        return {"is_duplicate": True, "duplicate_of": match["resource_code"]}
    return {"is_duplicate": False, "duplicate_of": None}


def assemble_record(assembly_json: str) -> dict:
    """
    Assemble the final draft record from Classification + Editorial + Appraisal JSON.
    assembly_json: {"resource_code", "title", "url", "classification", "editorial", "appraisal"}
    Returns the assembled draft record dict.
    """
    from agents.shared.schema import (
        AIAssessmentDraft, ClassificationResult, EditorialOutput, QualityDimensions
    )
    data = json.loads(assembly_json)
    logger.info("assemble_record top-level keys: %s", list(data.keys()))

    def _unwrap(d: dict, *alias_keys: str) -> dict:
        """Unwrap a dict the LLM may have nested under an alias key."""
        for alias in alias_keys:
            if alias in d and isinstance(d[alias], dict):
                return d[alias]
        return d

    _CONFIDENCE_MAP = {"low": 0.3, "medium": 0.5, "moderate": 0.5,
                       "high": 0.8, "very high": 0.95, "certain": 1.0}

    def _fill_classification(raw: dict) -> dict:
        """Fill required ClassificationResult fields; coerce string scores to floats."""
        raw = raw.copy()
        raw.setdefault("resource_type_code", "article")
        raw.setdefault("access_type", "free")
        # Coerce string scores to floats (LLM sometimes says "high" not 0.8)
        for score_field in ("relevance_score", "classification_confidence"):
            val = raw.get(score_field)
            if isinstance(val, str):
                raw[score_field] = _CONFIDENCE_MAP.get(val.lower().strip(), 0.5)
            raw.setdefault(score_field, 0.5)
        # Scrub legacy methodology codes
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        codes = raw.get("methodology_codes", [])
        raw["methodology_codes"] = [
            c for c in codes
            if not any(c.startswith(p) for p in LEGACY_METHODOLOGY_PREFIXES)
        ]
        return raw

    from agents.shared.codes import normalize_badge

    # LLM sometimes wraps under alias keys or sends a flat dict directly
    raw_classification = _fill_classification(_unwrap(
        data.get("classification", data),
        "ai_classification", "classification_result", "classification",
    ))
    try:
        classification = ClassificationResult(**raw_classification)
    except Exception as exc:
        logger.warning("ClassificationResult validation failed (%s); using defaults", exc)
        classification = ClassificationResult(
            resource_type_code="article",
            relevance_score=0.5,
            classification_confidence=0.5,
            access_type="free",
        )

    # Normalize badge names — LLM may emit friendly strings like "Essential Reference"
    raw_editorial = _unwrap(
        data.get("editorial", data),
        "editorial_output", "editorial_result", "editorial",
    ).copy()
    if "proposed_badges" in raw_editorial:
        normalized = []
        for b in raw_editorial["proposed_badges"]:
            canon = normalize_badge(b)
            if canon:
                normalized.append(canon)
            else:
                logger.warning("Unrecognised badge %r — dropping", b)
        raw_editorial["proposed_badges"] = normalized[:3]

    try:
        editorial = EditorialOutput(**raw_editorial)
    except Exception as exc:
        logger.warning("EditorialOutput validation failed (%s); using stubs", exc)
        editorial = EditorialOutput(
            editorial_description=raw_editorial.get("editorial_description", ""),
            summary=raw_editorial.get("summary", raw_editorial.get("editorial_description_long", "")),
            editorial_description_plain=raw_editorial.get("editorial_description_plain", ""),
        )

    ap = _unwrap(
        data.get("appraisal", data),
        "appraisal_result", "quality_assessment", "appraisal",
    ).copy()

    # Fill required fields; coerce {} to [] for list fields
    ap.setdefault("resource_code", data.get("resource_code", ""))
    ap.setdefault("model_version", "gemini-2.5-flash")
    ap.setdefault("pipeline_run_id", "")
    ap.setdefault("quality_score", 70.0)
    ap.setdefault("ai_confidence", 60.0)
    for list_field in ("relevance_to_discipline_codes", "thesis_stage_signals",
                       "relevance_to_methodology_codes", "proposed_badges",
                       "strengths", "limitations"):
        val = ap.get(list_field)
        if not isinstance(val, list):
            ap[list_field] = []

    raw_dims = ap.pop("quality_dimensions", {})
    if not isinstance(raw_dims, dict):
        raw_dims = {}
    dims_kwargs = {}
    for dim in ("relevance", "accuracy", "authority", "currency",
                "accessibility", "practical_utility"):
        if dim in raw_dims:
            dims_kwargs[dim] = raw_dims[dim]
    if "ebm_level" in raw_dims:
        dims_kwargs["ebm_level"] = raw_dims["ebm_level"]
    quality_dimensions = QualityDimensions(**dims_kwargs) if dims_kwargs else QualityDimensions.make_stub()

    try:
        appraisal = AIAssessmentDraft(quality_dimensions=quality_dimensions, **ap)
    except Exception as exc:
        logger.warning("AIAssessmentDraft validation failed (%s); using stub", exc)
        appraisal = AIAssessmentDraft(
            resource_code=data.get("resource_code", ""),
            model_version="gemini-2.5-flash",
            pipeline_run_id="",
            quality_score=70.0,
            ai_confidence=60.0,
            quality_dimensions=quality_dimensions,
        )

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
        FunctionTool(func=check_duplicate),
        FunctionTool(func=assemble_record),
    ],
)
