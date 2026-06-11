"""Live Compendium taxonomy loader — vocabulary is validation authority; live scrape for on-site badges."""
from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

from agents.shared import tag_vocabulary

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
    return tag_vocabulary.methodology_leaf_codes()


@lru_cache(maxsize=1)
def specialty_slugs() -> frozenset[str]:
    return frozenset(e["slug"] for e in specialty_entries())


@lru_cache(maxsize=1)
def subtype_codes() -> frozenset[str]:
    return tag_vocabulary.subtype_codes()


@lru_cache(maxsize=1)
def skill_codes() -> frozenset[str]:
    return tag_vocabulary.skill_codes()


@lru_cache(maxsize=1)
def subtype_code_to_type() -> dict[str, str]:
    return tag_vocabulary.subtype_parent_map()


@lru_cache(maxsize=1)
def methodology_code_to_name() -> dict[str, str]:
    nodes = tag_vocabulary._nodes_by_taxonomy_level()["methodology"]
    return {code: html.unescape(str(n.get("name", ""))) for code, n in nodes.items()}


@lru_cache(maxsize=1)
def specialty_slug_to_name() -> dict[str, str]:
    return {e["slug"]: html.unescape(e["name"]) for e in specialty_entries()}


@lru_cache(maxsize=1)
def subtype_code_to_name() -> dict[str, str]:
    nodes = tag_vocabulary._nodes_by_taxonomy_level()["resource_type"]
    return {
        code: html.unescape(str(n.get("name", "")))
        for code, n in nodes.items()
        if n.get("level") == "subtype"
    }


@lru_cache(maxsize=1)
def skill_code_to_name() -> dict[str, str]:
    nodes = tag_vocabulary._nodes_by_taxonomy_level()["foundation_skill"]
    return {code: html.unescape(str(n.get("name", ""))) for code, n in nodes.items()}


def normalize_methodology_code(code: str) -> str:
    return tag_vocabulary.normalize_methodology_code(code)


def normalize_discipline_slug(slug: str) -> str:
    """Legacy name — normalizes to canonical specialty code for storage."""
    code = tag_vocabulary.normalize_specialty_code(slug)
    return code if code else slug.strip().lower()


def is_valid_methodology_code(code: str) -> bool:
    return tag_vocabulary.is_valid_methodology_leaf(code)


def is_valid_discipline_slug(slug: str) -> bool:
    return tag_vocabulary.is_valid_specialty_code(slug)


def is_valid_specialty(code: str) -> bool:
    return tag_vocabulary.is_valid_specialty_code(code)


def normalize_subtype_code(code: str) -> str:
    return tag_vocabulary.normalize_subtype_code(code)


def is_valid_subtype_code(code: str) -> bool:
    return tag_vocabulary.is_valid_subtype_code(code)


def subtype_type_for(code: str) -> str | None:
    return tag_vocabulary.subtype_parent(code)


def normalize_skill_code(code: str) -> str:
    return tag_vocabulary.normalize_skill_code(code)


def is_valid_skill_code(code: str) -> bool:
    return tag_vocabulary.is_valid_skill_code(code)


def subtypes_for_type(type_code: str) -> tuple[dict, ...]:
    parent = type_code.strip().lower()
    nodes = tag_vocabulary._taxonomy_nodes()["resource_type"]
    return tuple(
        {"code": n["code"], "name": n.get("name", ""), "type_code": n.get("parent")}
        for n in nodes
        if n.get("level") == "subtype" and n.get("parent") == parent
    )


def build_methodology_guide() -> str:
    return tag_vocabulary.build_methodology_guide()


def build_discipline_guide() -> str:
    return tag_vocabulary.build_specialty_guide()


SKILL_RULE = (
    "Foundation Skills (skill_codes): assign ONLY when the resource *teaches* the skill "
    "(not merely uses it). Use [] when none apply."
)


def build_skill_guide() -> str:
    return tag_vocabulary.build_skill_guide()


def build_subtype_guide() -> str:
    return tag_vocabulary.build_subtype_guide()


def build_classification_vocabulary_guide() -> str:
    return tag_vocabulary.build_classification_vocabulary_guide()
