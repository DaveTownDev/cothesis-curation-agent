"""Editorial agent tools — output parsing and jargon validation."""
from __future__ import annotations

import logging
from typing import Any

from agents.shared.schema import EditorialOutput
from agents.shared.codes import PLAIN_JARGON_TERMS

logger = logging.getLogger(__name__)


def check_plain_for_jargon(text: str) -> list[str]:
    """
    Check editorial_description_plain for banned research jargon.
    Returns a list of violation strings (empty = clean).
    """
    lower = text.lower()
    return [term for term in PLAIN_JARGON_TERMS if term in lower]


def parse_editorial_json(raw: Any, resource_code: str = "") -> EditorialOutput:
    """
    Parse and validate the Editorial agent's JSON output.
    Raises ValidationError on invalid badges / difficulty.
    Logs jargon warnings but does not block — the QC panel catches violations.
    """
    if not isinstance(raw, dict):
        raise ValueError(f"Editorial output is not a dict: {type(raw)}")

    output = EditorialOutput(**raw)

    violations = check_plain_for_jargon(output.editorial_description_plain)
    if violations:
        logger.warning(
            "Jargon detected in plain field for %r: %s",
            resource_code, violations,
        )
    return output
