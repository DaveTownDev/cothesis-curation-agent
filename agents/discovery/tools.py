"""
Discovery tools — deterministic academic API lookups.

Production: these delegate to the MCP server (MCPToolset via SSE).
Local dev: direct API calls using the same result shapes.

The MCP server connection is set up in agent.py; these tools are the
fallback / test doubles when MCP_SERVER_URL is not configured.
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_OPENALEX_METHODOLOGY_QUERY = {
    "SYN-01": "narrative systematic review narrative synthesis",
    "SYN-02": "scoping review evidence mapping",
    "OBS-01": "retrospective chart review medical records",
    "EVAL-01": "standards-based clinical audit quality improvement",
}

_TYPE_TO_OPENALEX_FILTER = {
    "article": "type:article",
    "book": "type:book",
    "book_chapter": "type:book-chapter",
    "reporting_guideline": "type:article",
    "web_guide": None,
    "course": None,
    "video": None,
    "podcast": None,
    "software": None,
    "template": None,
    "visual_reference": None,
    "dataset": None,
    "community": None,
    "funding": None,
}


def search_openalex(methodology_code: str, resource_type: str, max_results: int = 10) -> list[dict]:
    """
    Search OpenAlex for resources matching a methodology + type.
    Returns a list of raw candidate dicts.
    """
    query_terms = _OPENALEX_METHODOLOGY_QUERY.get(methodology_code, methodology_code)
    type_filter = _TYPE_TO_OPENALEX_FILTER.get(resource_type)

    params: dict = {
        "search": query_terms,
        "per_page": max_results,
        "select": "id,doi,title,publication_year,cited_by_count,open_access,primary_location,type",
    }
    if type_filter:
        params["filter"] = type_filter

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://api.openalex.org/works",
                params=params,
                headers={"User-Agent": "CoThesis-curation/1.0"},
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
    except Exception as exc:
        logger.warning("OpenAlex search failed: %s", exc)
        return []

    candidates = []
    for work in results:
        url = work.get("doi") or (work.get("primary_location") or {}).get("landing_page_url") or ""
        if not url:
            continue
        candidates.append({
            "title": work.get("title", ""),
            "url": url,
            "source": "openalex",
            "type_hint": resource_type,
            "raw_metadata": {
                "openalex_id": work.get("id"),
                "doi": work.get("doi"),
                "year": work.get("publication_year"),
                "cited_by_count": work.get("cited_by_count"),
                "is_open_access": (work.get("open_access") or {}).get("is_oa"),
            },
            "skip_reason": None,
        })
    return candidates


def search_pubmed(methodology_code: str, max_results: int = 10) -> list[dict]:
    """Search PubMed for articles matching a methodology."""
    query_terms = _OPENALEX_METHODOLOGY_QUERY.get(methodology_code, methodology_code)
    query = f'({query_terms})[Title/Abstract] AND ("methodology"[MeSH] OR "methods"[MeSH])'

    try:
        with httpx.Client(timeout=15) as client:
            search_resp = client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
            )
            search_resp.raise_for_status()
            pmids = search_resp.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return []

        with httpx.Client(timeout=15) as client:
            summary_resp = client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            )
            summary_resp.raise_for_status()
            result_map = summary_resp.json().get("result", {})

    except Exception as exc:
        logger.warning("PubMed search failed: %s", exc)
        return []

    candidates = []
    for pmid in pmids:
        info = result_map.get(pmid, {})
        title = info.get("title", "")
        doi = next((uid["value"] for uid in info.get("articleids", []) if uid["idtype"] == "doi"), None)
        url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        candidates.append({
            "title": title,
            "url": url,
            "source": "pubmed",
            "type_hint": "article",
            "raw_metadata": {"pmid": pmid, "doi": doi, "pub_date": info.get("pubdate")},
            "skip_reason": None,
        })
    return candidates
