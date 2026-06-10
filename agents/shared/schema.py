"""
Canonical Pydantic models for the CoThesis curation pipeline.
Source of truth: docs/SCHEMA.md + docs/reference/entities/AIAssessment.canonical.md
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated
from pydantic import conlist


# ---------------------------------------------------------------------------
# Quality dimension models
# ---------------------------------------------------------------------------

class QualityDimension(BaseModel):
    score: float = Field(..., ge=0, le=100)
    weight: float = Field(default=0.1, ge=0, le=1)
    reasoning: str = Field(default="")

    @field_validator("weight", mode="before")
    @classmethod
    def normalise_weight(cls, v: object) -> float:
        # LLM sometimes returns weight as a percentage (e.g. 20) instead of fraction (0.2)
        v = float(v) if v is not None else 0.1
        return v / 100.0 if v > 1.0 else v


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


# ---------------------------------------------------------------------------
# ClassificationResult (Classification agent output)
# ---------------------------------------------------------------------------

class ClassificationResult(BaseModel):
    resource_type_code: str
    resource_subtype_code: Optional[str] = None
    methodology_codes: list[str] = Field(default_factory=list)
    stage_codes: list[str] = Field(default_factory=list)
    skill_codes: list[str] = Field(default_factory=list)  # FS-01..FS-16
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    classification_confidence: float = Field(..., ge=0.0, le=1.0)
    relevance_reasoning: Optional[str] = None
    access_type: str
    skip_reason: Optional[str] = None
    discipline_codes: list[str] = Field(default_factory=list)
    difficulty_level: Optional[str] = None

    @field_validator("resource_type_code")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        from agents.shared.codes import RESOURCE_TYPES
        if v not in RESOURCE_TYPES:
            raise ValueError(f"Invalid resource_type_code {v!r}. Must be one of {sorted(RESOURCE_TYPES)}")
        return v

    @field_validator("methodology_codes")
    @classmethod
    def validate_methodology_codes(cls, codes: list[str]) -> list[str]:
        from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
        from agents.taxonomy import is_valid_methodology_code, normalize_methodology_code
        normalized: list[str] = []
        for code in codes:
            for legacy in LEGACY_METHODOLOGY_PREFIXES:
                if code.startswith(legacy):
                    raise ValueError(
                        f"Legacy methodology code {code!r} (prefix {legacy!r}) detected. "
                        f"Emit platform codes (SYN-, OBS-, EVAL-…) per docs/TAXONOMY.md."
                    )
            norm = normalize_methodology_code(code)
            if not is_valid_methodology_code(norm):
                raise ValueError(
                    f"Invalid methodology code {code!r}. "
                    f"Must be a live platform code from data/taxonomy/live_methodologies.json."
                )
            normalized.append(norm)
        return normalized

    @field_validator("discipline_codes")
    @classmethod
    def validate_discipline_codes(cls, codes: list[str]) -> list[str]:
        from agents.taxonomy import is_valid_discipline_slug, normalize_discipline_slug
        normalized: list[str] = []
        for slug in codes:
            norm = normalize_discipline_slug(slug)
            if not is_valid_discipline_slug(norm):
                raise ValueError(
                    f"Invalid discipline slug {slug!r}. "
                    f"Must be a live specialty slug from data/taxonomy/live_specialties.json."
                )
            normalized.append(norm)
        return normalized

    @field_validator("stage_codes")
    @classmethod
    def validate_stage_codes(cls, codes: list[str]) -> list[str]:
        from agents.shared.codes import STAGE_CODES
        for code in codes:
            if code not in STAGE_CODES:
                raise ValueError(f"Invalid stage_code {code!r}. Must be one of {sorted(STAGE_CODES)}")
        return codes

    @field_validator("skill_codes")
    @classmethod
    def validate_skill_codes(cls, codes: list[str]) -> list[str]:
        from agents.taxonomy import is_valid_skill_code, normalize_skill_code
        normalized: list[str] = []
        for code in codes:
            norm = normalize_skill_code(code)
            if not is_valid_skill_code(norm):
                raise ValueError(
                    f"Invalid skill code {code!r}. "
                    f"Must be a foundation skill code from data/taxonomy/live_skills.json."
                )
            normalized.append(norm)
        return normalized

    @field_validator("resource_subtype_code")
    @classmethod
    def validate_resource_subtype_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        from agents.taxonomy import is_valid_subtype_code, normalize_subtype_code
        norm = normalize_subtype_code(v)
        if not is_valid_subtype_code(norm):
            raise ValueError(
                f"Invalid resource_subtype_code {v!r}. "
                f"Must be a live subtype code from data/taxonomy/live_subtypes.json."
            )
        return norm

    @model_validator(mode="after")
    def validate_subtype_matches_type(self) -> "ClassificationResult":
        from agents.taxonomy import subtype_type_for
        if self.resource_type_code == "book_chapter":
            if self.resource_subtype_code is not None:
                raise ValueError("book_chapter resources must have resource_subtype_code null")
            return self
        if self.resource_subtype_code is not None:
            parent = subtype_type_for(self.resource_subtype_code)
            if parent != self.resource_type_code:
                raise ValueError(
                    f"resource_subtype_code {self.resource_subtype_code!r} belongs to "
                    f"type {parent!r}, not {self.resource_type_code!r}"
                )
        return self


# ---------------------------------------------------------------------------
# EditorialOutput (Editorial agent output)
# ---------------------------------------------------------------------------

class EditorialOutput(BaseModel):
    editorial_description: str
    summary: str
    editorial_description_plain: str
    proposed_badges: Annotated[list[str], Field(max_length=3)] = Field(default_factory=list)
    difficulty_level: str = "intermediate"  # default — LLM sometimes omits

    @field_validator("proposed_badges")
    @classmethod
    def validate_badges(cls, badges: list[str]) -> list[str]:
        from agents.shared.codes import CANONICAL_BADGES
        for badge in badges:
            if badge not in CANONICAL_BADGES:
                raise ValueError(f"Invalid badge {badge!r}. Must be from canonical set: {sorted(CANONICAL_BADGES)}")
        return badges

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        from agents.shared.codes import DIFFICULTY_LEVELS
        if v not in DIFFICULTY_LEVELS:
            raise ValueError(f"Invalid difficulty_level {v!r}. Must be one of {sorted(DIFFICULTY_LEVELS)}")
        return v
