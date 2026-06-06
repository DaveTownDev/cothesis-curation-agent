"""
Read-only data-quality + URL-liveness audit over the processed records.

Pulls every review_queue doc, scores its embedded draft_record against the
canonical schema/vocab, tests the URL, and emits a per-record scorecard + an
aggregate summary to /tmp/cothesis_audit.json.

  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.audit_records
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

import httpx

from agents.shared.codes import (
    RESOURCE_TYPES, STAGE_CODES, ACCESS_TYPES, DIFFICULTY_LEVELS,
    CANONICAL_BADGES, PLAIN_JARGON_TERMS,
)

PLATFORM_CODE = re.compile(r"^(SYN|OBS|EVAL)-\d{2}$")
OUT = "/tmp/cothesis_audit.json"


def audit_record(dr: dict) -> dict:
    """Return {issues:[{sev,field,msg}], dq: ok|warn|fail} for one draft_record."""
    issues = []

    def warn(field, msg): issues.append({"sev": "warn", "field": field, "msg": msg})
    def fail(field, msg): issues.append({"sev": "fail", "field": field, "msg": msg})

    # Required / completeness
    for f in ("resource_code", "title", "url", "resource_type_code", "editorial_description"):
        if not dr.get(f):
            fail(f, "missing/empty (publish-blocking)")
    if not dr.get("summary"):
        warn("summary", "missing long description")
    if not dr.get("editorial_description_plain"):
        warn("editorial_description_plain", "missing plain-language layer")

    # Known-unpopulated canonical fields (completeness gaps)
    if not dr.get("type_fields"):
        warn("type_fields", "empty — no type-specific metadata")
    if not dr.get("discipline_codes"):
        warn("discipline_codes", "empty")
    for f in ("time_to_consume", "content_format"):
        if not dr.get(f):
            warn(f, "not populated by pipeline")

    # Validity — ranges
    qs = dr.get("quality_score")
    if qs is None or not (0 <= qs <= 100):
        fail("quality_score", f"out of [0,100]: {qs}")
    for f in ("relevance_score", "classification_confidence"):
        v = dr.get(f)
        if v is not None and not (0 <= v <= 1):
            fail(f, f"out of [0,1]: {v}")

    # Validity — controlled vocab
    rt = dr.get("resource_type_code")
    if rt and rt not in RESOURCE_TYPES:
        fail("resource_type_code", f"not a valid type: {rt}")
    mc = dr.get("methodology_codes") or []
    bad_mc = [c for c in mc if not PLATFORM_CODE.match(c)]
    if bad_mc:
        fail("methodology_codes", f"non-platform codes: {bad_mc}")
    if not mc:
        warn("methodology_codes", "no methodology codes")
    bad_badges = [b for b in (dr.get("proposed_badges") or []) if b not in CANONICAL_BADGES]
    if bad_badges:
        fail("proposed_badges", f"non-canonical: {bad_badges}")
    bad_stage = [s for s in (dr.get("stage_codes") or []) if s not in STAGE_CODES]
    if bad_stage:
        fail("stage_codes", f"invalid THESIS codes: {bad_stage}")
    dl = dr.get("difficulty_level")
    if dl and dl not in DIFFICULTY_LEVELS:
        warn("difficulty_level", f"unexpected: {dl}")
    at = dr.get("access_type")
    if at and at not in ACCESS_TYPES:
        warn("access_type", f"unexpected: {at}")

    # Editorial sanity
    ed = dr.get("editorial_description") or ""
    if ed and len(ed) < 30:
        warn("editorial_description", f"suspiciously short ({len(ed)} chars)")
    plain = (dr.get("editorial_description_plain") or "").lower()
    jargon = [t for t in PLAIN_JARGON_TERMS if t in plain]
    if jargon:
        warn("editorial_description_plain", f"contains jargon: {jargon[:5]}")

    sev = "fail" if any(i["sev"] == "fail" for i in issues) else ("warn" if issues else "ok")
    return {"dq": sev, "issues": issues}


def test_url(url: str) -> dict:
    if not url:
        return {"url_status": "missing", "code": None, "final": None}
    try:
        with httpx.Client(follow_redirects=True, timeout=12,
                          headers={"User-Agent": "Mozilla/5.0 CoThesis-audit/1.0"}) as c:
            r = c.get(url)
            code = r.status_code
            ctype = r.headers.get("content-type", "")
            body = r.text[:4000].lower() if "html" in ctype else ""
            paywall = any(k in body for k in ["sign in to read", "purchase access", "get access",
                                              "subscribe to", "institutional login", "paywall"])
            status = ("live" if code < 400 else "dead")
            if code < 400 and paywall:
                status = "paywalled"
            return {"url_status": status, "code": code, "final": str(r.url), "ctype": ctype[:40]}
    except Exception as e:
        return {"url_status": "unreachable", "code": None, "final": None, "err": str(e)[:80]}


def main() -> int:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    from google.cloud import firestore
    db = firestore.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])

    items = []
    for doc in db.collection("review_queue").stream():
        d = doc.to_dict()
        items.append({"queue_id": doc.id, "data": d})

    results = []
    for it in items:
        d = it["data"]
        dr = d.get("draft_record") or {}
        rec = {
            "queue_id": it["queue_id"],
            "resource_code": d.get("resource_code"),
            "title": (dr.get("title") or "")[:70],
            "type": dr.get("resource_type_code"),
            "routing": d.get("routing"),
            "quality_score": dr.get("quality_score"),
        }
        rec.update(audit_record(dr))
        rec.update(test_url(dr.get("url")))
        results.append(rec)
        flags = ",".join(f"{i['sev']}:{i['field']}" for i in rec["issues"]) or "-"
        print(f"{rec['dq']:>4} | {rec['url_status']:>11} | {str(rec['type'])[:12]:12} | {rec['title'][:42]:42} | {flags[:60]}")

    # Aggregate
    agg = {
        "n": len(results),
        "dq": dict(Counter(r["dq"] for r in results)),
        "url_status": dict(Counter(r["url_status"] for r in results)),
        "fail_fields": dict(Counter(i["field"] for r in results for i in r["issues"] if i["sev"] == "fail")),
        "warn_fields": dict(Counter(i["field"] for r in results for i in r["issues"] if i["sev"] == "warn")),
        "resource_code_dupes": {k: v for k, v in Counter(r["resource_code"] for r in results).items() if v > 1},
    }
    json.dump({"aggregate": agg, "records": results}, open(OUT, "w"), indent=2)
    print("\n=== AGGREGATE ===")
    print(json.dumps(agg, indent=2))
    print(f"\nFull scorecard -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
