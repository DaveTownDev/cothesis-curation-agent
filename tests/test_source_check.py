"""Tests for agents/shared/source_check.verify_source (mocked httpx)."""
from unittest.mock import MagicMock, patch
import httpx
import pytest

from agents.shared.source_check import verify_source


def _resp(code, url="https://x"):
    r = MagicMock()
    r.status_code = code
    r.url = url
    return r


def _client_returning(resp=None, exc=None):
    cm = MagicMock()
    client = MagicMock()
    if exc:
        client.get.side_effect = exc
    else:
        client.get.return_value = resp
    cm.__enter__.return_value = client
    return cm


def test_unknown_when_no_url_or_doi():
    assert verify_source(None, None)["status"] == "unknown"


def test_live_on_200():
    with patch("agents.shared.source_check.httpx.Client", return_value=_client_returning(_resp(200))):
        assert verify_source("https://example.com")["status"] == "live"


@pytest.mark.parametrize("code", [404, 410])
def test_dead_on_404_410(code):
    with patch("agents.shared.source_check.httpx.Client", return_value=_client_returning(_resp(code))):
        assert verify_source("https://example.com/missing")["status"] == "dead"


@pytest.mark.parametrize("code", [403, 429])
def test_blocked_treated_as_live(code):
    # Publisher anti-bot — must NOT be condemned as dead
    with patch("agents.shared.source_check.httpx.Client", return_value=_client_returning(_resp(code))):
        assert verify_source("https://publisher.com/article")["status"] == "blocked"


def test_doi_network_failure_is_dead():
    with patch("agents.shared.source_check.httpx.Client",
               return_value=_client_returning(exc=httpx.ConnectError("no resolve"))):
        assert verify_source(None, doi="10.0000/fake")["status"] == "dead"


def test_unsafe_url_blocked_without_fetch():
    with patch("agents.shared.source_check.is_safe_outbound_url", return_value=False):
        result = verify_source("https://169.254.169.254/latest/meta-data/")
    assert result["status"] == "dead"
    assert result.get("err") == "blocked url"


def test_bare_url_network_blip_is_blocked_not_dead():
    with patch("agents.shared.source_check.httpx.Client",
               return_value=_client_returning(exc=httpx.ReadTimeout("slow"))):
        assert verify_source("https://example.com")["status"] == "blocked"
