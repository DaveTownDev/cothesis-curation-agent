"""Canonical controlled vocabulary lists for the curation pipeline."""

RESOURCE_TYPES = frozenset({
    "article", "book", "book_chapter", "video", "podcast", "software",
    "reporting_guideline", "course", "web_guide", "template",
    "visual_reference", "dataset", "community", "funding",
})

LEGACY_METHODOLOGY_PREFIXES = frozenset({"RS-", "OD-", "EI-", "QI-"})

STAGE_CODES = frozenset({"TH", "HI", "EV", "ST", "IN", "SH"})

ACCESS_TYPES = frozenset({"free", "freemium", "paid", "subscription", "institutional", "open_access"})

DIFFICULTY_LEVELS = frozenset({"beginner", "intermediate", "advanced"})

CANONICAL_BADGES = frozenset({
    "editors_choice", "best_free", "best_beginners",
    "best_time_poor", "essential", "expert_pick",
})

# LLM badge normalization — maps common LLM variations to canonical codes
BADGE_NORMALIZATION: dict[str, str] = {
    # Case/spacing variants of canonical names
    "editors choice": "editors_choice",
    "editor's choice": "editors_choice",
    "editors_choice": "editors_choice",
    "best free": "best_free",
    "best free option": "best_free",
    "best for beginners": "best_beginners",
    "best beginners": "best_beginners",
    "best_beginners": "best_beginners",
    "best time poor": "best_time_poor",
    "best for time poor": "best_time_poor",
    "best_time_poor": "best_time_poor",
    "essential": "essential",
    "essential reference": "essential",
    "must have": "essential",
    "must-have": "essential",
    "expert pick": "expert_pick",
    "expert_pick": "expert_pick",
    "expert choice": "expert_pick",
}


def normalize_badge(raw: str) -> str | None:
    """Map a raw LLM badge string to its canonical code. Returns None if unrecognised."""
    key = raw.lower().strip()
    if key in BADGE_NORMALIZATION:
        return BADGE_NORMALIZATION[key]
    # Try exact match against canonical set
    if key in CANONICAL_BADGES:
        return key
    return None

# Research jargon terms banned from editorial_description_plain
PLAIN_JARGON_TERMS = [
    "systematic review",
    "scoping review",
    "retrospective",
    "observational",
    "risk-of-bias",
    "risk of bias",
    "reporting guideline",
    "meta-analysis",
    "meta analysis",
    "randomised controlled trial",
    "randomized controlled trial",
    "rct",
    "prisma",
    "strobe",
    "consort",
    "cohort study",
    "case-control",
    "cross-sectional",
    "clinical audit",
    "chart review",
    "qualitative research",
    "quantitative research",
    "grounded theory",
    "thematic analysis",
    "mixed methods",
    "grey literature",
    "heterogeneity",
    "confounders",
    "inter-rater reliability",
]


# ---------------------------------------------------------------------------
# Methodology grounding — injected into classification so the LLM disambiguates
# the 4 MVP methodologies instead of force-fitting (audit 2026-06-06: 40/60
# methodology codes were wrong without this). Source: data/methodologies/*.md.
# ---------------------------------------------------------------------------

METHODOLOGY_GUIDE = """The four MVP methodology codes and how to tell them apart. Assign the SINGLE
best-matching code, or [] if the resource genuinely matches none — do NOT force-fit.

- SYN-01 Narrative Systematic Review: a systematic literature search synthesised
  in WORDS (narrative), not statistics. Use when studies are too heterogeneous to
  pool. NOT a scoping review (that maps gaps), NOT a meta-analysis (statistical pooling).
- SYN-02 Scoping Review: maps the breadth of evidence/concepts/gaps in a field with
  broad inclusion and NO formal quality appraisal. If the title/abstract says
  "scoping review" it is SYN-02 (never SYN-01).
- OBS-01 Retrospective Chart Review: an OBSERVATIONAL study extracting data from
  existing medical records/EHR/registries to answer a question. If the title says
  "retrospective chart review", "chart review", or "review of records/EHR" it is
  OBS-01 (never EVAL-01).
- EVAL-01 Standards-Based Clinical Audit: compares actual clinical practice against
  an explicit evidence-based STANDARD/guideline to find gaps ("what we do" vs "what
  we should do"). Only EVAL-01 if it measures practice against a defined standard.

Resources outside these four (cohort/case-control/RCT/meta-analysis/qualitative/
funding calls/data portals/general textbooks) → methodology_codes: [] (route to human)."""

# Deterministic resource_type -> primary content_format (canonical, no LLM)
CONTENT_FORMAT_MAP = {
    "article": "text",
    "book": "text",
    "book_chapter": "text",
    "reporting_guideline": "pdf",
    "template": "pdf",
    "web_guide": "text",
    "course": "interactive",
    "software": "interactive",
    "dataset": "data",
    "visual_reference": "infographic",
    "video": "video",
    "podcast": "audio",
    "community": "interactive",
    "funding": "text",
}


def content_format_for(resource_type_code: str) -> str:
    """Deterministic content_format from the resource type."""
    return CONTENT_FORMAT_MAP.get(resource_type_code, "mixed")


def time_to_consume_for(resource_type_code: str, type_fields: dict | None = None) -> str:
    """
    Rough consumption-time estimate. Uses enrichment signals when present
    (article/book page_count), else a sensible per-type default.
    """
    tf = type_fields or {}
    pages = tf.get("page_count")
    if resource_type_code in ("book", "book_chapter"):
        if isinstance(pages, int) and pages > 0:
            hours = max(1, round(pages / 50))  # ~50 dense pages/hour
            return f"~{hours} hour{'s' if hours != 1 else ''}"
        return "several hours" if resource_type_code == "book" else "~30–60 min"
    if resource_type_code in ("article", "reporting_guideline"):
        return "~20–40 min"
    if resource_type_code in ("video", "podcast"):
        return "~10–60 min"
    if resource_type_code in ("course",):
        return "several hours"
    if resource_type_code in ("software", "dataset", "template", "community", "funding", "web_guide", "visual_reference"):
        return "varies"
    return "varies"
