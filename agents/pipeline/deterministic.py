"""
Deterministic code orchestrator — the PRODUCTION batch entrypoint.

Why this exists: the interactive LlmAgent orchestrator (agents/pipeline/agent.py)
is non-deterministic — it sometimes runs all stages, sometimes stops after one.
That's fine for exploration via `adk web`, but unacceptable for unattended batch
processing where every stage and every Firestore write is mandatory.

This module sequences the same specialised prompts and Gemini model tiers as the
8 ADK agents, but Python controls the order and performs every side-effect. The
LLM is used ONLY for judgments (scoring, classification, editorial writing). The
arbiter routing decision is pure Python — it is a deterministic gate, not a
judgment. Each stage writes pipeline_state so the console /pipeline page and the
Provenance tab reflect real progress.

Public entrypoint: `run_pipeline(resource_input: dict, pipeline_run_id: str)`.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Model tiering — same env vars as the agents (see docs/DECISIONS.md)
MODEL_FLASH = os.environ.get("MODEL_FLASH", "gemini-3.5-flash")
MODEL_FLASH_LITE = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")
MODEL_PRO = os.environ.get("MODEL_PRO", "gemini-3.1-pro-preview")

_STAGES = ["appraisal", "classification", "editorial", "reconciliation", "qc_panel", "arbiter"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def derive_resource_code(title: str, doi: str | None = None, url: str | None = None) -> str:
    """
    Kebab-case resource code + a short stable hash of the DOI/URL/title so that
    distinct resources with similar titles don't collide (audit 2026-06-06 found
    8 collisions that overwrote pipeline_state/draft_records). Same input → same code.
    """
    import hashlib
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "untitled").lower()).strip("-")[:52] or "untitled"
    seed = (doi or url or title or "").strip().lower()
    h = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:6] if seed else "000000"
    return f"{slug}-{h}"


def _load_prompt(name: str) -> str:
    path = f"agents/prompts/{name}.md"
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return f"{name} agent — see {path}"


def _llm_judgment(system_prompt: str, payload: dict, model: str, temperature: float = 0.0) -> dict:
    """
    Make one structured-output LLM call and return parsed JSON.
    Patched in tests so no real API calls are made.
    Raises ValueError if the response is not valid JSON.
    """
    from google import genai
    from google.genai import types

    # Hard per-call timeout (ms) so a stuck Vertex connection can't hang the
    # whole batch — a timeout becomes a caught error -> retry -> review_needed.
    timeout_ms = int(os.environ.get("LLM_TIMEOUT_MS", "90000"))
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        http_options=types.HttpOptions(timeout=timeout_ms),
    )
    contents = (
        f"{system_prompt}\n\n"
        f"Return ONLY a JSON object. Input resource:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=temperature,
        ),
    )
    return json.loads(resp.text)


def _as_dict(x: object) -> Optional[dict]:
    """Coerce an LLM judgment to a dict — the model sometimes wraps it in a
    JSON array. Returns the first dict element of a list, or None."""
    if isinstance(x, dict):
        return x
    if isinstance(x, list):
        for item in x:
            if isinstance(item, dict):
                return item
    return None


# Fallback when a model transiently 504s. MUST stay on Gemini 3.x — only 3.x
# is covered by the promotional credit; 2.5 incurs real charges. Cross-fall
# between covered 3.x models so a load spike on one doesn't drop the resource.
_FALLBACK_MODEL = {
    "gemini-3-flash-preview": "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite": "gemini-3-flash-preview",
    "gemini-3.1-pro-preview": "gemini-3-flash-preview",
    "gemini-3.5-flash": "gemini-3-flash-preview",
}


def _judge_with_retry(system_prompt: str, payload: dict, model: str) -> Optional[dict]:
    """
    LLM judgment with exponential backoff and a model fallback.

    Vertex's preview models intermittently return 504 DEADLINE_EXCEEDED under
    load; two immediate retries can both land in the same spike. So: attempt 1
    immediate, attempt 2 after ~3s, attempt 3 after ~12s on a stable fallback
    model. Returns a dict, or None if all attempts fail.
    """
    import time

    fallback = _FALLBACK_MODEL.get(model, model)
    attempts = [(0.0, model), (3.0, model), (12.0, fallback)]
    for i, (delay, m) in enumerate(attempts, 1):
        if delay:
            time.sleep(delay)
        try:
            result = _as_dict(_llm_judgment(system_prompt, payload, m, temperature=0.0))
            if result is not None:
                return result
            logger.warning("LLM judgment unusable (attempt %d, model=%s)", i, m)
        except Exception as exc:
            logger.warning("LLM judgment failed (attempt %d, model=%s): %s", i, m, str(exc)[:120])
    return None


# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------

_STAGE_TS_KEY = {
    "appraisal": "appraised_at",
    "classification": "classified_at",
    "editorial": "edited_at",
    "reconciliation": "reconciled_at",
    "qc_panel": "qc_panel_at",
    "arbiter": "arbiter_decision_at",
}


def _write_state(state: dict, *, stage: str, run_id: str, extra: Optional[dict] = None) -> dict:
    """Update the in-memory state dict and persist pipeline_state/{resource_code}."""
    completed = state.setdefault("stages_completed", [])
    if stage not in completed:
        completed.append(stage)
    state["current_stage"] = stage
    state["state"] = stage  # console reads either `state` or `current_stage`
    state["stages_remaining"] = [s for s in _STAGES if s not in completed]
    state["updated_at"] = _now()
    state["pipeline_run_id"] = run_id
    if stage in _STAGE_TS_KEY:
        state[_STAGE_TS_KEY[stage]] = _now()
    if extra:
        state.update(extra)
    try:
        from agents.shared.firestore_utils import get_firestore_collection, COLLECTION_PIPELINE_STATE
        get_firestore_collection(COLLECTION_PIPELINE_STATE).document(state["resource_code"]).set(state)
    except Exception as exc:
        logger.warning("pipeline_state write failed for %s: %s", state.get("resource_code"), exc)
    return state


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def run_pipeline(resource_input: dict, pipeline_run_id: str = "") -> dict:
    """
    Run the full curation pipeline deterministically on one resource.

    resource_input: {title, url, resource_type, methodology_tags, doi, pmid, description}
    Returns {resource_code, routing, reason, composite_score, outcome_detail}.
    Every stage runs in order; every Firestore write happens in code.
    """
    from agents.appraisal.tools import (
        fetch_openalex_metadata, fetch_pubmed_metadata,
        parse_appraisal_json, write_draft_assessment,
    )
    from agents.appraisal.agent import _ensure_dimensions
    from agents.classification.tools import parse_classification_json
    from agents.editorial.tools import parse_editorial_json
    from agents.reconciliation.tools import (
        is_duplicate, fetch_existing_titles, assemble_draft_record,
    )
    from agents.qc_panel.tools import (
        run_ai_pattern_scan, run_voice_review, run_plain_jargon_check,
        run_badge_check, run_taxonomy_qc_check, evaluate_dimension, aggregate_panel_results,
    )
    from agents.arbiter.tools import compute_routing_decision, compute_panel_agreement
    from agents.shared.taxonomy_rules import methodology_required_for_type
    from agents.shared.hitl import write_review_queue_item
    from agents.shared.firestore_utils import get_firestore_collection
    from agents.shared.schema import ClassificationResult, EditorialOutput, AIAssessmentDraft
    from agents.shared.codes import (
        REPORTING_GUIDELINE_GUIDE,
        CONTENT_FORMAT_MAP, content_format_for, time_to_consume_for,
    )
    from agents.shared.source_check import verify_source
    from agents.enrichment import enrich

    title = resource_input.get("title", "")
    url = resource_input.get("url", "")
    doi = resource_input.get("doi")
    rc = resource_input.get("resource_code") or derive_resource_code(title, doi=doi, url=url)
    run_id = pipeline_run_id or rc

    state = {
        "resource_code": rc,
        "started_at": _now(),
        "outcome": None,
        "discovered_at": _now(),
    }

    def _finish(routing: str, reason: str, composite: float, detail: dict) -> dict:
        _write_state(state, stage="arbiter", run_id=run_id,
                     extra={"outcome": routing,
                            "arbiter_decision": {"routing": routing,
                                                 "composite_score": composite,
                                                 "reason": reason}})
        return {"resource_code": rc, "routing": routing, "reason": reason,
                "composite_score": composite, **detail}

    orig_type = resource_input.get("resource_type") or "article"

    # ── Stage 0: Source verification — don't enrich dead/fabricated sources ─
    src = verify_source(url, doi)
    if src["status"] == "dead":
        minimal = {
            "resource_code": rc, "title": title, "url": url,
            "resource_type_code": orig_type,
            "editorial_description": "", "editorial_description_plain": "", "summary": "",
            "methodology_codes": [], "quality_score": 0, "ai_confidence": 0,
            "relevance_score": 0, "classification_confidence": 0, "proposed_badges": [],
        }
        try:
            write_review_queue_item(
                resource_code=rc, routing="review_needed",
                reason=f"Unverified source — link/DOI does not resolve (HTTP {src.get('code')})",
                panel_result={}, draft_record=minimal,
            )
        except Exception as exc:
            logger.warning("minimal review_queue write failed for %s: %s", rc, exc)
        return _finish("review_needed", "Unverified source (link/DOI does not resolve)", 0.0,
                       {"outcome_detail": "dead_source"})
    state["source_status"] = src["status"]

    # ── Stage 1: Enrichment (free sources) + Appraisal ────────────────────
    enrichment = enrich(orig_type, {
        "doi": doi, "pmid": resource_input.get("pmid"),
        "isbn": resource_input.get("isbn"), "url": url, "title": title,
    })
    metadata: dict[str, Any] = enrichment.get("type_fields", {})

    appraisal_raw = _judge_with_retry(
        _load_prompt("appraisal"),
        {"resource": resource_input, "metadata": metadata, "resource_code": rc},
        MODEL_FLASH,
    )
    if appraisal_raw is None:
        # Appraisal failed — still surface the item to a human reviewer with a
        # minimal record so it is never invisible (don't just write pipeline_state).
        minimal = {
            "resource_code": rc, "title": title, "url": url,
            "resource_type_code": resource_input.get("resource_type", "article"),
            "editorial_description": "", "editorial_description_plain": "", "summary": "",
            "methodology_codes": [], "quality_score": 0, "ai_confidence": 0,
            "relevance_score": 0, "classification_confidence": 0, "proposed_badges": [],
        }
        try:
            write_review_queue_item(resource_code=rc, routing="review_needed",
                                    reason="Appraisal LLM failed after retry — needs manual triage",
                                    panel_result={}, draft_record=minimal)
        except Exception as exc:
            logger.warning("minimal review_queue write failed for %s: %s", rc, exc)
        return _finish("review_needed", "Appraisal LLM failed after retry", 0.0,
                       {"outcome_detail": "appraisal_error"})
    appraisal_raw["resource_code"] = rc
    # `or run_id` (not setdefault) — the LLM sometimes returns pipeline_run_id: null
    appraisal_raw["pipeline_run_id"] = appraisal_raw.get("pipeline_run_id") or run_id
    draft = parse_appraisal_json(_ensure_dimensions(appraisal_raw), rc, MODEL_FLASH)
    try:
        write_draft_assessment(draft)
    except Exception as exc:
        logger.warning("write_draft_assessment failed for %s: %s", rc, exc)
    _write_state(state, stage="appraisal", run_id=run_id)

    # ── Stage 2: Classification (grounded; respects the source's real type) ─
    from agents.shared.codes import get_classification_vocabulary_guide

    cls_prompt = (
        _load_prompt("classification")
        + "\n\n"
        + get_classification_vocabulary_guide()
        + "\n\n## Resource type\nThe source was ingested as type '" + orig_type + "'. "
        "Treat this as a prior for resource_type_code, but OVERRIDE it when the metadata "
        "contradicts it — never default to 'article' for databases, registries, books, "
        "datasets, videos, or funding calls, and conversely do not keep 'reporting_guideline' "
        "for what is actually a journal article (see below).\n"
        + REPORTING_GUIDELINE_GUIDE
    )
    cls_raw = _judge_with_retry(
        cls_prompt,
        {"resource": resource_input, "metadata": metadata, "type_hint": orig_type},
        MODEL_FLASH_LITE,
    )
    classification = None
    if cls_raw:
        try:
            classification = parse_classification_json(cls_raw)
        except Exception as exc:
            from pydantic import ValidationError
            if isinstance(exc, ValidationError):
                logger.warning("Classification validation failed for %s: %s", rc, exc)
            else:
                raise
    if classification is None:
        classification = ClassificationResult(
            resource_type_code=orig_type,
            relevance_score=0.5, classification_confidence=0.5, access_type="free",
        )
    _write_state(state, stage="classification", run_id=run_id,
                 extra={"classification_result": classification.model_dump()})

    # ── Stage 3: Editorial ────────────────────────────────────────────────
    ed_raw = _judge_with_retry(
        _load_prompt("editorial"),
        {"resource": resource_input, "classification": classification.model_dump()},
        MODEL_FLASH,
    )
    if ed_raw and isinstance(ed_raw.get("proposed_badges"), list):
        # Normalise LLM badge strings ("Practical Guide") to canonical codes;
        # drop unrecognised ones so the parser doesn't reject the whole output.
        from agents.shared.codes import normalize_badge
        ed_raw["proposed_badges"] = [
            c for b in ed_raw["proposed_badges"] if (c := normalize_badge(b))
        ][:3]
    try:
        editorial = parse_editorial_json(ed_raw, resource_code=rc) if ed_raw else None
    except Exception as exc:
        logger.warning("parse_editorial_json failed for %s: %s", rc, exc)
        editorial = None
    if editorial is None:
        editorial = EditorialOutput(
            editorial_description=(ed_raw or {}).get("editorial_description", "") if ed_raw else "",
            summary=(ed_raw or {}).get("summary", "") if ed_raw else "",
            editorial_description_plain=(ed_raw or {}).get("editorial_description_plain", "") if ed_raw else "",
        )
    _write_state(state, stage="editorial", run_id=run_id)

    # ── Stage 4: Reconciliation (pure code) — within-batch + published dedup ─
    from agents.reconciliation.tools import fetch_existing_keys
    try:
        dup = is_duplicate(title, fetch_existing_keys(exclude_code=rc))
    except Exception:
        dup = None
    if dup:
        return _finish("auto_exclude", f"Duplicate of {dup.get('resource_code')}", 0.0,
                       {"outcome_detail": "duplicate"})

    record = assemble_draft_record(
        resource_code=rc, title=title, url=url,
        classification=classification, editorial=editorial, appraisal=draft,
    )
    # Completeness + enrichment fields (Wave C/D)
    final_type = record.get("resource_type_code") or orig_type
    record["content_format"] = content_format_for(final_type)
    record["type_fields"] = enrichment.get("type_fields", {})
    record["time_to_consume"] = time_to_consume_for(final_type, record["type_fields"])
    record["enrichment_sources"] = enrichment.get("enrichment_sources", [])
    if enrichment.get("needs_api_key"):
        record["enrichment_pending_keys"] = enrichment["needs_api_key"]
    try:
        get_firestore_collection("draft_records").document(rc).set(record)
    except Exception as exc:
        logger.warning("draft_records write failed for %s: %s", rc, exc)
    _write_state(state, stage="reconciliation", run_id=run_id)

    # ── Stage 5: QC Panel (deterministic checks + appraisal dimensions) ───
    panel_results = [
        run_ai_pattern_scan(f"{record['editorial_description']}\n{record.get('summary','')}\n{record['editorial_description_plain']}"),
        run_voice_review(record["editorial_description"], record.get("summary", ""), record["editorial_description_plain"]),
        run_plain_jargon_check(record["editorial_description_plain"]),
        run_badge_check(record.get("proposed_badges", [])),
        run_taxonomy_qc_check(record),
    ]
    for dim_name, dim in (draft.quality_dimensions.to_dict().items() if draft.quality_dimensions else []):
        panel_results.append(evaluate_dimension(dim_name, dim.get("score", 70), dim.get("reasoning", "")))
    panel_result = aggregate_panel_results(panel_results)
    _write_state(state, stage="qc_panel", run_id=run_id)

    # ── Stage 6: Arbiter (pure Python routing gate) ───────────────────────
    panel_agreement = compute_panel_agreement(panel_result.get("panel_scores", []))
    decision = compute_routing_decision(
        relevance_score=classification.relevance_score,
        classification_confidence=classification.classification_confidence,
        quality_score=draft.quality_score,
        ai_confidence=draft.ai_confidence,
        panel_agreement=panel_agreement,
        skip_reason=classification.skip_reason,
        has_methodology=bool(classification.methodology_codes),
        methodology_required=methodology_required_for_type(classification.resource_type_code),
    )
    routing = decision["routing"]
    reason = decision["reason"]
    composite = decision["composite_score"]

    # ── Stage 7: Outcome write ────────────────────────────────────────────
    if routing == "review_needed":
        try:
            write_review_queue_item(
                resource_code=rc, routing=routing, reason=reason,
                panel_result=panel_result, draft_record=record,
            )
        except Exception as exc:
            logger.warning("review_queue write failed for %s: %s", rc, exc)
    # auto_accept / auto_exclude: no review_queue write — outcome lives in pipeline_state.

    return _finish(routing, reason, composite, {"outcome_detail": record})
