"""Mirror of console/lib/qa-recommendations.ts — QA quick-action heuristics for CI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TypedDict


class QaRecommendation(TypedDict, total=False):
    id: str
    type: str
    label: str
    description: str
    resource_type_code: str
    suggested_url: str
    requeue_stage: str
    requeue_note: str
    reject_reason: str


KNOWN_RESOURCE_TYPES = {
    "article",
    "book",
    "book_chapter",
    "video",
    "podcast",
    "software",
    "reporting_guideline",
    "course",
    "web_guide",
    "template",
    "visual_reference",
    "dataset",
    "community",
    "funding",
}

RESOURCE_TYPE_IN_TEXT = re.compile(
    r"resource[_\s-]*type\s*[=:]\s*([a-z][a-z0-9_]*)", re.I
)
TYPE_SUGGESTION_HINT = re.compile(
    r"reasonable match|should be|recommend(?:ed)?|better (?:fit|match)|correct type|instead of",
    re.I,
)
DEAD_LINK_HINT = re.compile(
    r"\b404\b|broken provided url|dead link|does not resolve|unverified source|fabricated|url_status[=:\s]*dead",
    re.I,
)
CANONICAL_HINT = re.compile(
    r"canonical(?:\s+(?:url|link|doi))?[^.]{0,80}(?:fetched successfully|found|resolved|reachable|works)",
    re.I,
)
URL_IN_TEXT = re.compile(r"https?://[^\s\])\"'<>]+", re.I)
DOI_IN_TEXT = re.compile(r"\b10\.\d{4,9}/[^\s\])\"'<>]+", re.I)


def normalize_url(raw: str) -> str:
    trimmed = raw.rstrip(".,;")
    if trimmed.startswith("10."):
        return f"https://doi.org/{trimmed}"
    return trimmed


def extract_suggested_resource_types(text: str) -> list[str]:
    found: list[str] = []
    for match in RESOURCE_TYPE_IN_TEXT.finditer(text):
        code = match.group(1).lower()
        if code in KNOWN_RESOURCE_TYPES and code not in found:
            found.append(code)
    return found


def extract_urls(text: str) -> list[str]:
    urls = [normalize_url(u) for u in URL_IN_TEXT.findall(text)]
    dois = [normalize_url(d) for d in DOI_IN_TEXT.findall(text)]
    combined: list[str] = []
    for u in urls + dois:
        if u not in combined:
            combined.append(u)
    return combined


def collect_text(qa: dict[str, Any], item_reason: str | None = None) -> str:
    parts = [
        qa.get("source_notes"),
        qa.get("type_match"),
        qa.get("url_status"),
        qa.get("fetchable"),
        *(qa.get("source_issues") or []),
        *(qa.get("hallucinations") or []),
        *(qa.get("dq_issues") or []),
        item_reason,
    ]
    return "\n".join(str(p) for p in parts if p)


def parse_qa_recommendations(
    qa: dict[str, Any] | None,
    item_reason: str | None = None,
    current_type: str | None = None,
    current_url: str | None = None,
) -> list[QaRecommendation]:
    if not qa:
        return []

    text = collect_text(qa, item_reason)
    recs: list[QaRecommendation] = []
    seen: set[str] = set()

    type_mismatch = (
        str(qa.get("type_match", "")).lower() == "no"
        or re.search(r"\btype_match[=:\s]*no\b", text, re.I)
        or re.search(r"wrong resource_type", text, re.I)
    )
    for code in extract_suggested_resource_types(text):
        if code == current_type:
            continue
        if not (TYPE_SUGGESTION_HINT.search(text) or type_mismatch) and qa.get("source_verdict") != "fail":
            continue
        rec_id = f"change_type:{code}"
        if rec_id in seen:
            continue
        seen.add(rec_id)
        recs.append(
            {
                "id": rec_id,
                "type": "change_type",
                "label": f"Change type → {code.replace('_', ' ')}",
                "resource_type_code": code,
            }
        )

    if type_mismatch and not extract_suggested_resource_types(text) and qa.get("source_verdict") != "pass":
        rec_id = "requeue:classification:type"
        if rec_id not in seen:
            seen.add(rec_id)
            recs.append(
                {
                    "id": rec_id,
                    "type": "requeue",
                    "label": "Re-send for classification",
                    "requeue_stage": "classification",
                }
            )

    deadish = (
        bool(DEAD_LINK_HINT.search(text))
        or str(qa.get("url_status", "")).lower() == "dead"
        or qa.get("url_code") == 404
    )
    if deadish:
        urls = extract_urls(text)
        suggested = next((u for u in urls if u != current_url), urls[0] if urls else None)
        has_canonical = bool(CANONICAL_HINT.search(text)) or bool(suggested)
        if not has_canonical and not suggested:
            rec_id = "requeue:classification:url"
            if rec_id not in seen:
                seen.add(rec_id)
                recs.append(
                    {
                        "id": rec_id,
                        "type": "requeue",
                        "label": "Re-send — fix URL in pipeline",
                        "requeue_stage": "classification",
                    }
                )
        else:
            rec_id = f"fix_url:{suggested or 'manual'}"
            if rec_id not in seen:
                seen.add(rec_id)
                recs.append(
                    {
                        "id": rec_id,
                        "type": "fix_url",
                        "label": "Fix URL & re-send",
                        "suggested_url": suggested,
                        "requeue_stage": "classification",
                    }
                )

    hallucinations = qa.get("hallucinations") or []
    if hallucinations:
        rec_id = "reject:hallucination"
        if rec_id not in seen:
            seen.add(rec_id)
            sample = "; ".join(hallucinations[:2])
            recs.append(
                {
                    "id": rec_id,
                    "type": "reject_preset",
                    "label": "Reject — hallucinated content",
                    "reject_reason": f"Hallucinated content: {sample}",
                }
            )

    if qa.get("source_verdict") == "fail" and (
        DEAD_LINK_HINT.search(text) or re.search(r"fabricated", text, re.I)
    ):
        rec_id = "reject:dead_source"
        if rec_id not in seen:
            seen.add(rec_id)
            recs.append(
                {
                    "id": rec_id,
                    "type": "reject_preset",
                    "label": "Reject — dead / fabricated source",
                    "reject_reason": "Source URL or DOI is dead, unverifiable, or fabricated (QA audit)",
                }
            )

    return recs


def test_change_type_from_source_notes():
    qa = {
        "source_verdict": "warn",
        "type_match": "no",
        "source_notes": "resource_type=reporting_guideline is a reasonable match; tagged as article",
    }
    recs = parse_qa_recommendations(qa, current_type="article")
    assert any(r["type"] == "change_type" and r["resource_type_code"] == "reporting_guideline" for r in recs)


def test_fix_url_with_canonical():
    qa = {
        "source_verdict": "fail",
        "url_status": "dead",
        "url_code": 404,
        "source_notes": (
            "broken provided URL returned 404; canonical https://doi.org/10.1000/example "
            "fetched successfully"
        ),
    }
    recs = parse_qa_recommendations(
        qa,
        current_url="https://example.com/broken",
    )
    fix = next(r for r in recs if r["type"] == "fix_url")
    assert fix["suggested_url"] == "https://doi.org/10.1000/example"
    assert fix["requeue_stage"] == "classification"


def test_reject_hallucination():
    qa = {
        "source_verdict": "fail",
        "hallucinations": ["Claims RCT design not stated in source"],
    }
    recs = parse_qa_recommendations(qa)
    assert any(r["type"] == "reject_preset" and "Hallucinated" in r["reject_reason"] for r in recs)


def test_requeue_when_type_mismatch_without_code():
    qa = {"source_verdict": "warn", "type_match": "no", "source_notes": "wrong resource_type"}
    recs = parse_qa_recommendations(qa)
    assert any(r["type"] == "requeue" and r["requeue_stage"] == "classification" for r in recs)


def test_empty_without_qa():
    assert parse_qa_recommendations(None) == []


def test_ts_source_exists():
    assert (Path(__file__).resolve().parents[1] / "console/lib/qa-recommendations.ts").is_file()
