"""Tests for the audit-driven fixes: no-MVP routing, completeness helpers, dead-source guard."""
from unittest.mock import MagicMock, patch
import pytest

from agents.arbiter.tools import compute_routing_decision
from agents.shared.codes import content_format_for, time_to_consume_for


# ── Arbiter: no MVP methodology never auto-accepts ───────────────────────────

def test_no_mvp_methodology_routes_review_not_accept():
    # All signals would otherwise auto-accept
    d = compute_routing_decision(
        relevance_score=0.9, classification_confidence=0.9, quality_score=90,
        ai_confidence=90, panel_agreement=1.0, skip_reason=None,
        has_mvp_methodology=False,
    )
    assert d["routing"] == "review_needed"
    assert "MVP" in d["reason"]


def test_with_mvp_methodology_still_auto_accepts():
    d = compute_routing_decision(
        relevance_score=0.9, classification_confidence=0.9, quality_score=90,
        ai_confidence=90, panel_agreement=1.0, skip_reason=None,
        has_mvp_methodology=True,
    )
    assert d["routing"] == "auto_accept"


def test_no_mvp_but_low_quality_still_excludes():
    d = compute_routing_decision(
        relevance_score=0.9, classification_confidence=0.9, quality_score=40,
        ai_confidence=90, panel_agreement=1.0, skip_reason=None,
        has_mvp_methodology=False,
    )
    assert d["routing"] == "auto_exclude"


# ── Completeness helpers ─────────────────────────────────────────────────────

@pytest.mark.parametrize("rtype,fmt", [
    ("article", "text"), ("video", "video"), ("podcast", "audio"),
    ("software", "interactive"), ("dataset", "data"), ("reporting_guideline", "pdf"),
])
def test_content_format_map(rtype, fmt):
    assert content_format_for(rtype) == fmt


def test_time_to_consume_uses_page_count():
    assert "hour" in time_to_consume_for("book", {"page_count": 300})
    assert time_to_consume_for("article", {}) == "~20–40 min"


# ── run_pipeline: dead source is guarded before any LLM call ─────────────────

def test_dead_source_routes_review_without_llm(monkeypatch):
    from agents.pipeline import deterministic as det
    queue = []
    monkeypatch.setattr("agents.shared.source_check.verify_source",
                        lambda url, doi=None, **k: {"status": "dead", "code": 404, "final_url": url, "resolved": False})
    monkeypatch.setattr("agents.shared.hitl.write_review_queue_item",
                        lambda **kw: queue.append(kw) or "qid")
    monkeypatch.setattr("agents.shared.firestore_utils.get_firestore_collection",
                        lambda name: MagicMock())
    # If any LLM call happens, fail loudly
    monkeypatch.setattr("agents.pipeline.deterministic._judge_with_retry",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("LLM must not be called for a dead source")))
    out = det.run_pipeline({"title": "Fake", "url": "https://x/404", "doi": "10.0/fake",
                            "resource_type": "article"}, pipeline_run_id="t")
    assert out["routing"] == "review_needed"
    assert "Unverified source" in out["reason"]
    assert len(queue) == 1 and queue[0]["routing"] == "review_needed"
