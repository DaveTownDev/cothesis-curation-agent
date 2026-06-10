#!/usr/bin/env python3
"""Fetch methodology, specialty, subtype, and foundation-skill taxonomies from the live Compendium site.

Reads sitemap.xml for slugs, scrapes display names from page titles (skills use canonical names).
Writes versioned JSON to data/taxonomy/ (runtime source of truth for pipeline + console).

Usage:
    python -m scripts.fetch_live_taxonomy
    COMPENDIUM_BASE_URL=https://compendium-web-production.up.railway.app python -m scripts.fetch_live_taxonomy
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "taxonomy"
DEFAULT_BASE = "https://compendium-web-production.up.railway.app"

METH_RE = re.compile(r"library/methodology/([a-z0-9-]+)")
SPEC_RE = re.compile(r"library/specialty/([a-z0-9-]+)")
SUBTYPE_RE = re.compile(r"library/resources/([a-z0-9-]+)/([a-z0-9-]+)")
SKILL_RE = re.compile(r"library/skills/([a-z0-9-]+)")
TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.IGNORECASE)

# Canonical FS-01..FS-16 — slug join key from live sitemap; names from docs/TAXONOMY.md
CANONICAL_SKILLS: tuple[tuple[str, str, str], ...] = (
    ("FS-01", "project-management", "Project Management"),
    ("FS-02", "literature-searching", "Literature Searching"),
    ("FS-03", "literature-synthesis", "Literature Synthesis"),
    ("FS-04", "critical-appraisal", "Critical Appraisal"),
    ("FS-05", "research-ethics", "Research Ethics"),
    ("FS-06", "quantitative-methods", "Quantitative Methods"),
    ("FS-07", "qualitative-methods", "Qualitative Methods"),
    ("FS-08", "mixed-methods", "Mixed Methods"),
    ("FS-09", "statistical-literacy", "Statistical Literacy"),
    ("FS-10", "data-management", "Data Management"),
    ("FS-11", "research-software", "Research Software"),
    ("FS-12", "academic-writing", "Academic Writing"),
    ("FS-13", "research-presentation", "Research Presentation"),
    ("FS-14", "research-dissemination", "Research Dissemination"),
    ("FS-15", "supervision-and-mentoring", "Supervision & Mentoring"),
    ("FS-16", "grant-writing", "Grant Writing"),
)

# Sitemap type path segments → canonical resource_type_code
TYPE_SLUG_TO_CODE: dict[str, str] = {
    "reporting-guideline": "reporting_guideline",
    "web-guide": "web_guide",
    "visual-reference": "visual_reference",
    "book-chapter": "book_chapter",
}


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "cothesis-taxonomy-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _title_name(html: str) -> str:
    m = TITLE_RE.search(html)
    if not m:
        return ""
    return m.group(1).split("—")[0].split(" - ")[0].strip()


def _slug_to_code(slug: str) -> str:
    """Platform codes are uppercase slugs (syn-01 → SYN-01)."""
    return slug.upper()


def _type_slug_to_code(slug: str) -> str:
    return TYPE_SLUG_TO_CODE.get(slug, slug.replace("-", "_"))


def _subtype_slug_to_code(slug: str) -> str:
    return slug.replace("-", "_")


def fetch_taxonomy(base_url: str) -> tuple[dict, dict, dict, dict]:
    base = base_url.rstrip("/")
    sitemap = _fetch(f"{base}/sitemap.xml")
    meth_slugs = sorted(set(METH_RE.findall(sitemap)))
    spec_slugs = sorted(set(SPEC_RE.findall(sitemap)))

    methodologies = []
    for slug in meth_slugs:
        url = f"{base}/library/methodology/{slug}"
        try:
            html = _fetch(url)
            name = _title_name(html)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"warn: {slug}: {exc}", file=sys.stderr)
            name = slug.replace("-", " ").title()
        methodologies.append({
            "code": _slug_to_code(slug),
            "slug": slug,
            "name": name,
            "url": url,
        })

    specialties = []
    for slug in spec_slugs:
        url = f"{base}/library/specialty/{slug}"
        try:
            html = _fetch(url)
            name = _title_name(html)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"warn: {slug}: {exc}", file=sys.stderr)
            name = slug.replace("-", " ").title()
        specialties.append({
            "slug": slug,
            "name": name,
            "url": url,
        })

    subtype_pairs = sorted(set(SUBTYPE_RE.findall(sitemap)))
    subtypes = []
    for type_slug, subtype_slug in subtype_pairs:
        type_code = _type_slug_to_code(type_slug)
        code = _subtype_slug_to_code(subtype_slug)
        url = f"{base}/library/resources/{type_slug}/{subtype_slug}"
        try:
            html = _fetch(url)
            name = _title_name(html)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"warn: {type_slug}/{subtype_slug}: {exc}", file=sys.stderr)
            name = subtype_slug.replace("-", " ").title()
        subtypes.append({
            "code": code,
            "slug": subtype_slug,
            "type_code": type_code,
            "name": name,
            "url": url,
        })

    fetched_at = datetime.now(timezone.utc).isoformat()
    meth_doc = {
        "source": base,
        "fetched_at": fetched_at,
        "count": len(methodologies),
        "methodologies": methodologies,
    }
    spec_doc = {
        "source": base,
        "fetched_at": fetched_at,
        "count": len(specialties),
        "specialties": specialties,
    }
    subtype_doc = {
        "source": base,
        "fetched_at": fetched_at,
        "count": len(subtypes),
        "subtypes": subtypes,
    }

    sitemap_skill_slugs = set(SKILL_RE.findall(sitemap))
    canonical_by_slug = {slug: (code, name) for code, slug, name in CANONICAL_SKILLS}
    missing = sorted(canonical_by_slug.keys() - sitemap_skill_slugs)
    extra = sorted(sitemap_skill_slugs - canonical_by_slug.keys())
    if missing:
        print(f"warn: sitemap missing skill slugs: {missing}", file=sys.stderr)
    if extra:
        print(f"warn: sitemap has unknown skill slugs: {extra}", file=sys.stderr)

    skills = []
    for code, slug, name in CANONICAL_SKILLS:
        url = f"{base}/library/skills/{slug}"
        skills.append({
            "code": code,
            "slug": slug,
            "name": name,
            "url": url,
        })

    skill_doc = {
        "source": base,
        "fetched_at": fetched_at,
        "count": len(skills),
        "skills": skills,
    }
    return meth_doc, spec_doc, subtype_doc, skill_doc


def main() -> int:
    base = os.environ.get("COMPENDIUM_BASE_URL", DEFAULT_BASE)
    meth_doc, spec_doc, subtype_doc, skill_doc = fetch_taxonomy(base)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meth_path = OUT_DIR / "live_methodologies.json"
    spec_path = OUT_DIR / "live_specialties.json"
    subtype_path = OUT_DIR / "live_subtypes.json"
    skill_path = OUT_DIR / "live_skills.json"
    meth_text = json.dumps(meth_doc, indent=2, ensure_ascii=False) + "\n"
    spec_text = json.dumps(spec_doc, indent=2, ensure_ascii=False) + "\n"
    subtype_text = json.dumps(subtype_doc, indent=2, ensure_ascii=False) + "\n"
    skill_text = json.dumps(skill_doc, indent=2, ensure_ascii=False) + "\n"
    meth_path.write_text(meth_text)
    spec_path.write_text(spec_text)
    subtype_path.write_text(subtype_text)
    skill_path.write_text(skill_text)

    console_dir = ROOT / "console" / "lib" / "data" / "taxonomy"
    console_dir.mkdir(parents=True, exist_ok=True)
    (console_dir / "live_methodologies.json").write_text(meth_text)
    (console_dir / "live_specialties.json").write_text(spec_text)
    (console_dir / "live_subtypes.json").write_text(subtype_text)
    (console_dir / "live_skills.json").write_text(skill_text)

    print(f"Wrote {meth_doc['count']} methodologies → {meth_path.relative_to(ROOT)}")
    print(f"Wrote {spec_doc['count']} specialties → {spec_path.relative_to(ROOT)}")
    print(f"Wrote {subtype_doc['count']} subtypes → {subtype_path.relative_to(ROOT)}")
    print(f"Wrote {skill_doc['count']} foundation skills → {skill_path.relative_to(ROOT)}")
    print(f"Copied JSON → {console_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
