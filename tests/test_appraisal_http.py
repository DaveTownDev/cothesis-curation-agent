"""
Tests for Appraisal HTTP fetch functions (OpenAlex + PubMed metadata).
All HTTP calls mocked — no real network.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestFetchOpenAlexMetadata:

    def test_fetches_by_doi(self):
        from agents.appraisal.tools import fetch_openalex_metadata
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "id": "https://openalex.org/W111",
            "title": "STROBE Statement",
            "cited_by_count": 5000,
        }
        with patch("agents.appraisal.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            result = fetch_openalex_metadata(doi="10.1371/journal.pmed.0040297")
        assert result["title"] == "STROBE Statement"
        assert result["cited_by_count"] == 5000

    def test_fetches_by_title(self):
        from agents.appraisal.tools import fetch_openalex_metadata
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"results": [{"id": "W222", "title": "PRISMA 2020"}]}
        with patch("agents.appraisal.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            result = fetch_openalex_metadata(title="PRISMA 2020")
        assert result["title"] == "PRISMA 2020"

    def test_no_args_returns_empty(self):
        from agents.appraisal.tools import fetch_openalex_metadata
        result = fetch_openalex_metadata()
        assert result == {}

    def test_http_error_returns_empty(self):
        from agents.appraisal.tools import fetch_openalex_metadata
        with patch("agents.appraisal.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.side_effect = Exception("timeout")
            result = fetch_openalex_metadata(doi="10.9999/bad")
        assert result == {}

    def test_empty_results_list_returns_empty(self):
        from agents.appraisal.tools import fetch_openalex_metadata
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"results": []}
        with patch("agents.appraisal.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            result = fetch_openalex_metadata(title="nothing found")
        assert result == {}


class TestFetchPubMedMetadata:

    def test_fetches_by_pmid(self):
        from agents.appraisal.tools import fetch_pubmed_metadata
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "result": {"17941714": {"title": "STROBE statement", "pubdate": "2007"}}
        }
        with patch("agents.appraisal.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            result = fetch_pubmed_metadata(pmid="17941714")
        assert result["title"] == "STROBE statement"

    def test_no_pmid_returns_empty(self):
        from agents.appraisal.tools import fetch_pubmed_metadata
        result = fetch_pubmed_metadata()
        assert result == {}

    def test_http_error_returns_empty(self):
        from agents.appraisal.tools import fetch_pubmed_metadata
        with patch("agents.appraisal.tools.httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.side_effect = Exception("timeout")
            result = fetch_pubmed_metadata(pmid="99999")
        assert result == {}
