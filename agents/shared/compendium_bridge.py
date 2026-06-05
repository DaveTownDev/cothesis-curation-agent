"""
Bridge: agent Firestore `resources` record → Compendium ImportCandidate.

Maps approved pipeline output to the shape expected by POST /api/import/json.
This is the single place that knows about field-name differences between the
two systems. Nothing else should contain this mapping.

Reference: compendium-web/src/pipeline/types.ts — ImportCandidate interface.
"""
from __future__ import annotations

from typing import Any


# Agent access_type values that the Compendium doesn't have a 1:1 for
_ACCESS_TYPE_MAP: dict[str, str] = {
    "open_access": "free",  # OA is free; Compendium uses "free"
    "free": "free",
    "freemium": "freemium",
    "paid": "paid",
    "subscription": "subscription",
    "institutional": "institutional",
}

# Compendium valid access types (from types.ts AccessType)
_VALID_ACCESS_TYPES = frozenset({"free", "freemium", "paid", "subscription", "institutional"})


def to_compendium_record(resource: dict[str, Any]) -> dict[str, Any]:
    """
    Translate an approved Firestore `resources` record into a Compendium
    ImportCandidate dict for POST /api/import/json.

    Only includes fields present in the ImportCandidate interface.
    Internal pipeline fields (quality_score, stage_codes, etc.) are dropped.
    """
    out: dict[str, Any] = {}

    # --- Required fields ---
    out["title"] = resource.get("title")
    out["url"] = resource.get("url")
    out["resource_type"] = resource.get("resource_type_code")
    out["description"] = resource.get("editorial_description")
    out["source_tool"] = "claude"

    # --- Optional direct mappings ---
    if subtype := resource.get("resource_subtype_code"):
        out["subtype"] = subtype
    else:
        out["subtype"] = None

    out["methodology_tags"] = resource.get("methodology_codes") or []

    # Access type — normalise open_access → free
    raw_access = resource.get("access_type", "free")
    out["access_type"] = _ACCESS_TYPE_MAP.get(raw_access, "free")

    # --- Identifiers ---
    for field in ("doi", "isbn", "pmid"):
        val = resource.get(field)
        if val:
            out[field] = val
        else:
            out[field] = None

    # --- Plain description → discovery_context ---
    plain = resource.get("editorial_description_plain")
    out["discovery_context"] = plain if plain else None

    # --- Optional enrichment metadata ---
    for field in ("authors", "publisher", "journal_name", "platform", "year", "language"):
        val = resource.get(field)
        if val:
            out[field] = val

    return out
