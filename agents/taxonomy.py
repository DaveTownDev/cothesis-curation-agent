"""Live Compendium taxonomy loader — data/taxonomy/*.json is runtime source of truth."""
from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODOLOGIES_PATH = ROOT / "data" / "taxonomy" / "live_methodologies.json"
SPECIALTIES_PATH = ROOT / "data" / "taxonomy" / "live_specialties.json"

# Grounding cards in data/methodologies/*.md — still used by VertexAiSearchTool
MVP_METHODOLOGY_CODES = frozenset({"SYN-01", "SYN-02", "OBS-01", "EVAL-01"})

MVP_DISAMBIGUATION = """Core methodology disambiguation (assign the SINGLE best match, or [] if none):

- SYN-01 Narrative Systematic Review: systematic literature search synthesised in WORDS (narrative), not statistics.
- SYN-02 Scoping Review: maps breadth of evidence/concepts/gaps; broad inclusion, NO formal quality appraisal.
- OBS-01 Retrospective Chart Review: observational study extracting data from existing medical records/EHR/registries.
- EVAL-01 Standards-Based Clinical Audit: compares clinical practice against an explicit evidence-based standard/guideline.

When a resource clearly matches another platform code from the allowed list below, use that code.
Use [] only when no methodology applies (e.g. generic textbooks, funding calls, data portals)."""


@lru_cache(maxsize=1)
def _load_methodology_doc() -> dict:
    with METHODOLOGIES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_specialty_doc() -> dict:
    with SPECIALTIES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def methodology_entries() -> tuple[dict, ...]:
    return tuple(_load_methodology_doc().get("methodologies", []))


@lru_cache(maxsize=1)
def specialty_entries() -> tuple[dict, ...]:
    return tuple(_load_specialty_doc().get("specialties", []))


@lru_cache(maxsize=1)
def methodology_codes() -> frozenset[str]:
    return frozenset(e["code"] for e in methodology_entries())


@lru_cache(maxsize=1)
def specialty_slugs() -> frozenset[str]:
    return frozenset(e["slug"] for e in specialty_entries())


@lru_cache(maxsize=1)
def methodology_code_to_name() -> dict[str, str]:
    return {e["code"]: e["name"] for e in methodology_entries()}


@lru_cache(maxsize=1)
def specialty_slug_to_name() -> dict[str, str]:
    return {e["slug"]: html.unescape(e["name"]) for e in specialty_entries()}


def normalize_methodology_code(code: str) -> str:
    """Platform codes are uppercase (SYN-01). Slugs from the site are lowercase."""
    return code.strip().upper()


def normalize_discipline_slug(slug: str) -> str:
    return slug.strip().lower()


def is_valid_methodology_code(code: str) -> bool:
    return normalize_methodology_code(code) in methodology_codes()


def is_valid_discipline_slug(slug: str) -> bool:
    return normalize_discipline_slug(slug) in specialty_slugs()


def build_methodology_guide() -> str:
    """Compact allowed-code list + MVP disambiguation for classification prompts."""
    lines = [MVP_DISAMBIGUATION, "", "Allowed platform methodology codes (choose from this list only):"]
    for entry in methodology_entries():
        lines.append(f"- {entry['code']}: {entry['name']}")
    return "\n".join(lines)


def build_discipline_guide() -> str:
    """Compact specialty slug list for classification prompts."""
    lines = ["Allowed discipline_codes (specialty slugs, max 3; omit if broadly applicable):"]
    for entry in specialty_entries():
        name = html.unescape(entry["name"])
        lines.append(f"- {entry['slug']}: {name}")
    return "\n".join(lines)
