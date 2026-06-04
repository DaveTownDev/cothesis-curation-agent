"""Classification agent tools — JSON parsing + code validation."""
from __future__ import annotations

import logging
from typing import Any

from agents.shared.schema import ClassificationResult

logger = logging.getLogger(__name__)


def parse_classification_json(raw: Any) -> ClassificationResult | None:
    """
    Parse and validate the LLM's classification JSON.
    Returns None as a retry signal when input is unparseable.
    Raises ValidationError when codes violate the canonical schema.
    """
    if not isinstance(raw, dict):
        logger.warning("Classification output is not a dict — retry signal")
        return None
    try:
        return ClassificationResult(**raw)
    except (TypeError, KeyError) as exc:
        logger.warning("Classification parse error (retry): %s", exc)
        return None
    # ValidationError propagates — caller routes to review_needed
