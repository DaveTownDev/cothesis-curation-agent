"""
Discovery tools tests — mocked HTTP so no real network calls.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestSearchOpenAlex:

    def _mock_openalex_response(self, works: list[dict]) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = {"results": works}
        resp.raise_for_status.return_value = None
        return resp

    def test_returns_candidate_list(self):
        from agents.discovery.tools import search_openalex
        fake_work = {
            "id": "https://openalex.org/W1234",
            "doi": "https://doi.org/10.1001/test",
            "title": "Narrative Systematic Review Methods",
            "publication_year": 2022,
            "cited_by_count": 150,
            "open_access": {"is_oa": True},
            "primary_location": {"landing_page_url": "https://doi.org/10.1001/test"},
            "type": "article",
        }
        mock_resp = self._mock_openalex_response([fake_work])
        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            results = search_openalex("SYN-01", "article", max_results=5)
        assert len(results) == 1
        assert results[0]["title"] == "Narrative Systematic Review Methods"
        assert results[0]["source"] == "openalex"
        assert results[0]["type_hint"] == "article"
        assert results[0]["skip_reason"] is None

    def test_raw_metadata_includes_key_fields(self):
        from agents.discovery.tools import search_openalex
        fake_work = {
            "id": "https://openalex.org/W5678",
            "doi": "https://doi.org/10.1002/test",
            "title": "Scoping Review Methodology",
            "publication_year": 2021,
            "cited_by_count": 80,
            "open_access": {"is_oa": False},
            "primary_location": {"landing_page_url": "https://doi.org/10.1002/test"},
            "type": "article",
        }
        mock_resp = self._mock_openalex_response([fake_work])
        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            results = search_openalex("SYN-02", "article")
        assert results[0]["raw_metadata"]["cited_by_count"] == 80
        assert results[0]["raw_metadata"]["doi"] == "https://doi.org/10.1002/test"

    def test_skips_works_with_no_url(self):
        from agents.discovery.tools import search_openalex
        fake_work = {
            "id": "https://openalex.org/W9999",
            "doi": None,
            "title": "No URL Work",
            "publication_year": 2020,
            "cited_by_count": 10,
            "open_access": {"is_oa": False},
            "primary_location": None,
            "type": "article",
        }
        mock_resp = self._mock_openalex_response([fake_work])
        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            results = search_openalex("OBS-01", "article")
        assert results == []

    def test_http_error_returns_empty_list(self):
        from agents.discovery.tools import search_openalex
        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = Exception("timeout")
            results = search_openalex("EVAL-01", "article")
        assert results == []

    def test_empty_results_returns_empty_list(self):
        from agents.discovery.tools import search_openalex
        mock_resp = self._mock_openalex_response([])
        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            results = search_openalex("SYN-01", "book")
        assert results == []

    def test_all_four_mvp_methodology_codes_accepted(self):
        """search_openalex must accept all 4 MVP methodology codes without error."""
        from agents.discovery.tools import search_openalex
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status.return_value = None
        for code in ("SYN-01", "SYN-02", "OBS-01", "EVAL-01"):
            with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
                mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
                results = search_openalex(code, "article")
                assert isinstance(results, list)


class TestSearchPubMed:

    def test_returns_candidate_list(self):
        from agents.discovery.tools import search_pubmed

        mock_search_resp = MagicMock()
        mock_search_resp.raise_for_status.return_value = None
        mock_search_resp.json.return_value = {"esearchresult": {"idlist": ["17941714"]}}

        mock_summary_resp = MagicMock()
        mock_summary_resp.raise_for_status.return_value = None
        mock_summary_resp.json.return_value = {
            "result": {
                "17941714": {
                    "title": "Strengthening the reporting of observational studies in epidemiology",
                    "pubdate": "2007 Oct 16",
                    "articleids": [{"idtype": "doi", "value": "10.1371/journal.pmed.0040297"}],
                }
            }
        }

        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.get.side_effect = [mock_search_resp, mock_summary_resp]
            results = search_pubmed("OBS-01", max_results=5)

        assert len(results) == 1
        assert "STROBE" in results[0]["title"] or "observational" in results[0]["title"].lower()
        assert results[0]["source"] == "pubmed"
        assert results[0]["raw_metadata"]["pmid"] == "17941714"

    def test_no_pmids_returns_empty_list(self):
        from agents.discovery.tools import search_pubmed
        mock_search_resp = MagicMock()
        mock_search_resp.raise_for_status.return_value = None
        mock_search_resp.json.return_value = {"esearchresult": {"idlist": []}}

        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value.__enter__.return_value
            mock_client.get.return_value = mock_search_resp
            results = search_pubmed("EVAL-01")
        assert results == []

    def test_http_error_returns_empty_list(self):
        from agents.discovery.tools import search_pubmed
        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = Exception("network error")
            results = search_pubmed("SYN-01")
        assert results == []

    def test_doi_url_constructed_correctly(self):
        from agents.discovery.tools import search_pubmed

        mock_search = MagicMock()
        mock_search.raise_for_status.return_value = None
        mock_search.json.return_value = {"esearchresult": {"idlist": ["12345"]}}

        mock_summary = MagicMock()
        mock_summary.raise_for_status.return_value = None
        mock_summary.json.return_value = {
            "result": {"12345": {
                "title": "Test Article",
                "pubdate": "2023",
                "articleids": [{"idtype": "doi", "value": "10.9999/test"}],
            }}
        }

        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = [mock_search, mock_summary]
            results = search_pubmed("SYN-02")

        assert results[0]["url"] == "https://doi.org/10.9999/test"

    def test_pubmed_url_used_when_no_doi(self):
        from agents.discovery.tools import search_pubmed

        mock_search = MagicMock()
        mock_search.raise_for_status.return_value = None
        mock_search.json.return_value = {"esearchresult": {"idlist": ["99999"]}}

        mock_summary = MagicMock()
        mock_summary.raise_for_status.return_value = None
        mock_summary.json.return_value = {
            "result": {"99999": {
                "title": "No DOI Article",
                "pubdate": "2022",
                "articleids": [],
            }}
        }

        with patch("agents.discovery.tools.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = [mock_search, mock_summary]
            results = search_pubmed("OBS-01")

        assert results[0]["url"] == "https://pubmed.ncbi.nlm.nih.gov/99999/"
