"""Type-aware taxonomy rules — shared by pipeline, arbiter, audit, and publish checklist."""
from __future__ import annotations

from agents.shared.codes import RESOURCE_TYPES

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
