"""Tests for agents/enrichment — per-type dispatch + graceful failure (mocked sources)."""
from unittest.mock import patch

from agents.enrichment import enrich
from agents.enrichment import sources as S


def test_article_merges_free_sources():
    with patch.object(S, "crossref", return_value={"journal_name": "BMJ", "publication_year": 2021, "_source": "crossref"}), \
         patch.object(S, "openalex", return_value={"cited_by_count": 9000, "is_open_access": True, "_source": "openalex"}), \
         patch.object(S, "pubmed", return_value={}), \
         patch.object(S, "unpaywall", return_value={}), \
         patch.object(S, "icite", return_value={}):
        out = enrich("article", {"doi": "10.1136/bmj.n71", "title": "PRISMA"})
    tf = out["type_fields"]
    assert tf["journal_name"] == "BMJ"
    assert tf["cited_by_count"] == 9000
    assert tf["is_open_access"] is True
    assert "crossref" in out["enrichment_sources"] and "openalex" in out["enrichment_sources"]


def test_book_uses_book_sources():
    with patch.object(S, "openlibrary", return_value={"page_count": 300, "publisher": "Wiley", "_source": "openlibrary"}), \
         patch.object(S, "google_books", return_value={}), \
         patch.object(S, "crossref", return_value={}):
        out = enrich("book", {"isbn": "9781118603734", "title": "Methods in Social Epi"})
    assert out["type_fields"]["page_count"] == 300
    assert out["needs_api_key"] == ["isbndb"]


def test_software_uses_github():
    with patch.object(S, "github", return_value={"github_stars": 1200, "license": "MIT", "_source": "github"}), \
         patch.object(S, "biotools", return_value={}):
        out = enrich("software", {"url": "https://github.com/owner/repo", "title": "tool"})
    assert out["type_fields"]["github_stars"] == 1200


def test_unwired_type_returns_empty():
    out = enrich("podcast", {"title": "Some podcast"})
    assert out["type_fields"] == {}
    assert out["enrichment_sources"] == []


def test_source_failure_is_graceful():
    # All sources return {} -> empty type_fields, no crash
    with patch.object(S, "crossref", return_value={}), \
         patch.object(S, "openalex", return_value={}), \
         patch.object(S, "pubmed", return_value={}), \
         patch.object(S, "unpaywall", return_value={}), \
         patch.object(S, "icite", return_value={}):
        out = enrich("article", {"doi": "10.0/x"})
    assert out["type_fields"] == {}
