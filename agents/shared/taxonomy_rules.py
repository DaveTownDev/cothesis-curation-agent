"""Type-aware taxonomy rules — shared by pipeline, arbiter, audit, and publish checklist."""
from __future__ import annotations

from agents.shared.codes import RESOURCE_TYPES
from agents.taxonomy import (
    is_valid_methodology_code,
    is_valid_skill_code,
    is_valid_subtype_code,
    normalize_methodology_code,
    normalize_skill_code,
    normalize_subtype_code,
    subtype_type_for,
)

# Types where empty methodology_codes is valid (tools, portals, grants, reference assets).
METHODOLOGY_OPTIONAL_TYPES = frozenset({
    "software",
    "community",
    "funding",
    "dataset",
    "template",
    "visual_reference",
})


def methodology_required_for_type(resource_type_code: str | None) -> bool:
    """Return True when at least one platform methodology code is expected for this type."""
    if not resource_type_code:
        return True
    if resource_type_code not in RESOURCE_TYPES:
        return True
    return resource_type_code not in METHODOLOGY_OPTIONAL_TYPES


def validate_taxonomy_draft(dr: dict) -> list[dict]:
    """Return issue dicts {sev, field, msg} for one draft_record."""
    issues: list[dict] = []

    def warn(field: str, msg: str) -> None:
        issues.append({"sev": "warn", "field": field, "msg": msg})

    def fail(field: str, msg: str) -> None:
        issues.append({"sev": "fail", "field": field, "msg": msg})

    rt = dr.get("resource_type_code")
    if rt and rt not in RESOURCE_TYPES:
        fail("resource_type_code", f"unknown type: {rt}")

    sub = dr.get("resource_subtype_code")
    if sub is not None and sub != "":
        norm_sub = normalize_subtype_code(sub)
        if not is_valid_subtype_code(norm_sub):
            fail("resource_subtype_code", f"unknown subtype: {sub}")
        elif rt and subtype_type_for(norm_sub) != rt:
            fail(
                "resource_subtype_code",
                f"subtype {norm_sub} parent type {subtype_type_for(norm_sub)!r} != {rt!r}",
            )
    elif rt == "book_chapter" and sub is None:
        pass
    elif rt and rt != "book_chapter" and not sub:
        warn("resource_subtype_code", "missing subtype for non-book_chapter type")

    mc = dr.get("methodology_codes") or []
    for code in mc:
        norm = normalize_methodology_code(code)
        if not is_valid_methodology_code(norm):
            fail("methodology_codes", f"unknown platform code: {code}")
    if methodology_required_for_type(rt) and not mc:
        warn("methodology_codes", "empty but required for this resource type")

    skills = dr.get("skill_codes") or []
    for code in skills:
        norm = normalize_skill_code(code)
        if not is_valid_skill_code(norm):
            fail("skill_codes", f"unknown foundation skill: {code}")

    return issues
