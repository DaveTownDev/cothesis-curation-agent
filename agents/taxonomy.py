"""Live Compendium taxonomy loader — data/taxonomy/*.json is runtime source of truth."""
from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODOLOGIES_PATH = ROOT / "data" / "taxonomy" / "live_methodologies.json"
SPECIALTIES_PATH = ROOT / "data" / "taxonomy" / "live_specialties.json"
SUBTYPES_PATH = ROOT / "data" / "taxonomy" / "live_subtypes.json"
SKILLS_PATH = ROOT / "data" / "taxonomy" / "live_skills.json"

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
def _load_subtype_doc() -> dict:
    with SUBTYPES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_skill_doc() -> dict:
    with SKILLS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def methodology_entries() -> tuple[dict, ...]:
    return tuple(_load_methodology_doc().get("methodologies", []))


@lru_cache(maxsize=1)
def specialty_entries() -> tuple[dict, ...]:
    return tuple(_load_specialty_doc().get("specialties", []))


@lru_cache(maxsize=1)
def subtype_entries() -> tuple[dict, ...]:
    return tuple(_load_subtype_doc().get("subtypes", []))


@lru_cache(maxsize=1)
def skill_entries() -> tuple[dict, ...]:
    return tuple(_load_skill_doc().get("skills", []))


@lru_cache(maxsize=1)
def methodology_codes() -> frozenset[str]:
    return frozenset(e["code"] for e in methodology_entries())


@lru_cache(maxsize=1)
def specialty_slugs() -> frozenset[str]:
    return frozenset(e["slug"] for e in specialty_entries())


@lru_cache(maxsize=1)
def subtype_codes() -> frozenset[str]:
    return frozenset(e["code"] for e in subtype_entries())


@lru_cache(maxsize=1)
def skill_codes() -> frozenset[str]:
    return frozenset(e["code"] for e in skill_entries())


@lru_cache(maxsize=1)
def subtype_code_to_type() -> dict[str, str]:
    return {e["code"]: e["type_code"] for e in subtype_entries()}


@lru_cache(maxsize=1)
def methodology_code_to_name() -> dict[str, str]:
    return {e["code"]: e["name"] for e in methodology_entries()}


@lru_cache(maxsize=1)
def specialty_slug_to_name() -> dict[str, str]:
    return {e["slug"]: html.unescape(e["name"]) for e in specialty_entries()}


@lru_cache(maxsize=1)
def subtype_code_to_name() -> dict[str, str]:
    return {e["code"]: html.unescape(e["name"]) for e in subtype_entries()}


@lru_cache(maxsize=1)
def skill_code_to_name() -> dict[str, str]:
    return {e["code"]: html.unescape(e["name"]) for e in skill_entries()}


def normalize_methodology_code(code: str) -> str:
    """Platform codes are uppercase (SYN-01). Slugs from the site are lowercase."""
    return code.strip().upper()


def normalize_discipline_slug(slug: str) -> str:
    return slug.strip().lower()


def is_valid_methodology_code(code: str) -> bool:
    return normalize_methodology_code(code) in methodology_codes()


def is_valid_discipline_slug(slug: str) -> bool:
    return normalize_discipline_slug(slug) in specialty_slugs()


def normalize_subtype_code(code: str) -> str:
    return code.strip().lower().replace("-", "_")


def is_valid_subtype_code(code: str) -> bool:
    return normalize_subtype_code(code) in subtype_codes()


def subtype_type_for(code: str) -> str | None:
    return subtype_code_to_type().get(normalize_subtype_code(code))


def normalize_skill_code(code: str) -> str:
    raw = code.strip().upper()
    if raw.startswith("FS-"):
        num = raw[3:].lstrip("0") or "0"
        if num.isdigit():
            return f"FS-{int(num):02d}"
    return raw


def is_valid_skill_code(code: str) -> bool:
    return normalize_skill_code(code) in skill_codes()


def subtypes_for_type(type_code: str) -> tuple[dict, ...]:
    return tuple(e for e in subtype_entries() if e["type_code"] == type_code)


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


SKILL_RULE = (
    "Foundation Skills (skill_codes): assign ONLY when the resource *teaches* the skill "
    "(not merely uses it). Use [] when none apply."
)


def build_skill_guide() -> str:
    """Compact foundation-skill code list for classification prompts."""
    lines = [SKILL_RULE, "", "Allowed foundation skill codes (choose from this list only):"]
    for entry in skill_entries():
        lines.append(f"- {entry['code']}: {entry['name']}")
    return "\n".join(lines)


def build_subtype_guide() -> str:
    """Compact subtype code list grouped by resource type for classification prompts."""
    from agents.shared.codes import RESOURCE_TYPES

    lines = [
        "Allowed resource_subtype_code values (globally unique snake_case codes).",
        "Set null for book_chapter (no subtypes). For all other types, pick the best match.",
        "",
    ]
    for type_code in sorted(RESOURCE_TYPES):
        if type_code == "book_chapter":
            lines.append(f"## {type_code}: (no subtypes — use null)")
            continue
        entries = subtypes_for_type(type_code)
        lines.append(f"## {type_code}:")
        for entry in entries:
            name = html.unescape(entry["name"])
            lines.append(f"- {entry['code']}: {name}")
    return "\n".join(lines)
