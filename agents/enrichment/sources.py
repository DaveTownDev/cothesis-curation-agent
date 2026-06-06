"""
Free / keyless metadata source clients.

Each function returns a plain dict (normalised subset) or {} on any failure.
~10s timeout, never raises. These are the field-maps' Tier-1 free sources;
keyed premium sources (Altmetric, Dimensions, Scite, ISBNdb) are listed in
NEEDS_API_KEY and left unimplemented until credentials exist.
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

CONTACT_EMAIL = os.environ.get("ENRICHMENT_CONTACT_EMAIL", "research@cothesis.ai")
_UA = {"User-Agent": f"CoThesis-curation/1.0 (mailto:{CONTACT_EMAIL})"}
_TIMEOUT = 10

NEEDS_API_KEY = ["altmetric", "dimensions", "scite", "isbndb"]


def _get(url: str, params: dict | None = None) -> dict | None:
    try:
        with httpx.Client(timeout=_TIMEOUT, headers=_UA, follow_redirects=True) as c:
            r = c.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as exc:
        logger.warning("source GET failed %s: %s", url, str(exc)[:80])
        return None


# ── Articles / reporting guidelines ──────────────────────────────────────────

def crossref(doi: str) -> dict:
    if not doi:
        return {}
    d = _get(f"https://api.crossref.org/works/{doi}")
    m = (d or {}).get("message") or {}
    if not m:
        return {}
    return {
        "title": (m.get("title") or [None])[0],
        "journal_name": (m.get("container-title") or [None])[0],
        "publisher": m.get("publisher"),
        "publication_year": (m.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0],
        "volume": m.get("volume"),
        "issue": m.get("issue"),
        "pages": m.get("page"),
        "issn": (m.get("ISSN") or [None])[0],
        "reference_count": m.get("reference-count"),
        "citation_count": m.get("is-referenced-by-count"),
        "type": m.get("type"),
        "authors": [f"{a.get('given','')} {a.get('family','')}".strip()
                    for a in (m.get("author") or [])][:25],
        "_source": "crossref",
    }


def openalex(doi: str | None = None, title: str | None = None) -> dict:
    if doi:
        d = _get(f"https://api.openalex.org/works/https://doi.org/{doi}")
    elif title:
        d = _get("https://api.openalex.org/works",
                 {"search": title, "per_page": 1, "mailto": CONTACT_EMAIL})
        d = (d or {}).get("results", [None])[0] if d else None
    else:
        return {}
    if not d:
        return {}
    pl = d.get("primary_location") or {}
    src = pl.get("source") or {}
    return {
        "openalex_id": d.get("id"),
        "publication_year": d.get("publication_year"),
        "cited_by_count": d.get("cited_by_count"),
        "is_open_access": (d.get("open_access") or {}).get("is_oa"),
        "journal_name": src.get("display_name"),
        "type": d.get("type"),
        "topics": [t.get("display_name") for t in (d.get("topics") or [])][:5],
        "_source": "openalex",
    }


def pubmed(pmid: str) -> dict:
    if not pmid:
        return {}
    d = _get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
             {"db": "pubmed", "id": pmid, "retmode": "json"})
    rec = ((d or {}).get("result") or {}).get(pmid) or {}
    if not rec:
        return {}
    return {
        "pmid": pmid,
        "title": rec.get("title"),
        "journal_name": rec.get("fulljournalname") or rec.get("source"),
        "pubdate": rec.get("pubdate"),
        "authors": [a.get("name") for a in (rec.get("authors") or [])][:25],
        "_source": "pubmed",
    }


def unpaywall(doi: str) -> dict:
    if not doi:
        return {}
    d = _get(f"https://api.unpaywall.org/v2/{doi}", {"email": CONTACT_EMAIL})
    if not d:
        return {}
    return {
        "is_open_access": d.get("is_oa"),
        "oa_status": d.get("oa_status"),
        "pdf_url": ((d.get("best_oa_location") or {}) or {}).get("url_for_pdf"),
        "_source": "unpaywall",
    }


def icite(pmid: str) -> dict:
    if not pmid:
        return {}
    d = _get("https://icite.od.nih.gov/api/pubs", {"pmids": pmid})
    rec = ((d or {}).get("data") or [None])[0]
    if not rec:
        return {}
    return {
        "relative_citation_ratio": rec.get("relative_citation_ratio"),
        "nih_percentile": rec.get("nih_percentile"),
        "citation_count": rec.get("citation_count"),
        "_source": "icite",
    }


# ── Books / book chapters ────────────────────────────────────────────────────

def openlibrary(isbn: str | None = None, title: str | None = None) -> dict:
    if isbn:
        d = _get("https://openlibrary.org/api/books",
                 {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"})
        rec = (d or {}).get(f"ISBN:{isbn}") or {}
    elif title:
        d = _get("https://openlibrary.org/search.json", {"title": title, "limit": 1})
        rec = ((d or {}).get("docs") or [None])[0] or {}
    else:
        return {}
    if not rec:
        return {}
    return {
        "isbn": isbn,
        "publisher": (rec.get("publishers") or [{}])[0].get("name") if isinstance(rec.get("publishers"), list) and rec.get("publishers") and isinstance(rec["publishers"][0], dict) else (rec.get("publisher") or [None])[0] if isinstance(rec.get("publisher"), list) else None,
        "publication_year": rec.get("publish_date") or rec.get("first_publish_year"),
        "page_count": rec.get("number_of_pages") or rec.get("number_of_pages_median"),
        "subjects": [s.get("name") if isinstance(s, dict) else s for s in (rec.get("subjects") or [])][:8],
        "authors": [a.get("name") if isinstance(a, dict) else a for a in (rec.get("authors") or [])][:10],
        "_source": "openlibrary",
    }


def google_books(isbn: str | None = None, title: str | None = None) -> dict:
    q = f"isbn:{isbn}" if isbn else (title or "")
    if not q:
        return {}
    d = _get("https://www.googleapis.com/books/v1/volumes", {"q": q, "maxResults": 1})
    items = (d or {}).get("items") or []
    if not items:
        return {}
    vi = items[0].get("volumeInfo") or {}
    return {
        "publisher": vi.get("publisher"),
        "publication_year": (vi.get("publishedDate") or "")[:4] or None,
        "page_count": vi.get("pageCount"),
        "categories": vi.get("categories"),
        "authors": vi.get("authors", [])[:10],
        "_source": "google_books",
    }


# ── Software ─────────────────────────────────────────────────────────────────

def github(repo_url: str) -> dict:
    if not repo_url or "github.com" not in repo_url:
        return {}
    import re
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
    if not m:
        return {}
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    d = _get(f"https://api.github.com/repos/{owner}/{repo}")
    if not d or "full_name" not in d:
        return {}
    return {
        "github_stars": d.get("stargazers_count"),
        "github_forks": d.get("forks_count"),
        "github_language": d.get("language"),
        "license": (d.get("license") or {}).get("spdx_id"),
        "homepage": d.get("homepage"),
        "open_issues": d.get("open_issues_count"),
        "_source": "github",
    }


def biotools(name: str) -> dict:
    if not name:
        return {}
    d = _get("https://bio.tools/api/tool/", {"q": name, "format": "json"})
    rec = ((d or {}).get("list") or [None])[0]
    if not rec:
        return {}
    return {
        "biotools_id": rec.get("biotoolsID"),
        "edam_topics": [t.get("term") for t in (rec.get("topic") or [])][:5],
        "homepage": rec.get("homepage"),
        "_source": "biotools",
    }


# ── Datasets ─────────────────────────────────────────────────────────────────

def datacite(doi: str) -> dict:
    if not doi:
        return {}
    d = _get(f"https://api.datacite.org/dois/{doi}")
    attr = ((d or {}).get("data") or {}).get("attributes") or {}
    if not attr:
        return {}
    return {
        "publisher": attr.get("publisher"),
        "publication_year": attr.get("publicationYear"),
        "doi": attr.get("doi"),
        "_source": "datacite",
    }
