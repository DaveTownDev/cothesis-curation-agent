"""Tests for live Compendium export helpers."""
from agents.shared.live_compendium_export import (
    compendium_public_url,
    normalize_export_row,
    to_pipeline_input,
)


def test_to_pipeline_input_maps_article():
    row = {
        "resource_id": "abc-123",
        "title": "PRISMA 2020",
        "url": "https://doi.org/10.1136/bmj.n71",
        "description": "Reporting guideline",
        "resource_type": "Article",
        "methodology_tags": ["SYN-01"],
        "doi": "10.1136/bmj.n71",
    }
    out = to_pipeline_input(row)
    assert out["resource_type"] == "article"
    assert out["methodology_tags"] == ["SYN-01"]
    assert out["compendium_id"] == "abc-123"
    assert "library/resource/abc-123" in out["compendium_url"]


def test_normalize_export_row_snake_cases_type():
    row = normalize_export_row({"resource_id": "x", "resource_type": "ReportingGuideline"})
    assert row["resource_type"] == "reporting_guideline"


def test_compendium_public_url():
    url = compendium_public_url("uuid-here", "https://example.com")
    assert url == "https://example.com/library/resource/uuid-here"
