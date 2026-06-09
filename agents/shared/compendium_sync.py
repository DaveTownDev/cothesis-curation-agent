"""
Compendium import response parsing and public URL construction.

Shared by scripts/sync.py (scheduler) and documented for console parity in
console/lib/compendium-sync.ts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResourceSyncOutcome:
    compendium_id: str | None
    compendium_url: str | None


@dataclass(frozen=True)
class ImportBatchResult:
    import_batch_id: str
    outcomes: list[ResourceSyncOutcome]


def _first_str(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def extract_resource_id(item: dict[str, Any]) -> str | None:
    return _first_str(item, "resource_id", "compendium_id", "resourceId", "id")


def _subtype_path_segment(subtype: str | None, resource_type: str | None) -> str:
    if subtype:
        return subtype.replace("_", "-")
    if resource_type:
        return resource_type.replace("_", "-")
    return "resources"


def build_compendium_public_url(
    base_url: str,
    *,
    resource_id: str | None = None,
    slug: str | None = None,
    subtype_slug: str | None = None,
    resource_type_code: str | None = None,
) -> str | None:
    """Construct a Compendium library URL when the import API omits one."""
    root = base_url.rstrip("/")
    if resource_id:
        return f"{root}/library/resources/{resource_id}"
    if slug:
        segment = _subtype_path_segment(subtype_slug, resource_type_code)
        return f"{root}/library/{segment}/{slug}"
    return None


def extract_public_url(
    item: dict[str, Any],
    base_url: str,
    record: dict[str, Any],
) -> str | None:
    for key in ("compendium_url", "public_url", "page_url", "library_url", "url"):
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        trimmed = value.strip()
        if trimmed.startswith("http://") or trimmed.startswith("https://"):
            return trimmed
        if trimmed.startswith("/"):
            return f"{base_url.rstrip('/')}{trimmed}"

    resource_id = extract_resource_id(item)
    slug = _first_str(item, "slug", "code")
    subtype = _first_str(item, "subtype_slug", "subtype") or record.get("resource_subtype_code")
    resource_type = record.get("resource_type_code")
    return build_compendium_public_url(
        base_url,
        resource_id=resource_id,
        slug=slug,
        subtype_slug=str(subtype) if subtype else None,
        resource_type_code=str(resource_type) if resource_type else None,
    )


def _resource_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("resources", "accepted", "accepted_resources", "results", "imported"):
        raw = response.get(key)
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
    return []


def parse_import_response(
    response: dict[str, Any],
    records: list[dict[str, Any]],
    base_url: str,
) -> ImportBatchResult:
    """
    Map POST /api/import/json response to per-record id + public URL.

    When the API returns only import_batch_id (no per-resource array), outcomes
    are empty placeholders — callers still mark compendium_synced_at.
    """
    batch_id = str(response.get("import_batch_id") or response.get("batch_id") or "")
    items = _resource_items(response)

    outcomes: list[ResourceSyncOutcome] = []
    if items:
        for index, record in enumerate(records):
            item = items[index] if index < len(items) else {}
            outcomes.append(
                ResourceSyncOutcome(
                    compendium_id=extract_resource_id(item),
                    compendium_url=extract_public_url(item, base_url, record),
                )
            )
    else:
        outcomes = [ResourceSyncOutcome(None, None) for _ in records]

    return ImportBatchResult(import_batch_id=batch_id, outcomes=outcomes)


def title_to_slug(title: str) -> str:
    """Fallback slug when API returns resource_id but not slug (rare)."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:120] or "resource"
