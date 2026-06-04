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
