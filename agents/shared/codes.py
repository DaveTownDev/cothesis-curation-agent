"""Canonical controlled vocabulary lists for the curation pipeline."""

RESOURCE_TYPES = frozenset({
    "article", "book", "book_chapter", "video", "podcast", "software",
    "reporting_guideline", "course", "web_guide", "template",
    "visual_reference", "dataset", "community", "funding",
})

LEGACY_METHODOLOGY_PREFIXES = frozenset({"RS-", "OD-", "EI-", "QI-"})

# Common LLM aliases → canonical resource_type_code. The interactive (adk web)
# classifier occasionally emits these free-text variants; map them rather than
# discarding the whole classification on a Pydantic enum failure.
RESOURCE_TYPE_ALIASES = {
    "guideline": "reporting_guideline", "guidelines": "reporting_guideline",
    "reporting guideline": "reporting_guideline", "checklist": "reporting_guideline",
    "standard": "reporting_guideline", "reporting_standard": "reporting_guideline",
    "methodological_article": "article", "methods_article": "article",
    "research_article": "article", "journal_article": "article", "review": "article",
    "review_article": "article", "paper": "article", "preprint": "article",
    "editorial": "article", "commentary": "article", "scale": "article",
    "textbook": "book", "monograph": "book", "ebook": "book",
    "chapter": "book_chapter",
    "tool": "software", "package": "software", "library": "software",
    "code": "software", "repository": "software", "repo": "software", "app": "software",
    "database": "dataset", "registry": "dataset", "data_portal": "dataset",
    "data_set": "dataset", "data": "dataset", "repository_data": "dataset",
    "website": "web_guide", "web_resource": "web_guide", "web_page": "web_guide",
    "webpage": "web_guide", "blog": "web_guide", "guide": "web_guide",
    "grant": "funding", "funding_call": "funding", "fellowship": "funding", "award": "funding",
    "webinar": "video", "lecture": "video", "talk": "video",
    "forum": "community", "network": "community",
}


def normalize_resource_type(value) -> str | None:
    """Map an LLM resource_type to the canonical enum. Returns None if unmappable."""
    if not value:
        return None
    v = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if v in RESOURCE_TYPES:
        return v
    return RESOURCE_TYPE_ALIASES.get(v) or RESOURCE_TYPE_ALIASES.get(v.replace("_", " "))


# Free-text research-lifecycle stage names → THESIS codes
# (TH=Theory, HI=History, EV=Evaluate, ST=Study, IN=Interpret, SH=Share).
STAGE_CODE_ALIASES = {
    "theory": "TH", "theoretical": "TH", "concept": "TH", "conceptual": "TH",
    "framework": "TH", "background": "HI", "history": "HI", "literature": "HI",
    "literature_review": "HI", "prior_work": "HI",
    "evaluate": "EV", "evaluation": "EV", "appraisal": "EV", "critical_appraisal": "EV",
    "assessment": "EV", "quality": "EV", "quality_appraisal": "EV",
    "study": "ST", "design": "ST", "research_design": "ST", "methodology": "ST",
    "methods": "ST", "methodology_development": "ST", "planning": "ST", "conduct": "ST",
    "data_collection": "ST", "data-collection": "ST", "implementation": "ST",
    "execution": "ST", "fieldwork": "ST",
    "interpret": "IN", "interpretation": "IN", "analysis": "IN", "synthesis": "IN",
    "data_synthesis": "IN", "results": "IN", "findings": "IN", "discussion": "IN",
    "share": "SH", "writing": "SH", "write_up": "SH", "dissemination": "SH",
    "reporting": "SH", "publication": "SH", "communicate": "SH", "communication": "SH",
}


def normalize_stage_code(value) -> str | None:
    """Map an LLM stage label to a THESIS code. Returns None if unmappable."""
    if not value:
        return None
    v = str(value).strip().upper()
    if v in STAGE_CODES:
        return v
    return STAGE_CODE_ALIASES.get(str(value).strip().lower().replace("-", "_").replace(" ", "_"))


def _thesis_codes() -> frozenset[str]:
    from agents.shared.tag_vocabulary import thesis_codes
    return thesis_codes()


STAGE_CODES = _thesis_codes()

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
# Methodology grounding — full live platform code list from data/taxonomy/*.json.
# MVP disambiguation text retained for the four grounding-card methodologies.
# ---------------------------------------------------------------------------

def get_classification_vocabulary_guide() -> str:
    from agents.shared.tag_vocabulary import build_classification_vocabulary_guide
    return build_classification_vocabulary_guide()


def get_methodology_guide() -> str:
    from agents.taxonomy import build_methodology_guide
    return build_methodology_guide()


def get_discipline_guide() -> str:
    from agents.taxonomy import build_discipline_guide
    return build_discipline_guide()


def get_subtype_guide() -> str:
    from agents.taxonomy import build_subtype_guide
    return build_subtype_guide()


def get_skill_guide() -> str:
    from agents.taxonomy import build_skill_guide
    return build_skill_guide()


# Back-compat alias used by deterministic pipeline
METHODOLOGY_GUIDE = get_methodology_guide()


REPORTING_GUIDELINE_GUIDE = """`reporting_guideline` means a FORMAL reporting standard,
checklist, or appraisal tool for research — e.g. CONSORT, PRISMA, STROBE, STARD,
SPIRIT, TRIPOD, SRQR, COREQ, the EQUATOR Network items, or a named risk-of-bias /
quality-appraisal scale. These are the checklist/standard ITSELF, usually hosted on
equator-network.org or a society site (not a journal article DOI).

A peer-reviewed JOURNAL ARTICLE that merely discusses, reviews, introduces, applies,
or is titled "Guidelines for …" is `article`, NOT `reporting_guideline` — even when
its title contains "guideline(s)". Tell-tale signs it is an `article`: the metadata
shows a journal_name / volume / issue / a journal DOI (10.xxxx via a publisher like
Wiley, Elsevier, Taylor & Francis, Springer), or it is a narrative/methods review or
a validation study of a scale. When in doubt and the metadata says it is in a journal,
choose `article`."""

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
