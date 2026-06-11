"""Canonical tag vocabulary loader — sole code authority for classification and push."""
from __future__ import annotations

import html
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_PATH = ROOT / "data" / "taxonomy" / "tag_vocabulary.json"
DEMO_RETAG_PATH = ROOT / "data" / "taxonomy" / "demo_resources_retagged.json"

TAXONOMY_KEYS = (
    "resource_type",
    "methodology",
    "specialty",
    "thesis",
    "cross_specialty_domain",
    "foundation_skill",
)

LEAF_METHODOLOGY_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{2}$")
_MATCH_TERM_CAP = 8


@lru_cache(maxsize=1)
def _load_doc() -> dict[str, Any]:
    with VOCABULARY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _taxonomy_nodes() -> dict[str, tuple[dict[str, Any], ...]]:
    taxonomies = _load_doc().get("taxonomies", {})
    return {
        key: tuple(taxonomies.get(key, {}).get("nodes", []))
        for key in TAXONOMY_KEYS
    }


@lru_cache(maxsize=1)
def _nodes_by_taxonomy_level() -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for tax, nodes in _taxonomy_nodes().items():
        by_code: dict[str, dict[str, Any]] = {}
        for node in nodes:
            by_code[node["code"]] = node
        out[tax] = by_code
    return out


def valid_codes(taxonomy: str) -> frozenset[str]:
    """All codes defined for a taxonomy key."""
    return frozenset(_nodes_by_taxonomy_level().get(taxonomy, {}).keys())


@lru_cache(maxsize=1)
def methodology_leaf_codes() -> frozenset[str]:
    return frozenset(
        n["code"]
        for n in _taxonomy_nodes()["methodology"]
        if n.get("level") == "methodology"
    )


@lru_cache(maxsize=1)
def specialty_codes() -> frozenset[str]:
    return frozenset(
        n["code"]
        for n in _taxonomy_nodes()["specialty"]
        if n.get("level") == "specialty"
    )


@lru_cache(maxsize=1)
def thesis_codes() -> frozenset[str]:
    return frozenset(n["code"] for n in _taxonomy_nodes()["thesis"])


@lru_cache(maxsize=1)
def subtype_codes() -> frozenset[str]:
    return frozenset(
        n["code"]
        for n in _taxonomy_nodes()["resource_type"]
        if n.get("level") == "subtype"
    )


@lru_cache(maxsize=1)
def resource_type_codes() -> frozenset[str]:
    return frozenset(
        n["code"]
        for n in _taxonomy_nodes()["resource_type"]
        if n.get("level") == "type"
    )


@lru_cache(maxsize=1)
def skill_codes() -> frozenset[str]:
    return frozenset(n["code"] for n in _taxonomy_nodes()["foundation_skill"])


@lru_cache(maxsize=1)
def domain_codes() -> frozenset[str]:
    return frozenset(n["code"] for n in _taxonomy_nodes()["cross_specialty_domain"])


@lru_cache(maxsize=1)
def specialty_code_to_slug_map() -> dict[str, str]:
    return {
        n["code"]: n["slug"]
        for n in _taxonomy_nodes()["specialty"]
        if n.get("level") == "specialty" and n.get("slug")
    }


@lru_cache(maxsize=1)
def specialty_slug_to_code_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for code, slug in specialty_code_to_slug_map().items():
        out[slug.lower()] = code
    return out


@lru_cache(maxsize=1)
def subtype_parent_map() -> dict[str, str]:
    return {
        n["code"]: n["parent"]
        for n in _taxonomy_nodes()["resource_type"]
        if n.get("level") == "subtype" and n.get("parent")
    }


def specialty_code_to_slug(code: str) -> str | None:
    return specialty_code_to_slug_map().get(code.strip().upper())


def specialty_slug_to_code(slug: str) -> str | None:
    return specialty_slug_to_code_map().get(slug.strip().lower())


def subtype_parent(code: str) -> str | None:
    norm = code.strip().lower().replace("-", "_")
    return subtype_parent_map().get(norm)


def normalize_specialty_code(value: str) -> str | None:
    """Map slug or code to canonical specialty code (e.g. cardiology → CARDIO)."""
    raw = value.strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper in specialty_codes():
        return upper
    slug_code = specialty_slug_to_code(raw)
    if slug_code:
        return slug_code
    return None


def is_valid_methodology_leaf(code: str) -> bool:
    return normalize_methodology_code(code) in methodology_leaf_codes()


def normalize_methodology_code(code: str) -> str:
    return code.strip().upper()


def is_valid_specialty_code(code: str) -> bool:
    return normalize_specialty_code(code) is not None


def is_valid_subtype_code(code: str) -> bool:
    norm = code.strip().lower().replace("-", "_")
    return norm in subtype_codes()


def is_valid_thesis_code(code: str) -> bool:
    return code.strip().upper() in thesis_codes()


def is_valid_skill_code(code: str) -> bool:
    return normalize_skill_code(code) in skill_codes()


def is_valid_domain_code(code: str) -> bool:
    return code.strip().upper() in domain_codes()


def normalize_skill_code(code: str) -> str:
    raw = code.strip().upper()
    if raw.startswith("FS-"):
        num = raw[3:].lstrip("0") or "0"
        if num.isdigit():
            return f"FS-{int(num):02d}"
    return raw


def normalize_subtype_code(code: str) -> str:
    return code.strip().lower().replace("-", "_")


def is_leaf_methodology_code(code: str) -> bool:
    """Trusted upstream fast path — leaf pattern per handover §3."""
    return bool(LEAF_METHODOLOGY_PATTERN.match(normalize_methodology_code(code)))


def _cap_terms(terms: list[str]) -> list[str]:
    return terms[:_MATCH_TERM_CAP]


def _node_match_terms(node: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for key in ("synonyms", "search_terms", "child_terms"):
        for term in node.get(key) or []:
            if term and term not in terms:
                terms.append(str(term))
    name = node.get("name")
    if name and name not in terms:
        terms.append(str(name))
    code = node.get("code")
    if code and code not in terms:
        terms.append(str(code))
    return _cap_terms(terms)


def _format_node_line(taxonomy: str, node: dict[str, Any]) -> str:
    code = node["code"]
    name = html.unescape(str(node.get("name", "")))
    terms = _node_match_terms(node)
    extra = ""
    if taxonomy == "thesis":
        bits: list[str] = []
        if node.get("deliverables"):
            bits.append(f"deliverables: {node['deliverables']}")
        if node.get("search_terms"):
            bits.append(f"search: {', '.join(_cap_terms(list(node['search_terms'])))}")
        if bits:
            extra = f" ({'; '.join(bits)})"
    elif terms:
        extra = f" [match: {', '.join(terms)}]"
    return f"- {code}: {name}{extra}"


def _section_header(taxonomy: str) -> tuple[str, str]:
    doc = _load_doc()["taxonomies"][taxonomy]
    title = taxonomy.replace("_", " ").title()
    when = doc.get("when_to_use", "")
    return title, when


def build_methodology_guide() -> str:
    lines = [_section_header("methodology")[1], "", "Allowed methodology codes (leaf only):"]
    for node in _taxonomy_nodes()["methodology"]:
        if node.get("level") == "methodology":
            lines.append(_format_node_line("methodology", node))
    return "\n".join(lines)


def build_specialty_guide() -> str:
    lines = [
        "Allowed specialty codes (max 3; omit if broadly applicable; domain≠specialty):",
        "",
    ]
    for node in _taxonomy_nodes()["specialty"]:
        if node.get("level") == "specialty":
            slug = node.get("slug", "")
            lines.append(_format_node_line("specialty", node) + (f" (slug: {slug})" if slug else ""))
    return "\n".join(lines)


def build_subtype_guide() -> str:
    lines = [
        "Allowed resource_subtype_code values (vocabulary subtypes).",
        "For book chapters use resource_type_code book + subtype chapter.",
        "Legacy book_chapter type is accepted short-term — maps to chapter at push.",
        "",
    ]
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for node in _taxonomy_nodes()["resource_type"]:
        if node.get("level") == "subtype":
            by_parent.setdefault(node.get("parent") or "?", []).append(node)
    for parent in sorted(by_parent):
        lines.append(f"## {parent}:")
        for node in sorted(by_parent[parent], key=lambda n: n["code"]):
            lines.append(_format_node_line("resource_type", node))
    return "\n".join(lines)


def build_thesis_guide() -> str:
    lines = [
        "Allowed stage_codes — phases (TH, HI, EV, ST, IN, SH) and stages (e.g. IN-02, EV-03).",
        "Tag finest stage when confident; use phase only when resource spans a whole phase.",
        "Match on deliverables and search_terms, not canonical stage names.",
        "",
    ]
    for node in _taxonomy_nodes()["thesis"]:
        lines.append(_format_node_line("thesis", node))
    return "\n".join(lines)


def build_skill_guide() -> str:
    lines = [
        "Foundation skills (skill_codes): assign ONLY when the resource *teaches* the skill.",
        "",
        "Allowed foundation skill codes:",
    ]
    for node in _taxonomy_nodes()["foundation_skill"]:
        lines.append(_format_node_line("foundation_skill", node))
    return "\n".join(lines)


def build_domain_guide() -> str:
    lines = [
        "Cross-specialty domains (domain_codes): optional; tag when genuinely cross-cutting.",
        "Do not confuse informatics/health-economics domains with clinical specialties.",
        "",
    ]
    for node in _taxonomy_nodes()["cross_specialty_domain"]:
        lines.append(_format_node_line("cross_specialty_domain", node))
    return "\n".join(lines)


def build_classification_vocabulary_guide() -> str:
    """Single injected block for classification prompts."""
    meta = _load_doc().get("_meta", {})
    rules = meta.get("tagging_rules", {})
    parts = [
        "## Canonical tagging rules",
        str(meta.get("purpose", "")),
        f"- Tag at: {rules.get('tag_at', 'finest confident level')}",
        f"- Rollup: {rules.get('rollup', 'up-only')}",
        f"- Multi-tag: {rules.get('multi_tag', 'allowed across taxonomies')}",
        "",
        "## Methodology",
        build_methodology_guide(),
        "",
        "## Specialty",
        build_specialty_guide(),
        "",
        "## Resource subtypes",
        build_subtype_guide(),
        "",
        "## Thesis phases and stages",
        build_thesis_guide(),
        "",
        "## Foundation skills",
        build_skill_guide(),
        "",
        "## Cross-specialty domains",
        build_domain_guide(),
    ]
    return "\n".join(parts)


@lru_cache(maxsize=1)
def match_terms_index() -> dict[str, tuple[str, str]]:
    """Lowercase match term → (taxonomy, code). First registration wins."""
    index: dict[str, tuple[str, str]] = {}
    for taxonomy, nodes in _taxonomy_nodes().items():
        for node in nodes:
            code = node["code"]
            for term in _node_match_terms(node):
                key = term.strip().lower()
                if key and key not in index:
                    index[key] = (taxonomy, code)
    return index


def resolve_match_term(term: str) -> tuple[str, str] | None:
    return match_terms_index().get(term.strip().lower())


@lru_cache(maxsize=1)
def demo_retag_resources() -> tuple[dict[str, Any], ...]:
    with DEMO_RETAG_PATH.open(encoding="utf-8") as f:
        doc = json.load(f)
    return tuple(doc.get("resources", []))


def demo_retag_by_id(resource_id: str) -> dict[str, Any] | None:
    for item in demo_retag_resources():
        if item.get("resource_id") == resource_id:
            return item
    return None
