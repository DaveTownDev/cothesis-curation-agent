"""
QC Panel tools — evaluator helpers.

The panel runs:
  - 6 dimension evaluators (one per quality dimension)
  - ai_pattern_scanner — detects AI tell / non-editorial voice
  - voice_reviewer — brand voice check
  - claim_verifier — factual claims vs source
  - ref_checker — DOI / URL reachability

Each evaluator returns:
  {"dimension": str, "score": float (0-100), "pass": bool, "reasoning": str}
"""
from __future__ import annotations

import logging
import re
from typing import Any

from agents.shared.codes import PLAIN_JARGON_TERMS, CANONICAL_BADGES

logger = logging.getLogger(__name__)

_PASS_THRESHOLD = 60.0  # score >= 60 = pass for a panel dimension

# AI tell patterns (phrases that signal LLM-generated text leaking through)
_AI_TELL_PATTERNS = [
    r"\bI(?:'d| would) (?:like to|be happy to)\b",
    r"\bcertainly\b",
    r"\bof course\b",
    r"\bas an AI\b",
    r"\bfeel free to\b",
    r"\blet me know if\b",
    r"\bI hope this helps\b",
    r"\bIn conclusion\b",
    r"\bIn summary\b",
]

# Brand banned phrases (disparaging, judgemental)
_BRAND_BANNED = [
    "isn't for you",
    "not suitable for",
    "avoid",
    "unfortunately",
    "poor quality",
    "not recommended",
    "outdated",
    "inferior",
]


def evaluate_dimension(dimension_name: str, score: float, reasoning: str) -> dict:
    """Build a panel evaluator result for a single quality dimension."""
    return {
        "dimension": dimension_name,
        "score": round(float(score), 1),
        "pass": score >= _PASS_THRESHOLD,
        "reasoning": reasoning,
    }


def run_ai_pattern_scan(text: str) -> dict:
    """
    Check all text fields for AI tell patterns (non-editorial voice).
    Returns a panel evaluator result.
    """
    violations = []
    for pattern in _AI_TELL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(pattern)

    if violations:
        return evaluate_dimension(
            "ai_pattern_scanner",
            score=20.0,
            reasoning=f"AI tell patterns detected: {violations}",
        )
    return evaluate_dimension(
        "ai_pattern_scanner",
        score=95.0,
        reasoning="No AI tell patterns detected.",
    )


def run_voice_review(editorial_description: str, summary: str,
                     editorial_description_plain: str) -> dict:
    """
    Check editorial copy for brand voice violations (disparaging, negative framing).
    """
    combined = f"{editorial_description}\n{summary}\n{editorial_description_plain}"
    violations = [phrase for phrase in _BRAND_BANNED if phrase.lower() in combined.lower()]

    if violations:
        return evaluate_dimension(
            "voice_reviewer",
            score=25.0,
            reasoning=f"Brand voice violations: {violations}",
        )
    return evaluate_dimension(
        "voice_reviewer",
        score=90.0,
        reasoning="Brand voice check passed — no banned phrases.",
    )


def run_plain_jargon_check(editorial_description_plain: str) -> dict:
    """Check plain field for research jargon (must be clean for QC pass)."""
    violations = [t for t in PLAIN_JARGON_TERMS if t in editorial_description_plain.lower()]
    if violations:
        return evaluate_dimension(
            "plain_jargon_check",
            score=10.0,
            reasoning=f"Research jargon in plain field: {violations}",
        )
    return evaluate_dimension(
        "plain_jargon_check",
        score=100.0,
        reasoning="Plain field is jargon-free.",
    )


def run_badge_check(proposed_badges: list[str]) -> dict:
    """Verify proposed badges are from the canonical set."""
    invalid = [b for b in proposed_badges if b not in CANONICAL_BADGES]
    if invalid:
        return evaluate_dimension(
            "badge_check",
            score=0.0,
            reasoning=f"Non-canonical badges: {invalid}",
        )
    return evaluate_dimension(
        "badge_check",
        score=100.0,
        reasoning=f"All badges canonical: {proposed_badges}",
    )


def aggregate_panel_results(results: list[dict]) -> dict:
    """
    Aggregate panel evaluator results.
    Returns {"panel_scores": [...], "panel_agreement": float,
             "overall_pass": bool, "summary": str}
    """
    if not results:
        return {"panel_scores": [], "panel_agreement": 0.0,
                "overall_pass": False, "summary": "No panel results"}

    pass_count = sum(1 for r in results if r.get("pass", False))
    agreement = round(pass_count / len(results), 3)
    avg_score = round(sum(r["score"] for r in results) / len(results), 1)

    failures = [r["dimension"] for r in results if not r.get("pass", False)]
    summary = (
        f"Panel: {pass_count}/{len(results)} pass, avg_score={avg_score}, "
        f"agreement={agreement}"
        + (f"; failed: {failures}" if failures else "")
    )

    return {
        "panel_scores": results,
        "panel_agreement": agreement,
        "overall_pass": agreement >= 0.7,
        "avg_score": avg_score,
        "summary": summary,
    }
