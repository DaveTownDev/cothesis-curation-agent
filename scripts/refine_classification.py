"""
Re-run the classification stage for one review_queue resource (no full pipeline).

Use after prompt changes or HITL taxonomy flags to replay classification only.
Updates draft_record taxonomy fields and pipeline_state.classification_result.

  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.refine_classification RC-001
  .venv/bin/python -m scripts.refine_classification RC-001 --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_CLASSIFICATION_FIELDS = (
    "resource_type_code",
    "resource_subtype_code",
    "methodology_codes",
    "discipline_codes",
    "stage_codes",
    "skill_codes",
    "relevance_score",
    "classification_confidence",
    "access_type",
    "difficulty_level",
    "skip_reason",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_classification_prompt(orig_type: str) -> str:
    from agents.pipeline.deterministic import _load_prompt
    from agents.shared.codes import (
        METHODOLOGY_GUIDE,
        REPORTING_GUIDELINE_GUIDE,
        get_discipline_guide,
        get_skill_guide,
        get_subtype_guide,
    )

    return (
        _load_prompt("classification")
        + "\n\n## Methodology grounding (assign the best match or [] — do NOT force-fit)\n"
        + METHODOLOGY_GUIDE
        + "\n\n## Specialty / discipline slugs\n"
        + get_discipline_guide()
        + "\n\n## Resource subtypes\n"
        + get_subtype_guide()
        + "\n\n## Foundation skills\n"
        + get_skill_guide()
        + "\n\n## Resource type\nThe source was ingested as type '" + orig_type + "'. "
        "Treat this as a prior for resource_type_code, but OVERRIDE it when the metadata "
        "contradicts it — never default to 'article' for databases, registries, books, "
        "datasets, videos, or funding calls, and conversely do not keep 'reporting_guideline' "
        "for what is actually a journal article (see below).\n"
        + REPORTING_GUIDELINE_GUIDE
    )


def refine_classification_for_resource(
    resource_code: str,
    *,
    dry_run: bool = False,
    db: Any | None = None,
) -> dict[str, Any]:
    """
    Replay classification for one review_queue item. Returns summary dict.

    Raises ValueError when resource_code is not in review_queue.
    """
    from agents.classification.tools import parse_classification_json
    from agents.pipeline.deterministic import MODEL_FLASH_LITE, _judge_with_retry
    from agents.shared.schema import ClassificationResult

    if db is None:
        from google.cloud import firestore

        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
        db = firestore.Client(project=project)

    matches = list(
        db.collection("review_queue").where("resource_code", "==", resource_code).stream()
    )
    if not matches:
        raise ValueError(f"resource_code {resource_code!r} not found in review_queue")

    doc = matches[0]
    queue_data = doc.to_dict() or {}
    draft = dict(queue_data.get("draft_record") or {})
    if not draft.get("resource_code"):
        draft["resource_code"] = resource_code

    title = draft.get("title") or ""
    url = draft.get("url") or ""
    orig_type = draft.get("resource_type_code") or queue_data.get("resource_type") or "article"
    metadata = draft.get("type_fields") or {}

    resource_input = {
        "title": title,
        "url": url,
        "resource_type": orig_type,
        "doi": draft.get("doi") or metadata.get("doi"),
        "pmid": metadata.get("pmid"),
        "resource_code": resource_code,
    }

    cls_prompt = _build_classification_prompt(orig_type)
    cls_raw = _judge_with_retry(
        cls_prompt,
        {"resource": resource_input, "metadata": metadata, "type_hint": orig_type},
        MODEL_FLASH_LITE,
    )
    classification = parse_classification_json(cls_raw) if cls_raw else None
    if classification is None:
        classification = ClassificationResult(
            resource_type_code=orig_type,
            relevance_score=0.5,
            classification_confidence=0.5,
            access_type=draft.get("access_type") or "free",
        )

    cls_dump = classification.model_dump()
    patch = {k: cls_dump[k] for k in _CLASSIFICATION_FIELDS if k in cls_dump}
    updated_draft = {**draft, **patch}

    result = {
        "resource_code": resource_code,
        "queue_id": doc.id,
        "dry_run": dry_run,
        "classification": cls_dump,
        "patch": patch,
    }

    if dry_run:
        logger.info("dry-run: would update %s with %s", resource_code, patch)
        return result

    doc.reference.update({"draft_record": updated_draft})
    draft_ref = db.collection("draft_records").document(resource_code)
    if draft_ref.get().exists:
        draft_ref.update(patch)

    state_ref = db.collection("pipeline_state").document(resource_code)
    if state_ref.get().exists:
        state_ref.update({
            "classification_result": cls_dump,
            "classified_at": _now(),
            "current_stage": "classification",
        })

    logger.info("Updated classification for %s", resource_code)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay classification for one review_queue item")
    parser.add_argument("resource_code", help="resource_code to refine")
    parser.add_argument("--dry-run", action="store_true", help="Print patch without writing")
    args = parser.parse_args()

    try:
        result = refine_classification_for_resource(args.resource_code, dry_run=args.dry_run)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
