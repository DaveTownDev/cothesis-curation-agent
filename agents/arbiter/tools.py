"""
Arbiter routing logic — deterministic gate.

Routes on 0-1 signals (classification_confidence, relevance_score)
+ 0-100 signals (quality_score, ai_confidence) + panel agreement.
Do NOT conflate the two scales.

Thresholds from .env (IMPORT_* keys):
  IMPORT_RELEVANCE_AUTO_ACCEPT=0.6
  IMPORT_RELEVANCE_AUTO_EXCLUDE=0.3
  IMPORT_CONFIDENCE_AUTO_ACCEPT=0.8
  IMPORT_CONFIDENCE_REVIEW=0.5
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# 0-1 routing thresholds
REL_AUTO_ACCEPT = float(os.environ.get("IMPORT_RELEVANCE_AUTO_ACCEPT", "0.6"))
REL_AUTO_EXCLUDE = float(os.environ.get("IMPORT_RELEVANCE_AUTO_EXCLUDE", "0.3"))
CONF_AUTO_ACCEPT = float(os.environ.get("IMPORT_CONFIDENCE_AUTO_ACCEPT", "0.8"))
CONF_REVIEW = float(os.environ.get("IMPORT_CONFIDENCE_REVIEW", "0.5"))
PANEL_AGREE_THRESHOLD = 0.7

# 0-100 quality thresholds
QUALITY_AUTO_ACCEPT = 80.0
QUALITY_EXCLUDE = 60.0
AI_CONFIDENCE_REVIEW = 70.0


def compute_routing_decision(
    relevance_score: float,
    classification_confidence: float,
    quality_score: float,
    ai_confidence: float,
    panel_agreement: float,
    skip_reason: Optional[str],
) -> dict:
    """
    Compute the arbiter's routing decision.
    Returns {"routing": str, "composite_score": float, "reason": str}.

    Routing outcomes:
      auto_accept   — high confidence, high relevance, high quality, panel agrees
      review_needed — borderline on any signal; human must decide
      auto_exclude  — skip_reason set, very low relevance, or very low quality
    """
    composite = _compute_composite_score(
        relevance_score, classification_confidence, quality_score,
        ai_confidence, panel_agreement,
    )

    # 1. skip_reason always excludes
    if skip_reason:
        return {
            "routing": "auto_exclude",
            "composite_score": composite,
            "reason": f"skip_reason set: {skip_reason}",
        }

    # 2. Quality floor — very low quality excludes regardless of routing signals
    if quality_score < QUALITY_EXCLUDE:
        return {
            "routing": "auto_exclude",
            "composite_score": composite,
            "reason": f"quality_score={quality_score:.1f} < {QUALITY_EXCLUDE} floor",
        }

    # 3. Low relevance with high classifier confidence → irrelevant, exclude
    if classification_confidence >= CONF_AUTO_ACCEPT and relevance_score < REL_AUTO_EXCLUDE:
        return {
            "routing": "auto_exclude",
            "composite_score": composite,
            "reason": (
                f"relevance_score={relevance_score:.2f} < {REL_AUTO_EXCLUDE} "
                f"(classifier confident at {classification_confidence:.2f})"
            ),
        }

    # 4. auto_accept: all signals green
    if (
        classification_confidence >= CONF_AUTO_ACCEPT
        and relevance_score >= REL_AUTO_ACCEPT
        and quality_score >= QUALITY_AUTO_ACCEPT
        and ai_confidence >= AI_CONFIDENCE_REVIEW
        and panel_agreement >= PANEL_AGREE_THRESHOLD
    ):
        return {
            "routing": "auto_accept",
            "composite_score": composite,
            "reason": (
                f"all signals green — conf={classification_confidence:.2f}, "
                f"rel={relevance_score:.2f}, quality={quality_score:.1f}, "
                f"ai_conf={ai_confidence:.1f}, panel={panel_agreement:.2f}"
            ),
        }

    # 5. Everything else → review_needed; explain which signal failed
    reasons = []
    if classification_confidence < CONF_REVIEW:
        reasons.append(f"classification_confidence={classification_confidence:.2f} < {CONF_REVIEW}")
    if relevance_score < REL_AUTO_ACCEPT:
        reasons.append(f"relevance_score={relevance_score:.2f} < {REL_AUTO_ACCEPT}")
    if QUALITY_EXCLUDE <= quality_score < QUALITY_AUTO_ACCEPT:
        reasons.append(f"quality_score={quality_score:.1f} in review band 60-79")
    if ai_confidence < AI_CONFIDENCE_REVIEW:
        reasons.append(f"ai_confidence={ai_confidence:.1f} < {AI_CONFIDENCE_REVIEW}")
    if panel_agreement < PANEL_AGREE_THRESHOLD:
        reasons.append(f"panel_agreement={panel_agreement:.2f} < {PANEL_AGREE_THRESHOLD}")
    if not reasons:
        reasons.append("borderline signals — defaulting to human review")

    return {
        "routing": "review_needed",
        "composite_score": composite,
        "reason": "; ".join(reasons),
    }


def _compute_composite_score(
    relevance_score: float,
    classification_confidence: float,
    quality_score: float,
    ai_confidence: float,
    panel_agreement: float,
) -> float:
    """
    Weighted composite score (0-100).
    quality_score and ai_confidence are already 0-100.
    relevance_score, classification_confidence, panel_agreement normalised × 100.
    """
    return round(
        quality_score * 0.40
        + ai_confidence * 0.20
        + relevance_score * 100 * 0.15
        + classification_confidence * 100 * 0.15
        + panel_agreement * 100 * 0.10,
        1,
    )


def compute_panel_agreement(panel_scores: list[dict]) -> float:
    """
    Compute panel agreement as the fraction of evaluators that passed.
    Returns 0.0 for empty panel.
    """
    if not panel_scores:
        return 0.0
    pass_count = sum(1 for s in panel_scores if s.get("pass", False))
    return round(pass_count / len(panel_scores), 3)
