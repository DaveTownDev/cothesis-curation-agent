"""
Per-type enrichment: fetch all available free sources for a resource and merge
into a `type_fields` dict (shaped per docs/field_maps/field_mapping_<type>.md).

Returns {type_fields, enrichment_sources, needs_api_key}. The merged metadata
is ALSO used as the appraisal LLM's context (deterministic-API-first) — so this
one call delivers both the type_fields and the metadata-fallback chain.
"""
from __future__ import annotations

from agents.enrichment import sources as S


def _merge(*dicts: dict) -> dict:
    """Merge source dicts; earlier non-empty values win; drop None/empty + _source."""
    out: dict = {}
    used = []
    for d in dicts:
        if not d:
            continue
        if d.get("_source"):
            used.append(d["_source"])
        for k, v in d.items():
            if k == "_source" or v in (None, "", [], {}):
                continue
            out.setdefault(k, v)
    return out, used


def enrich(resource_type: str, ids: dict) -> dict:
    """
    resource_type: snake_case canonical type.
    ids: {doi, pmid, isbn, url, title, github_url}
    """
    doi = ids.get("doi")
    pmid = ids.get("pmid")
    isbn = ids.get("isbn")
    title = ids.get("title")
    url = ids.get("url")
    github_url = ids.get("github_url") or (url if url and "github.com" in url else None)

    needs_key: list[str] = []

    if resource_type in ("article", "reporting_guideline", "book_chapter"):
        tf, used = _merge(
            S.crossref(doi),
            S.openalex(doi=doi, title=title),
            S.pubmed(pmid),
            S.unpaywall(doi),
            S.icite(pmid),
        )
        needs_key = ["altmetric", "dimensions", "scite"]
    elif resource_type in ("book",):
        tf, used = _merge(
            S.openlibrary(isbn=isbn, title=title),
            S.google_books(isbn=isbn, title=title),
            S.crossref(doi),
        )
        needs_key = ["isbndb"]
    elif resource_type == "software":
        tf, used = _merge(
            S.github(github_url),
            S.biotools(title),
        )
    elif resource_type == "dataset":
        tf, used = _merge(
            S.datacite(doi),
            S.crossref(doi),
            S.openalex(doi=doi, title=title),
        )
    else:
        # video, podcast, course, web_guide, template, visual_reference,
        # community, funding — no free structured source wired yet.
        tf, used = {}, []

    return {
        "type_fields": tf,
        "enrichment_sources": used,
        "needs_api_key": needs_key,
    }
