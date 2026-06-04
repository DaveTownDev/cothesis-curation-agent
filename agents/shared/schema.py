"""
Canonical Pydantic models for the CoThesis curation pipeline.
Source of truth: docs/SCHEMA.md + docs/reference/entities/AIAssessment.canonical.md
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Quality dimension models
# ---------------------------------------------------------------------------

class QualityDimension(BaseModel):
    score: float = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    reasoning: str


class QualityDimensions(BaseModel):
    """
    6 universal dimensions (every resource type) plus ebm_level
    (articles only — omit / leave None for all other types).
    """
    relevance: QualityDimension
    accuracy: QualityDimension
    authority: QualityDimension
    currency: QualityDimension
    accessibility: QualityDimension
    practical_utility: QualityDimension
    ebm_level: Optional[QualityDimension] = None

    @classmethod
    def make_stub(cls, ebm_level: Optional[QualityDimension] = None) -> "QualityDimensions":
        """Convenience factory for tests — produces a neutral 70/0.1 stub."""
        dim = QualityDimension(score=70.0, weight=0.1, reasoning="stub")
        return cls(
            relevance=dim,
            accuracy=dim,
            authority=dim,
            currency=dim,
            accessibility=dim,
            practical_utility=QualityDimension(score=70.0, weight=0.4, reasoning="stub"),
            ebm_level=ebm_level,
        )

    def to_dict(self) -> dict:
        result = {}
        for field_name in ("relevance", "accuracy", "authority",
                           "currency", "accessibility", "practical_utility"):
            result[field_name] = getattr(self, field_name).model_dump()
        if self.ebm_level is not None:
            result["ebm_level"] = self.ebm_level.model_dump()
        return result


# ---------------------------------------------------------------------------
# AIAssessment draft (written to Firestore `drafts` collection)
# ---------------------------------------------------------------------------

class AIAssessmentDraft(BaseModel):
    """
    The Appraisal agent's output — stored in Firestore `drafts`.
    Routing thresholds (docs/SCHEMA.md):
      quality_score >= 80 + ai_confidence >= 70 → auto-accept
      quality_score 60-79 OR ai_confidence < 70 → requires_human_review=True
      quality_score < 60 → auto-reject (arbiter sets this)
    """
    resource_code: str
    model_version: str
    pipeline_run_id: str

    quality_score: float = Field(..., ge=0, le=100)
    ai_confidence: float = Field(..., ge=0, le=100)
    quality_dimensions: QualityDimensions

    # Optional enrichment fields
    summary: Optional[str] = None
    ai_subtype_signal: Optional[str] = None
    relevance_to_methodology_codes: list[str] = Field(default_factory=list)
    relevance_to_discipline_codes: list[str] = Field(default_factory=list)
    thesis_stage_signals: list[str] = Field(default_factory=list)
    difficulty_level: Optional[str] = None
    proposed_badges: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    trainee_suitability_score: Optional[float] = Field(default=None, ge=0, le=100)
    language_detected: Optional[str] = None
    assessment_prompt_version: Optional[str] = None

    # Computed — do not set manually
    requires_human_review: bool = False
    assessed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def compute_review_flag(self) -> "AIAssessmentDraft":
        self.requires_human_review = (
            self.ai_confidence < 70 or 60 <= self.quality_score < 80
        )
        if self.assessed_at is None:
            self.assessed_at = datetime.now(timezone.utc)
        return self

    def firestore_dict(self) -> dict:
        d = self.model_dump()
        d["quality_dimensions"] = self.quality_dimensions.to_dict()
        d["assessed_at"] = self.assessed_at.isoformat()
        return d


# ---------------------------------------------------------------------------
# Candidate resource (Discovery agent output → Appraisal input)
# ---------------------------------------------------------------------------

class CandidateResource(BaseModel):
    title: str
    url: str
    source: str
    type_hint: str
    raw_metadata: dict = Field(default_factory=dict)
    skip_reason: Optional[str] = None

    @property
    def is_processable(self) -> bool:
        return self.skip_reason is None
