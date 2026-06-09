"""Tests for agents/shared/compendium_sync.py — import response → id/url fields."""
from __future__ import annotations

from agents.shared.compendium_sync import (
    build_compendium_public_url,
    extract_public_url,
    extract_resource_id,
    parse_import_response,
)


RECORD = {
    "resource_code": "syn01-article-001",
    "title": "PRISMA 2020 statement",
    "url": "https://doi.org/10.1136/bmj.n71",
    "resource_type_code": "article",
    "resource_subtype_code": "reporting_guideline",
}


class TestExtractResourceId:
    def test_resource_id_key(self):
        assert extract_resource_id({"resource_id": "uuid-abc"}) == "uuid-abc"

    def test_compendium_id_key(self):
        assert extract_resource_id({"compendium_id": "uuid-xyz"}) == "uuid-xyz"


class TestBuildCompendiumPublicUrl:
    def test_from_resource_id(self):
        url = build_compendium_public_url(
            "https://cothesis.ai",
            resource_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert url == "https://cothesis.ai/library/resources/550e8400-e29b-41d4-a716-446655440000"

    def test_from_slug_and_subtype(self):
        url = build_compendium_public_url(
            "https://compendium-web-production.up.railway.app",
            slug="prisma-2020",
            subtype_slug="reporting_guideline",
            resource_type_code="article",
        )
        assert url.endswith("/library/reporting-guideline/prisma-2020")


class TestExtractPublicUrl:
    def test_absolute_url_in_response(self):
        item = {"public_url": "https://cothesis.ai/library/articles/prisma"}
        assert extract_public_url(item, "https://cothesis.ai", RECORD) == (
            "https://cothesis.ai/library/articles/prisma"
        )

    def test_relative_path_in_response(self):
        item = {"url": "/library/reporting-guideline/prisma-2020"}
        assert extract_public_url(item, "https://cothesis.ai", RECORD) == (
            "https://cothesis.ai/library/reporting-guideline/prisma-2020"
        )

    def test_builds_from_resource_id(self):
        item = {"resource_id": "abc-123"}
        assert extract_public_url(item, "https://cothesis.ai", RECORD) == (
            "https://cothesis.ai/library/resources/abc-123"
        )


class TestParseImportResponse:
    def test_batch_only_response(self):
        result = parse_import_response(
            {"success": True, "import_batch_id": "batch-1", "job_id": "job-1"},
            [RECORD],
            "https://cothesis.ai",
        )
        assert result.import_batch_id == "batch-1"
        assert len(result.outcomes) == 1
        assert result.outcomes[0].compendium_id is None
        assert result.outcomes[0].compendium_url is None

    def test_per_resource_array(self):
        result = parse_import_response(
            {
                "import_batch_id": "batch-2",
                "resources": [
                    {
                        "resource_id": "rid-1",
                        "slug": "prisma-2020",
                        "public_url": "https://cothesis.ai/library/reporting-guideline/prisma-2020",
                    }
                ],
            },
            [RECORD],
            "https://cothesis.ai",
        )
        assert result.outcomes[0].compendium_id == "rid-1"
        assert result.outcomes[0].compendium_url == (
            "https://cothesis.ai/library/reporting-guideline/prisma-2020"
        )

    def test_accepted_resources_alias(self):
        result = parse_import_response(
            {
                "batch_id": "batch-3",
                "accepted_resources": [{"compendium_id": "rid-9", "slug": "strobe"}],
            },
            [RECORD],
            "https://cothesis.ai",
        )
        assert result.import_batch_id == "batch-3"
        assert result.outcomes[0].compendium_id == "rid-9"
        assert result.outcomes[0].compendium_url == "https://cothesis.ai/library/resources/rid-9"
