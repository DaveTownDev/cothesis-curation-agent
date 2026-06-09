"""Tests for agents/shared/url_safety SSRF guards."""
import pytest

from agents.shared.url_safety import is_safe_outbound_url, normalise_doi, safe_https_url


def test_blocks_metadata_host():
    assert not is_safe_outbound_url("https://metadata.google.internal/computeMetadata/v1/")


def test_blocks_private_ip_literal():
    assert not is_safe_outbound_url("https://169.254.169.254/latest/meta-data/")


def test_blocks_non_https():
    assert not is_safe_outbound_url("http://example.com/")


def test_allows_public_https(monkeypatch):
    monkeypatch.setattr(
        "agents.shared.url_safety._hostname_resolves_to_blocked_ip",
        lambda _h: False,
    )
    assert is_safe_outbound_url("https://example.com/article")


def test_safe_https_url_returns_none_when_blocked():
    assert safe_https_url("http://127.0.0.1/") is None


@pytest.mark.parametrize("doi", ["10.1234/abc", "10.1038/nature12345"])
def test_normalise_doi_valid(doi):
    assert normalise_doi(doi) == doi


def test_normalise_doi_rejects_path_traversal():
    assert normalise_doi("10.1234/evil/../../../metadata") is None
