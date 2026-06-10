"""
Reconciliation agent tools — dedup + draft record assembly.

Dedup: title similarity >= IMPORT_TITLE_SIMILARITY_THRESHOLD (0.9) → duplicate.
Assembly: combines Classification + Editorial + Appraisal into the full draft record.
"""
from __future__ import annotations

import difflib
import logging
import os
from typing import Optional

from agents.shared.schema import (
    AIAssessmentDraft,
    ClassificationResult,
    EditorialOutput,
)

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = float(os.environ.get("IMPORT_TITLE_SIMILARITY_THRESHOLD", "0.9"))


def title_similarity(a: str, b: str) -> float:
    """Normalised title similarity using SequenceMatcher (case-insensitive)."""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def is_duplicate(
    candidate_title: str,
    existing: list[dict],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Optional[dict]:
    """
    Check candidate_title against a list of existing resource dicts.
    Returns the first matching existing record or None.
    existing items must have at least {"title": str, "resource_code": str}.
    """
    for record in existing:
        score = title_similarity(candidate_title, record.get("title", ""))
        if score >= threshold:
            logger.info(
                "Duplicate detected: %r ~ %r (score=%.3f)",
                candidate_title, record["title"], score,
            )
            return record
    return None


def assemble_draft_record(
    resource_code: str,
    title: str,
    url: str,
    classification: ClassificationResult,
    editorial: EditorialOutput,
    appraisal: AIAssessmentDraft,
    alternative_titles: Optional[list[str]] = None,
) -> dict:
    """
    Assemble the final draft Resource record from the three agent outputs.
    Sets editorial_status: 'proposed'. type_fields is empty for MVP;
    populated downstream from field_mapping_*.md.
    """
    return {
        # Identity
        "resource_code": resource_code,
        "title": title,
        "url": url,
        # Type
        "resource_type_code": classification.resource_type_code,
        "resource_subtype_code": classification.resource_subtype_code,
        # Editorial (AI-drafted, human-ratified later)
        "editorial_description": editorial.editorial_description,
        "editorial_description_plain": editorial.editorial_description_plain,
        # Classification signals
        "methodology_codes": classification.methodology_codes,
        "discipline_codes": classification.discipline_codes,
        "stage_codes": classification.stage_codes,
        "difficulty_level": editorial.difficulty_level or classification.difficulty_level,
        "access_type": classification.access_type,
        # Quality (from Appraisal)
        "quality_score": appraisal.quality_score,
        "ai_confidence": appraisal.ai_confidence,
        "quality_dimensions": appraisal.quality_dimensions.to_dict(),
        "trainee_suitability_score": appraisal.trainee_suitability_score,
        "language_detected": appraisal.language_detected,
        "strengths": appraisal.strengths,
        "limitations": appraisal.limitations,
        "current_ai_assessment_id": None,  # set after Firestore write
        # Routing signals (0-1 scale)
        "relevance_score": classification.relevance_score,
        "classification_confidence": classification.classification_confidence,
        # Proposed badges (AI; ratified by human later)
        "proposed_badges": editorial.proposed_badges,
        # Foundation Skills
        "skill_codes": classification.skill_codes,
        # Long display slot (stored on AIAssessment; passed through here for console)
        "summary": editorial.summary,
        # Search surface
        "alternative_titles": alternative_titles or [],
        # Extension (type-specific fields; populated from field_maps)
        "type_fields": {},
        # Pipeline state
        "editorial_status": "proposed",
        "requires_human_review": appraisal.requires_human_review,
    }


def fetch_existing_titles() -> list[dict]:
    """
    Fetch resource titles from Firestore `resources` collection for dedup.
    Returns list of {"title": str, "resource_code": str}.
    """
    from agents.shared.firestore_utils import get_firestore_collection, COLLECTION_RESOURCES
    try:
        col = get_firestore_collection(COLLECTION_RESOURCES)
        # MVP limit: 500 titles. Sufficient for early Compendium; revisit at scale.
        docs = col.select(["title", "resource_code"]).limit(500).stream()
        return [{"title": d.get("title", ""), "resource_code": d.id} for d in docs]
    except Exception as exc:
        logger.warning("Could not fetch existing titles for dedup: %s", exc)
        return []


def fetch_existing_keys(exclude_code: str | None = None) -> list[dict]:
    """
    Titles already seen — published `resources` AND in-flight `draft_records`
    (within-batch dedup; the source queue contains duplicates that the
    published-only check missed — audit 2026-06-06).
    Returns list of {"title", "resource_code"}; excludes `exclude_code` (self).
    """
    from agents.shared.firestore_utils import get_firestore_collection
    out: list[dict] = []
    for coll in ("resources", "draft_records"):
        try:
            for d in get_firestore_collection(coll).select(["title"]).limit(1000).stream():
                if d.id == exclude_code:
                    continue
                out.append({"title": (d.to_dict() or {}).get("title", ""), "resource_code": d.id})
        except Exception as exc:
            logger.warning("fetch_existing_keys(%s) failed: %s", coll, exc)
    return out
