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
