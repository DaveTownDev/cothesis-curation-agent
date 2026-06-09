"""
Publish checklist — validates a draft record before it can be set to `published`.

From docs/SCHEMA.md:
  editorial_description present
  ≥1 methodology_code (platform)
  quality_score present and ≥ 60
  url present (link verified)
  human-ratified (editorial_reviewed_by + editorial_reviewed_at)

Returns a list of error strings; empty list = passes.
"""
from __future__ import annotations

from agents.shared.codes import LEGACY_METHODOLOGY_PREFIXES
from agents.taxonomy import is_valid_methodology_code, normalize_methodology_code


def validate_publish_checklist(record: dict) -> list[str]:
    """
    Validate a draft record against the publish checklist.
    Returns a list of violation strings. Empty = publishable.
    """
    errors: list[str] = []

    # 1. editorial_description present
    if not record.get("editorial_description", "").strip():
        errors.append("editorial_description is missing or empty")

    # 2. ≥1 platform methodology_code
    codes = record.get("methodology_codes", [])
    if not codes:
        errors.append("methodology_codes: ≥1 platform code required (SYN-/OBS-/EVAL-…)")
    else:
        for code in codes:
            for legacy in LEGACY_METHODOLOGY_PREFIXES:
                if code.startswith(legacy):
                    errors.append(
                        f"Legacy methodology code {code!r} (prefix {legacy!r}) in "
                        f"methodology_codes — emit platform codes only"
                    )
            norm = normalize_methodology_code(code)
            if not is_valid_methodology_code(norm):
                errors.append(
                    f"methodology_codes: unknown platform code {code!r} "
                    f"(not in live Compendium taxonomy)"
                )

    # 3. quality_score present and ≥ 60
    quality_score = record.get("quality_score")
    if quality_score is None:
        errors.append("quality_score is missing")
    elif quality_score < 60:
        errors.append(
            f"quality_score={quality_score} is below 60 — "
            "records scoring below 60 are not publishable (hidden on card)"
        )

    # 4. url present (link verified)
    if not record.get("url", "").strip():
        errors.append("url is missing — link must be verified before publishing")

    # 5. Human ratification: editorial_reviewed_by + editorial_reviewed_at
    if not record.get("editorial_reviewed_by"):
        errors.append(
            "editorial_reviewed_by is missing — record must be human-ratified before publishing"
        )
    if not record.get("editorial_reviewed_at"):
        errors.append(
            "editorial_reviewed_at is missing — record must be human-ratified before publishing"
        )

    return errors
