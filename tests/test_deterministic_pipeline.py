"""
Tests for agents/pipeline/deterministic.py — the production code orchestrator.

All LLM calls and Firestore writes are mocked; no external calls.
_judge_with_retry is called once per LLM stage in order:
  [appraisal, classification, editorial]
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


# ── Canned LLM judgments ─────────────────────────────────────────────────────

APPRAISAL_OK = {"quality_score": 85, "ai_confidence": 90, "summary": "A solid resource."}

CLASSIFICATION_AUTO = {
    "resource_type_code": "article",
    "methodology_codes": ["OBS-01"],
    "stage_codes": ["EV"],
    "relevance_score": 0.9,
    "classification_confidence": 0.9,
    "access_type": "free",
    "discipline_codes": [],
    "skill_codes": [],
}
CLASSIFICATION_REVIEW = {**CLASSIFICATION_AUTO, "classification_confidence": 0.4, "relevance_score": 0.5}
CLASSIFICATION_SKIP = {**CLASSIFICATION_AUTO, "skip_reason": "Not a discrete citable resource"}

EDITORIAL_OK = {
    "editorial_description": "A practical guide to reviewing medical records for research.",
    "summary": "This resource walks through how to design and run a structured review of existing records.",
    "editorial_description_plain": "How to study information already collected about patients to answer a question.",
    "proposed_badges": ["editors_choice"],
    "difficulty_level": "intermediate",
}

RESOURCE = {
    "title": "A Guide to the Retrospective Chart Review",
    "url": "https://example.com/guide",
    "resource_type": "article",
    "methodology_tags": ["cohort-study"],
    "doi": None,
    "pmid": None,
}


# ── Fixtures: patch all external side-effects ────────────────────────────────

@pytest.fixture
def mocked(monkeypatch):
    """Patch LLM, metadata fetch, and all Firestore writes. Returns recorders."""
    rec = {"queue": [], "state": MagicMock(), "drafts": []}

    # No metadata fetch (avoid HTTP)
    monkeypatch.setattr("agents.appraisal.tools.fetch_openalex_metadata", lambda **k: {})
    monkeypatch.setattr("agents.appraisal.tools.fetch_pubmed_metadata", lambda **k: {})
    # Source verification → live (no HTTP); enrichment → empty (no HTTP)
    monkeypatch.setattr("agents.shared.source_check.verify_source",
                        lambda url, doi=None, **k: {"status": "live", "code": 200, "final_url": url, "resolved": True})
    monkeypatch.setattr("agents.enrichment.enrich",
                        lambda rtype, ids: {"type_fields": {}, "enrichment_sources": [], "needs_api_key": []})
    # No draft write
    monkeypatch.setattr("agents.appraisal.tools.write_draft_assessment",
                        lambda d: rec["drafts"].append(d) or "draft-id")
    # No existing titles (no dup) unless a test overrides
    monkeypatch.setattr("agents.reconciliation.tools.fetch_existing_titles", lambda: [])
    monkeypatch.setattr("agents.reconciliation.tools.fetch_existing_keys", lambda exclude_code=None: [])
    # Capture review_queue writes
    monkeypatch.setattr("agents.shared.hitl.write_review_queue_item",
                        lambda **kw: rec["queue"].append(kw) or "queue-id")
    # Firestore collection → MagicMock (captures draft_records + pipeline_state .set())
    monkeypatch.setattr("agents.shared.firestore_utils.get_firestore_collection",
                        lambda name: rec["state"])
    return rec


def _patch_judgments(values):
    """Patch _judge_with_retry with an ordered side_effect list."""
    return patch("agents.pipeline.deterministic._judge_with_retry", side_effect=values)


# ── Happy path ───────────────────────────────────────────────────────────────

class TestHappyPath:
    def test_auto_accept_runs_all_stages(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        with _patch_judgments([APPRAISAL_OK, CLASSIFICATION_AUTO, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="run-1")
        assert out["routing"] == "auto_accept"
        assert out["resource_code"].startswith("a-guide-to-the-retrospective-chart-review")
        # Draft written, queue item written (auto_accept still queues for ratification)
        assert len(mocked["drafts"]) == 1
        assert len(mocked["queue"]) == 1
        assert mocked["queue"][0]["routing"] == "auto_accept"
        # Queue item carries the full assembled record
        assert mocked["queue"][0]["draft_record"]["title"] == RESOURCE["title"]

    def test_pipeline_state_written_each_stage(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        with _patch_judgments([APPRAISAL_OK, CLASSIFICATION_AUTO, EDITORIAL_OK]):
            run_pipeline(RESOURCE, pipeline_run_id="run-1")
        # pipeline_state .set() called multiple times (once per stage + final)
        assert mocked["state"].document.return_value.set.call_count >= 6


# ── Routing outcomes ─────────────────────────────────────────────────────────

class TestRouting:
    def test_low_confidence_routes_review(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        with _patch_judgments([APPRAISAL_OK, CLASSIFICATION_REVIEW, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        assert out["routing"] == "review_needed"
        assert len(mocked["queue"]) == 1
        assert mocked["queue"][0]["routing"] == "review_needed"

    def test_skip_reason_routes_exclude(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        with _patch_judgments([APPRAISAL_OK, CLASSIFICATION_SKIP, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        assert out["routing"] == "auto_exclude"
        # auto_exclude does not write to the review queue
        assert len(mocked["queue"]) == 0

    def test_low_quality_routes_exclude(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        low_quality = {"quality_score": 40, "ai_confidence": 90}
        with _patch_judgments([low_quality, CLASSIFICATION_AUTO, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        assert out["routing"] == "auto_exclude"


# ── Dedup ────────────────────────────────────────────────────────────────────

class TestDedup:
    def test_duplicate_stops_and_excludes(self, mocked, monkeypatch):
        from agents.pipeline.deterministic import run_pipeline
        monkeypatch.setattr(
            "agents.reconciliation.tools.fetch_existing_keys",
            lambda exclude_code=None: [{"title": RESOURCE["title"], "resource_code": "existing-001"}],
        )
        with _patch_judgments([APPRAISAL_OK, CLASSIFICATION_AUTO, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        assert out["routing"] == "auto_exclude"
        assert "existing-001" in out["reason"]
        assert len(mocked["queue"]) == 0


# ── LLM failure handling ─────────────────────────────────────────────────────

class TestLLMFailure:
    def test_appraisal_failure_routes_review(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        with _patch_judgments([None, CLASSIFICATION_AUTO, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        assert out["routing"] == "review_needed"
        assert "Appraisal LLM failed" in out["reason"]

    def test_classification_failure_uses_default(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        # classification None → default (conf 0.5) → review_needed, pipeline continues
        with _patch_judgments([APPRAISAL_OK, None, EDITORIAL_OK]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        assert out["routing"] == "review_needed"
        assert len(mocked["drafts"]) == 1  # appraisal still ran

    def test_editorial_failure_uses_stub(self, mocked):
        from agents.pipeline.deterministic import run_pipeline
        with _patch_judgments([APPRAISAL_OK, CLASSIFICATION_AUTO, None]):
            out = run_pipeline(RESOURCE, pipeline_run_id="r")
        # editorial stub → empty descriptions → jargon check passes but record still assembled
        assert out["routing"] in ("auto_accept", "review_needed")
        assert out["resource_code"]


# ── Resource code derivation ─────────────────────────────────────────────────

def test_derive_resource_code():
    from agents.pipeline.deterministic import derive_resource_code
    # kebab slug + short stable hash suffix
    code = derive_resource_code("PRISMA 2020 Statement!", doi="10.1136/bmj.n71")
    assert code.startswith("prisma-2020-statement-")
    # same input -> same code (stable/idempotent)
    assert code == derive_resource_code("PRISMA 2020 Statement!", doi="10.1136/bmj.n71")
    # different DOI -> different code (no collision)
    assert code != derive_resource_code("PRISMA 2020 Statement!", doi="10.9999/other")
    assert derive_resource_code("").startswith("untitled")
