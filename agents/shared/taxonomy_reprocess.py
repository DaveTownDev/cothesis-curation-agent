"""Normalize methodology_codes and discipline_codes on stored records."""
from __future__ import annotations

from agents.taxonomy import (
    is_valid_discipline_slug,
    is_valid_methodology_code,
    methodology_entries,
    normalize_discipline_slug,
    normalize_methodology_code,
)

LEGACY_METHODOLOGY_MAP: dict[str, str] = {
    "RS-01": "SYN-01",
    "RS-04": "SYN-02",
    "OD-01": "OBS-01",
    "OD-06": "EVAL-01",
}


def _slug_to_methodology_code() -> dict[str, str]:
    return {e["slug"]: e["code"] for e in methodology_entries()}


def reprocess_methodology_codes(codes: list[str] | None) -> list[str]:
    slug_map = _slug_to_methodology_code()
    out: list[str] = []
    seen: set[str] = set()
    for raw in codes or []:
        if not raw or not str(raw).strip():
            continue
        text = str(raw).strip()
        code = slug_map.get(text.lower(), normalize_methodology_code(text))
        code = LEGACY_METHODOLOGY_MAP.get(code, code)
        if not is_valid_methodology_code(code) or code in seen:
            continue
        seen.add(code)
        out.append(code)
    return out


def reprocess_discipline_codes(slugs: list[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in slugs or []:
        if not raw or not str(raw).strip():
            continue
        slug = normalize_discipline_slug(str(raw))
        if not is_valid_discipline_slug(slug) or slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    return out


def reprocess_record_fields(record: dict) -> dict:
    """Return patch dict with normalized taxonomy fields (only changed keys)."""
    patch: dict = {}
    new_meth = reprocess_methodology_codes(record.get("methodology_codes"))
    old_meth = list(record.get("methodology_codes") or [])
    if new_meth != old_meth:
        patch["methodology_codes"] = new_meth

    new_disc = reprocess_discipline_codes(record.get("discipline_codes"))
    old_disc = [normalize_discipline_slug(d) for d in (record.get("discipline_codes") or [])]
    if new_disc != old_disc:
        patch["discipline_codes"] = new_disc
    return patch
