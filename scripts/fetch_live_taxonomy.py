#!/usr/bin/env python3
"""Fetch methodology, specialty, and resource-subtype taxonomies from the live Compendium site.

Reads sitemap.xml for slugs, scrapes display names from page titles.
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
TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.IGNORECASE)

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


def fetch_taxonomy(base_url: str) -> tuple[dict, dict, dict]:
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
    return meth_doc, spec_doc, subtype_doc


def main() -> int:
    base = os.environ.get("COMPENDIUM_BASE_URL", DEFAULT_BASE)
    meth_doc, spec_doc, subtype_doc = fetch_taxonomy(base)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meth_path = OUT_DIR / "live_methodologies.json"
    spec_path = OUT_DIR / "live_specialties.json"
    subtype_path = OUT_DIR / "live_subtypes.json"
    meth_text = json.dumps(meth_doc, indent=2, ensure_ascii=False) + "\n"
    spec_text = json.dumps(spec_doc, indent=2, ensure_ascii=False) + "\n"
    subtype_text = json.dumps(subtype_doc, indent=2, ensure_ascii=False) + "\n"
    meth_path.write_text(meth_text)
    spec_path.write_text(spec_text)
    subtype_path.write_text(subtype_text)

    console_dir = ROOT / "console" / "lib" / "data" / "taxonomy"
    console_dir.mkdir(parents=True, exist_ok=True)
    (console_dir / "live_methodologies.json").write_text(meth_text)
    (console_dir / "live_specialties.json").write_text(spec_text)
    (console_dir / "live_subtypes.json").write_text(subtype_text)

    print(f"Wrote {meth_doc['count']} methodologies → {meth_path.relative_to(ROOT)}")
    print(f"Wrote {spec_doc['count']} specialties → {spec_path.relative_to(ROOT)}")
    print(f"Wrote {subtype_doc['count']} subtypes → {subtype_path.relative_to(ROOT)}")
    print(f"Copied JSON → {console_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
