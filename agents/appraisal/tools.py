"""
Appraisal agent tools.

Deterministic-and-API-first pattern:
  1. Fetch structured metadata (OpenAlex, PubMed, Semantic Scholar)
  2. LLM scores using those signals
  3. write_draft_assessment() → Firestore drafts collection

parse_appraisal_json() is the contract between the LLM output and the schema.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from agents.shared.schema import (
    AIAssessmentDraft,
    CandidateResource,
    QualityDimension,
    QualityDimensions,
)
from agents.shared.firestore_utils import get_firestore_collection, COLLECTION_DRAFTS

logger = logging.getLogger(__name__)

_REQUIRED_DIMS = (
    "relevance", "accuracy", "authority",
    "currency", "accessibility", "practical_utility",
)

# ---------------------------------------------------------------------------
# Deterministic metadata fetchers
# ---------------------------------------------------------------------------

def fetch_openalex_metadata(doi: str | None = None, title: str | None = None) -> dict:
    """Fetch structured metadata from OpenAlex. Returns {} on failure."""
    params: dict[str, str | int] | None = None
    if doi:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    elif title:
        url = "https://api.openalex.org/works"
        params = {"search": title, "per_page": 1}
    else:
        return {}
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                url,
                params=params if title else None,
                headers={"User-Agent": "CoThesis-curation/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            if "results" in data:
                return data["results"][0] if data["results"] else {}
            return data
    except Exception as exc:
        logger.warning("OpenAlex fetch failed: %s", exc)
        return {}


def fetch_pubmed_metadata(pmid: str | None = None) -> dict:
    """Fetch PubMed summary for a given PMID. Returns {} on failure."""
    if not pmid:
        return {}
    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        f"?db=pubmed&id={pmid}&retmode=json"
    )
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {}).get(pmid, {})
    except Exception as exc:
        logger.warning("PubMed fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# LLM output → schema
# ---------------------------------------------------------------------------

def parse_appraisal_json(
    llm_output: dict[str, Any],
    resource_code: str,
    model_version: str,
) -> AIAssessmentDraft:
    """
    Validate and convert raw LLM appraisal JSON into an AIAssessmentDraft.
    Raises ValueError if required quality dimensions are missing.
    """
    raw_dims = llm_output.get("quality_dimensions", {})
    for dim in _REQUIRED_DIMS:
        if dim not in raw_dims:
            raise ValueError(
                f"LLM appraisal missing required quality dimension: {dim!r}. "
                f"Got: {list(raw_dims)}"
            )

    def _coerce_dim(v: object) -> dict:
        # LLM sometimes returns a plain number instead of {score, weight, reasoning}
        if isinstance(v, (int, float)):
            return {"score": float(v)}
        return v  # type: ignore[return-value]

    dims_kwargs: dict[str, QualityDimension] = {
        dim: QualityDimension(**_coerce_dim(raw_dims[dim])) for dim in _REQUIRED_DIMS
    }
    if "ebm_level" in raw_dims:
        dims_kwargs["ebm_level"] = QualityDimension(**_coerce_dim(raw_dims["ebm_level"]))

    quality_dimensions = QualityDimensions(**dims_kwargs)

    return AIAssessmentDraft(
        resource_code=resource_code,
        model_version=model_version,
        pipeline_run_id=llm_output.get("pipeline_run_id") or "",
        quality_score=float(llm_output["quality_score"]),
        ai_confidence=float(llm_output.get("ai_confidence", 50)),
        quality_dimensions=quality_dimensions,
        summary=llm_output.get("summary"),
        ai_subtype_signal=llm_output.get("ai_subtype_signal"),
        relevance_to_methodology_codes=llm_output.get("methodology_codes", []),
        relevance_to_discipline_codes=llm_output.get("relevance_to_discipline_codes", []),
        thesis_stage_signals=llm_output.get("thesis_stage_signals", []),
        difficulty_level=llm_output.get("difficulty_level"),
        proposed_badges=llm_output.get("proposed_badges", []),
        strengths=llm_output.get("strengths", []),
        limitations=llm_output.get("limitations", []),
        trainee_suitability_score=llm_output.get("trainee_suitability_score"),
        language_detected=llm_output.get("language_detected"),
    )


# ---------------------------------------------------------------------------
# Firestore write
# ---------------------------------------------------------------------------

def write_draft_assessment(draft: AIAssessmentDraft) -> str:
    """
    Write an AIAssessmentDraft to the Firestore `drafts` collection.
    Returns the auto-generated document ID.
    """
    col = get_firestore_collection(COLLECTION_DRAFTS)
    _, doc_ref = col.add(draft.firestore_dict())
    logger.info(
        "Draft assessment written: resource=%s doc_id=%s quality=%s",
        draft.resource_code, doc_ref.id, draft.quality_score,
    )
    return doc_ref.id
