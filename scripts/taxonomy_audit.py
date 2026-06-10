"""
Taxonomy audit — deterministic validation + optional gold-set scoring.

Reads review_queue draft_records from Firestore (or a JSON fixture), validates
taxonomy fields against live JSON + type-aware rules, and compares to
eval/taxonomy_gold.json when resource_code matches.

  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.taxonomy_audit
  .venv/bin/python -m scripts.taxonomy_audit --fixture /path/to/drafts.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "eval" / "taxonomy_gold.json"
OUT_DEFAULT = "/tmp/cothesis_taxonomy_audit.json"

from agents.shared.codes import RESOURCE_TYPES
from agents.shared.taxonomy_rules import methodology_required_for_type
from agents.taxonomy import (
    is_valid_methodology_code,
    is_valid_skill_code,
    is_valid_subtype_code,
    normalize_methodology_code,
    normalize_skill_code,
    normalize_subtype_code,
    subtype_type_for,
)


def load_gold_cases(path: Path = GOLD_PATH) -> dict[str, dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {c["resource_code"]: c.get("expected", {}) for c in doc.get("cases", [])}


def validate_taxonomy_draft(dr: dict) -> list[dict]:
    """Return issue dicts {sev, field, msg} for one draft_record."""
    issues: list[dict] = []

    def warn(field: str, msg: str) -> None:
        issues.append({"sev": "warn", "field": field, "msg": msg})

    def fail(field: str, msg: str) -> None:
        issues.append({"sev": "fail", "field": field, "msg": msg})

    rt = dr.get("resource_type_code")
    if rt and rt not in RESOURCE_TYPES:
        fail("resource_type_code", f"unknown type: {rt}")

    sub = dr.get("resource_subtype_code")
    if sub is not None and sub != "":
        norm_sub = normalize_subtype_code(sub)
        if not is_valid_subtype_code(norm_sub):
            fail("resource_subtype_code", f"unknown subtype: {sub}")
        elif rt and subtype_type_for(norm_sub) != rt:
            fail(
                "resource_subtype_code",
                f"subtype {norm_sub} parent type {subtype_type_for(norm_sub)!r} != {rt!r}",
            )
    elif rt == "book_chapter" and sub is None:
        pass
    elif rt and rt != "book_chapter" and not sub:
        warn("resource_subtype_code", "missing subtype for non-book_chapter type")

    mc = dr.get("methodology_codes") or []
    for code in mc:
        norm = normalize_methodology_code(code)
        if not is_valid_methodology_code(norm):
            fail("methodology_codes", f"unknown platform code: {code}")
    if methodology_required_for_type(rt) and not mc:
        warn("methodology_codes", "empty but required for this resource type")

    skills = dr.get("skill_codes") or []
    for code in skills:
        norm = normalize_skill_code(code)
        if not is_valid_skill_code(norm):
            fail("skill_codes", f"unknown foundation skill: {code}")

    return issues


def score_against_gold(dr: dict, gold_expected: dict) -> list[dict]:
    """Field-level mismatches vs hand-labeled expected block."""
    mismatches: list[dict] = []
    for field, expected in gold_expected.items():
        actual = dr.get(field)
        if field == "methodology_codes" or field == "skill_codes":
            exp_set = set(expected or [])
            act_set = set(actual or [])
            if exp_set != act_set:
                mismatches.append({
                    "field": field,
                    "expected": sorted(exp_set),
                    "actual": sorted(act_set),
                })
        elif actual != expected:
            mismatches.append({"field": field, "expected": expected, "actual": actual})
    return mismatches


def aggregate_by_type(records: list[dict]) -> dict:
    by_type: dict[str, dict] = defaultdict(lambda: {"n": 0, "warn": 0, "fail": 0, "empty_methodology": 0})
    for rec in records:
        t = rec.get("type") or "unknown"
        by_type[t]["n"] += 1
        by_type[t]["warn"] += sum(1 for i in rec["issues"] if i["sev"] == "warn")
        by_type[t]["fail"] += sum(1 for i in rec["issues"] if i["sev"] == "fail")
        dr = rec.get("draft") or {}
        if not (dr.get("methodology_codes") or []):
            by_type[t]["empty_methodology"] += 1
    return dict(by_type)


def audit_records_from_firestore(project: str) -> list[dict]:
    from google.cloud import firestore

    db = firestore.Client(project=project)
    items = []
    for doc in db.collection("review_queue").stream():
        d = doc.to_dict() or {}
        dr = d.get("draft_record") or {}
        items.append({
            "queue_id": doc.id,
            "resource_code": d.get("resource_code") or dr.get("resource_code"),
            "draft": dr,
        })
    return items


def run_audit(items: list[dict], gold: dict[str, dict]) -> dict:
    results = []
    for it in items:
        dr = it.get("draft") or it
        rc = it.get("resource_code") or dr.get("resource_code")
        issues = validate_taxonomy_draft(dr)
        gold_mismatch = []
        if rc and rc in gold:
            gold_mismatch = score_against_gold(dr, gold[rc])
        sev = "fail" if any(i["sev"] == "fail" for i in issues) else (
            "warn" if issues or gold_mismatch else "ok"
        )
        results.append({
            "resource_code": rc,
            "queue_id": it.get("queue_id"),
            "type": dr.get("resource_type_code"),
            "taxonomy": sev,
            "issues": issues,
            "gold_mismatch": gold_mismatch,
            "draft": dr,
        })

    agg = {
        "n": len(results),
        "taxonomy": dict(Counter(r["taxonomy"] for r in results)),
        "by_type": aggregate_by_type(results),
        "gold_matched": sum(1 for r in results if r["gold_mismatch"] == [] and r["resource_code"] in gold),
        "gold_cases": len(gold),
    }
    return {"aggregate": agg, "records": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Taxonomy audit over review_queue drafts")
    parser.add_argument("--fixture", type=Path, help="JSON list of {resource_code, draft} objects")
    parser.add_argument("--out", type=Path, default=Path(OUT_DEFAULT))
    args = parser.parse_args()

    gold = load_gold_cases()
    if args.fixture:
        items = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
        items = audit_records_from_firestore(os.environ["GOOGLE_CLOUD_PROJECT"])

    report = run_audit(items, gold)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))
    print(f"\nFull report -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
