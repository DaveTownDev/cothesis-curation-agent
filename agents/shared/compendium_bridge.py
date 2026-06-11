"""
Bridge: agent Firestore `resources` record → Compendium ImportCandidate.

Maps approved pipeline output to vocabulary-native `tags[]` for POST /api/import/json.
Reference: docs/INGESTION_AGENT_HANDOVER.md
"""
from __future__ import annotations

import re
from typing import Any

from agents.shared.tag_vocabulary import (
    is_leaf_methodology_code,
    is_valid_methodology_leaf,
    normalize_methodology_code,
)

LEAF_METHODOLOGY_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{2}$")

_ACCESS_TYPE_MAP: dict[str, str] = {
    "open_access": "free",
    "free": "free",
    "freemium": "freemium",
    "paid": "paid",
    "subscription": "subscription",
    "institutional": "institutional",
}


def _default_confidence(resource: dict[str, Any]) -> float:
    raw = resource.get("classification_confidence")
    if isinstance(raw, (int, float)):
        return max(0.0, min(1.0, float(raw)))
    return 0.85


def _tag(taxonomy: str, code: str, confidence: float) -> dict[str, Any]:
    return {"taxonomy": taxonomy, "code": code, "confidence": confidence}


def draft_record_to_vocabulary_tags(resource: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Map draft_record taxonomy fields → vocabulary-native tags[] per handover §3.
    """
    conf = _default_confidence(resource)
    tags: list[dict[str, Any]] = []

    subtype = resource.get("resource_subtype_code")
    rtype = resource.get("resource_type_code")
    if rtype == "book_chapter":
        tags.append(_tag("resource_type", "chapter", conf))
    elif subtype:
        tags.append(_tag("resource_type", str(subtype), conf))
    elif rtype and rtype in {
        "article", "book", "video", "podcast", "software", "reporting_guideline",
        "course", "web_guide", "template", "visual_reference", "dataset",
        "community", "funding",
    }:
        # Broad type-only tag when no subtype — uncommon at push time
        pass

    for code in resource.get("methodology_codes") or []:
        norm = normalize_methodology_code(str(code))
        if is_valid_methodology_leaf(norm):
            tags.append(_tag("methodology", norm, conf))

    for code in resource.get("discipline_codes") or []:
        norm = str(code).strip().upper()
        if norm:
            tags.append(_tag("specialty", norm, conf))

    for code in resource.get("stage_codes") or []:
        norm = str(code).strip().upper()
        if norm:
            tags.append(_tag("thesis", norm, conf))

    for code in resource.get("skill_codes") or []:
        norm = str(code).strip().upper()
        if norm:
            tags.append(_tag("foundation_skill", norm, conf))

    for code in resource.get("domain_codes") or []:
        norm = str(code).strip().upper()
        if norm:
            tags.append(_tag("cross_specialty_domain", norm, conf))

    return tags


def has_trusted_path_methodology(resource: dict[str, Any]) -> bool:
    """Trusted upstream fast path requires ≥1 leaf methodology tag."""
    tags = draft_record_to_vocabulary_tags(resource)
    return any(
        t.get("taxonomy") == "methodology" and is_leaf_methodology_code(str(t.get("code", "")))
        for t in tags
    )


def to_compendium_record(resource: dict[str, Any]) -> dict[str, Any]:
    """
    Translate an approved Firestore `resources` record into a vocabulary-native
    ImportCandidate dict for POST /api/import/json.
    """
    out: dict[str, Any] = {
        "title": resource.get("title"),
        "url": resource.get("url"),
        "editorial_description": resource.get("editorial_description"),
        "source_tool": "claude",
        "tags": draft_record_to_vocabulary_tags(resource),
    }

    raw_access = resource.get("access_type", "free")
    out["access_type"] = _ACCESS_TYPE_MAP.get(raw_access, "free")

    for field in ("doi", "isbn", "pmid"):
        val = resource.get(field)
        out[field] = val if val else None

    plain = resource.get("editorial_description_plain")
    if plain:
        out["editorial_description_long"] = plain

    for field in ("authors", "publisher", "journal_name", "platform", "year", "language"):
        val = resource.get(field)
        if val:
            out[field] = val

    return out
