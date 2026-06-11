"""
Source-accuracy audit — compare review_queue draft_records against live sources.

Produces /tmp/cothesis_source_accuracy.json for scripts.write_qa_audit to merge
into review_queue.qa_audit (source_verdict, type_match, methodology_plausible, …).

Deterministic heuristics only (no LLM). Re-run after batch processing or before
QA triage; pair with scripts.audit_records then scripts.write_qa_audit.

  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.source_accuracy_audit
  .venv/bin/python -m scripts.source_accuracy_audit --fixture /path/to/queue.json --out /tmp/out.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from agents.shared.source_check import verify_source
from agents.shared.taxonomy_rules import methodology_required_for_type

OUT_DEFAULT = "/tmp/cothesis_source_accuracy.json"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CoThesis-curation/1.0)"}
_SNIPPET_LEN = 4000

# URL/title hints for coarse type sanity (not exhaustive).
_TYPE_URL_HINTS: dict[str, list[str]] = {
    "software": ["github.com", "gitlab", "pypi.org", "cran.r-project.org", "covidence", "zotero"],
    "dataset": ["figshare", "zenodo.org/record", "dryad", "dataverse", "mimic"],
    "video": ["youtube.com", "vimeo.com", "youtu.be"],
    "funding": ["grants.gov", "nih.gov/grants", "wellcome.org/grant"],
    "community": ["forum", "discourse", "slack.com", "listserv"],
}
_TYPE_TITLE_HINTS: dict[str, list[str]] = {
    "article": ["journal", "doi:", "pmid", "abstract", "randomized", "cohort"],
    "book": ["edition", "isbn", "handbook", "textbook"],
    "reporting_guideline": ["guideline", "statement", "checklist", "prisma", "consort"],
}


def _title_tokens(title: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{4,}", (title or "").lower())}


def _fetch_snippet(url: str | None, timeout: int = 12) -> tuple[str, str | None]:
    """Return (snippet_text, error). Empty snippet on failure."""
    if not url:
        return "", "no url"
    try:
        with httpx.Client(
            follow_redirects=True, timeout=timeout, headers=_HEADERS,
        ) as client:
            resp = client.get(url)
            if resp.status_code >= 400:
                return "", f"http {resp.status_code}"
            text = resp.text[:_SNIPPET_LEN].lower()
            return text, None
    except httpx.HTTPError as exc:
        return "", str(exc)[:120]


def _check_type_match(dr: dict, snippet: str, src: dict) -> str:
    """Return yes | no | uncertain."""
    rt = dr.get("resource_type_code") or ""
    url = (dr.get("url") or "").lower()
    title = (dr.get("title") or "").lower()
    combined = f"{url} {title} {snippet}"

    if src.get("status") == "dead":
        return "uncertain"
    if src.get("status") in ("blocked", "unknown") and not snippet:
        return "uncertain"

    for hint in _TYPE_URL_HINTS.get(rt, []):
        if hint in combined:
            return "yes"
    for hint in _TYPE_TITLE_HINTS.get(rt, []):
        if hint in combined:
            return "yes"

    # Obvious mismatches
    if rt == "article" and any(h in combined for h in ("github.com", "pypi.org")):
        return "no"
    if rt == "software" and "journal." in combined and "github" not in combined:
        return "no"

    if snippet or src.get("status") == "live":
        return "uncertain"
    return "uncertain"


def _check_methodology_plausible(dr: dict) -> str:
    rt = dr.get("resource_type_code")
    mc = dr.get("methodology_codes") or []
    if not methodology_required_for_type(rt):
        return "n/a"
    if mc:
        return "yes"
    return "no"


def _check_description_accurate(dr: dict, snippet: str) -> tuple[str, list[str]]:
    """Return (verdict, hallucinations[])."""
    title = dr.get("title") or ""
    tokens = _title_tokens(title)
    if len(tokens) < 2:
        return "uncertain", []

    editorial = " ".join(
        str(dr.get(f) or "")
        for f in ("editorial_description", "summary", "editorial_description_plain")
    ).lower()

    if not editorial.strip():
        return "no", ["No editorial copy to compare against source"]

    overlap = sum(1 for t in tokens if t in editorial or (snippet and t in snippet))
    ratio = overlap / len(tokens)

    hallucinations: list[str] = []
    if ratio >= 0.5:
        return "yes", hallucinations
    if ratio >= 0.25:
        return "minor", hallucinations

    hallucinations.append(
        f"Editorial copy shares few title tokens with source ({overlap}/{len(tokens)})"
    )
    return "no", hallucinations


def audit_draft_record(dr: dict) -> dict[str, Any]:
    """Build one source-accuracy row for write_qa_audit."""
    rc = dr.get("resource_code") or ""
    url = dr.get("url")
    doi = dr.get("doi") or (dr.get("type_fields") or {}).get("doi")

    src = verify_source(url, doi)
    fetchable = "yes" if src.get("resolved") else "no"
    snippet, fetch_err = _fetch_snippet(src.get("final_url") or url)
    if fetch_err and src.get("status") != "dead":
        fetchable = "uncertain"

    type_match = _check_type_match(dr, snippet, src)
    methodology_plausible = _check_methodology_plausible(dr)
    description_accurate, hallucinations = _check_description_accurate(dr, snippet)

    source_issues: list[str] = []
    if src.get("status") == "dead":
        source_issues.append(f"Source unreachable ({src.get('code') or src.get('err', 'dead')})")
    if type_match == "no":
        source_issues.append(f"resource_type_code {dr.get('resource_type_code')!r} mismatches URL/title hints")
    if methodology_plausible == "no":
        source_issues.append("methodology_codes empty but required for this type")
    if description_accurate == "no":
        source_issues.append("description not grounded in source title/snippet")

    # Aggregate verdict
    hard_fail = (
        src.get("status") == "dead"
        or type_match == "no"
        or methodology_plausible == "no"
        or description_accurate == "no"
    )
    soft_warn = (
        type_match == "uncertain"
        or fetchable == "uncertain"
        or description_accurate == "minor"
        or methodology_plausible == "n/a"
    )
    if hard_fail:
        source_verdict = "fail"
    elif soft_warn:
        source_verdict = "warn"
    else:
        source_verdict = "pass"

    notes_parts = []
    if src.get("status"):
        notes_parts.append(f"source_status={src['status']}")
    if fetch_err:
        notes_parts.append(f"fetch={fetch_err}")

    return {
        "resource_code": rc,
        "source_verdict": source_verdict,
        "fetchable": fetchable,
        "type_match": type_match,
        "methodology_plausible": methodology_plausible,
        "description_accurate": description_accurate,
        "source_issues": source_issues,
        "hallucinations": hallucinations,
        "source_notes": "; ".join(notes_parts) if notes_parts else None,
    }


def load_queue_items_from_firestore(project: str) -> list[dict]:
    from google.cloud import firestore

    db = firestore.Client(project=project)
    items = []
    for doc in db.collection("review_queue").stream():
        d = doc.to_dict() or {}
        dr = d.get("draft_record") or {}
        if not dr.get("resource_code"):
            dr = {**dr, "resource_code": d.get("resource_code")}
        items.append({"queue_id": doc.id, "draft_record": dr})
    return items


def run_audit(items: list[dict]) -> list[dict]:
    rows = []
    for it in items:
        dr = it.get("draft_record") or it.get("draft") or it
        row = audit_draft_record(dr)
        if it.get("queue_id"):
            row["queue_id"] = it["queue_id"]
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Source-accuracy audit over review_queue drafts")
    parser.add_argument("--fixture", type=Path, help="JSON list of {resource_code, draft_record}")
    parser.add_argument("--out", type=Path, default=Path(OUT_DEFAULT))
    args = parser.parse_args()

    if args.fixture:
        items = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        project = os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
        items = load_queue_items_from_firestore(project)

    rows = run_audit(items)
    args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    verdicts = Counter(r["source_verdict"] for r in rows)
    print(f"Audited {len(rows)} records -> {args.out}")
    print("Verdicts:", dict(verdicts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
