"""
Tests for scripts/sync.py (Firestore approved records → Compendium /api/import/json).

Committed before implementation — all tests must fail initially.
Mocks Firestore and HTTP so no external calls are made.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

APPROVED_RECORD_1 = {
    "resource_code": "syn01-article-001",
    "title": "PRISMA 2020 statement",
    "url": "https://doi.org/10.1136/bmj.n71",
    "resource_type_code": "article",
    "editorial_description": "Updated systematic review reporting guideline.",
    "editorial_description_plain": "A checklist for clear literature review reporting.",
    "methodology_codes": ["SYN-01"],
    "access_type": "open_access",
    "editorial_status": "published",
    "doi": "10.1136/bmj.n71",
}

APPROVED_RECORD_2 = {
    "resource_code": "obs01-article-002",
    "title": "STROBE statement for observational studies",
    "url": "https://doi.org/10.1093/aje/kwm255",
    "resource_type_code": "article",
    "editorial_description": "Reporting guideline for observational studies.",
    "editorial_description_plain": "A checklist to help report studies that observe but don't intervene.",
    "methodology_codes": ["OBS-01"],
    "access_type": "free",
    "editorial_status": "published",
}

ALREADY_SYNCED = {
    **APPROVED_RECORD_1,
    "compendium_synced_at": "2026-06-05T10:00:00Z",
    "compendium_batch_id": "existing-batch-uuid",
}


def _make_fs_doc(data: dict, doc_id: str = "doc1"):
    doc = MagicMock()
    doc.id = doc_id
    doc.to_dict.return_value = dict(data)
    return doc


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

from scripts.sync import (
    fetch_unsynced_records,
    post_to_compendium,
    mark_synced,
    mark_sync_error,
    run_sync,
    SyncResult,
)


# ---------------------------------------------------------------------------
# fetch_unsynced_records
# ---------------------------------------------------------------------------

class TestFetchUnsyncedRecords:
    def test_returns_records_without_synced_at(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        query = col.where.return_value
        query.stream.return_value = [
            _make_fs_doc(APPROVED_RECORD_1, "doc1"),
            _make_fs_doc(APPROVED_RECORD_2, "doc2"),
        ]
        records = fetch_unsynced_records(mock_db)
        assert len(records) == 2
        assert records[0]["_doc_id"] == "doc1"
        assert records[1]["_doc_id"] == "doc2"

    def test_excludes_fully_synced_records(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        query = col.where.return_value
        query.stream.return_value = [
            _make_fs_doc({
                **ALREADY_SYNCED,
                "compendium_id": "uuid-1",
                "compendium_url": "https://cothesis.ai/library/resource/uuid-1",
            }, "doc-synced"),
        ]
        records = fetch_unsynced_records(mock_db)
        assert records == []

    def test_includes_synced_records_missing_id_or_url(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        query = col.where.return_value
        query.stream.return_value = [
            _make_fs_doc({
                **APPROVED_RECORD_1,
                "compendium_synced_at": "2026-06-09T00:00:00Z",
                "compendium_batch_id": "old-batch",
            }, "doc-resync"),
        ]
        records = fetch_unsynced_records(mock_db)
        assert len(records) == 1
        assert records[0]["_doc_id"] == "doc-resync"

    def test_queries_published_status(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        col.where.return_value.stream.return_value = []
        fetch_unsynced_records(mock_db)
        mock_db.collection.assert_called_with("resources")
        col.where.assert_called_with("editorial_status", "==", "published")

    def test_respects_limit(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        query = col.where.return_value
        query.limit.return_value.stream.return_value = []
        fetch_unsynced_records(mock_db, limit=25)
        query.limit.assert_called_with(25)


# ---------------------------------------------------------------------------
# post_to_compendium
# ---------------------------------------------------------------------------

class TestPostToCompendium:
    def test_posts_records_as_import_candidate_array(self):
        records = [
            {**APPROVED_RECORD_1, "_doc_id": "doc1"},
            {**APPROVED_RECORD_2, "_doc_id": "doc2"},
        ]
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "success": True,
                "import_batch_id": "batch-uuid-123",
                "job_id": "job-456",
                "resources": [
                    {
                        "resource_id": "rid-1",
                        "public_url": "https://cothesis.ai/library/resources/rid-1",
                    },
                    {"resource_id": "rid-2"},
                ],
            }
            mock_post.return_value.raise_for_status = MagicMock()
            result = post_to_compendium(
                records,
                compendium_url="https://cothesis.ai",
                api_key="test-key",
            )
        assert result.import_batch_id == "batch-uuid-123"
        assert result.outcomes[0].compendium_id == "rid-1"
        assert result.outcomes[0].compendium_url == "https://cothesis.ai/library/resources/rid-1"
        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs["json"]
        assert body["source_tool"] == "claude"
        assert len(body["resources"]) == 2

    def test_uses_bearer_auth(self):
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "success": True, "import_batch_id": "b", "job_id": "j"
            }
            mock_post.return_value.raise_for_status = MagicMock()
            post_to_compendium(
                [{**APPROVED_RECORD_1, "_doc_id": "d"}],
                compendium_url="https://cothesis.ai",
                api_key="secret-key",
            )
        headers = mock_post.call_args.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer secret-key"

    def test_correct_endpoint_url(self):
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "success": True, "import_batch_id": "b", "job_id": "j"
            }
            mock_post.return_value.raise_for_status = MagicMock()
            post_to_compendium(
                [{**APPROVED_RECORD_1, "_doc_id": "d"}],
                compendium_url="https://cothesis.ai",
                api_key="k",
            )
        url = mock_post.call_args.args[0]
        assert url == "https://cothesis.ai/api/import/json"

    def test_raises_on_http_error(self):
        import httpx
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(httpx.HTTPStatusError):
                post_to_compendium(
                    [{**APPROVED_RECORD_1, "_doc_id": "d"}],
                    compendium_url="https://cothesis.ai",
                    api_key="bad-key",
                )


# ---------------------------------------------------------------------------
# mark_synced / mark_sync_error
# ---------------------------------------------------------------------------

class TestMarkSynced:
    def test_writes_synced_at_and_batch_id(self):
        from agents.shared.compendium_sync import ResourceSyncOutcome

        mock_db = MagicMock()
        col = mock_db.collection.return_value
        doc_ref = col.document.return_value
        mark_synced(
            mock_db,
            "doc1",
            "batch-uuid-abc",
            ResourceSyncOutcome("rid-1", "https://cothesis.ai/library/resources/rid-1"),
        )
        mock_db.collection.assert_called_with("resources")
        col.document.assert_called_with("doc1")
        update_data = doc_ref.update.call_args.args[0]
        assert "compendium_synced_at" in update_data
        assert update_data["compendium_batch_id"] == "batch-uuid-abc"
        assert update_data["compendium_id"] == "rid-1"
        assert update_data["compendium_url"] == "https://cothesis.ai/library/resources/rid-1"

    def test_clears_sync_error_on_success(self):
        mock_db = MagicMock()
        doc_ref = mock_db.collection.return_value.document.return_value
        mark_synced(mock_db, "doc1", "batch-abc")
        update_data = doc_ref.update.call_args.args[0]
        assert "compendium_sync_error" in update_data
        assert update_data["compendium_sync_error"] is None


class TestMarkSyncError:
    def test_writes_error_message(self):
        mock_db = MagicMock()
        doc_ref = mock_db.collection.return_value.document.return_value
        mark_sync_error(mock_db, "doc1", "HTTP 401 Unauthorized")
        update_data = doc_ref.update.call_args.args[0]
        assert update_data["compendium_sync_error"] == "HTTP 401 Unauthorized"

    def test_does_not_set_synced_at(self):
        mock_db = MagicMock()
        doc_ref = mock_db.collection.return_value.document.return_value
        mark_sync_error(mock_db, "doc1", "error")
        update_data = doc_ref.update.call_args.args[0]
        assert "compendium_synced_at" not in update_data


# ---------------------------------------------------------------------------
# run_sync integration
# ---------------------------------------------------------------------------

class TestRunSync:
    def test_returns_sync_result(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        col.where.return_value.stream.return_value = [
            _make_fs_doc({**APPROVED_RECORD_1, "_doc_id": "d1"}, "d1"),
        ]
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "success": True, "import_batch_id": "b1", "job_id": "j1",
                "resources": [{"resource_id": "r1"}],
            }
            mock_post.return_value.raise_for_status = MagicMock()
            result = run_sync(
                db=mock_db,
                compendium_url="https://cothesis.ai",
                api_key="key",
            )
        assert isinstance(result, SyncResult)
        assert result.synced == 1
        assert result.errors == 0
        assert result.batch_ids == ["b1"]

    def test_dry_run_skips_post_and_update(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        col.where.return_value.stream.return_value = [
            _make_fs_doc(APPROVED_RECORD_1, "d1"),
        ]
        with patch("scripts.sync.httpx.post") as mock_post:
            result = run_sync(
                db=mock_db,
                compendium_url="https://cothesis.ai",
                api_key="key",
                dry_run=True,
            )
        mock_post.assert_not_called()
        assert result.synced == 0
        assert result.dry_run is True

    def test_marks_error_on_http_failure(self):
        import httpx
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        col.where.return_value.stream.return_value = [
            _make_fs_doc(APPROVED_RECORD_1, "d1"),
        ]
        doc_ref = mock_db.collection.return_value.document.return_value
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=MagicMock()
            )
            result = run_sync(
                db=mock_db,
                compendium_url="https://cothesis.ai",
                api_key="key",
            )
        assert result.errors == 1
        assert result.synced == 0

    def test_batches_records_by_batch_size(self):
        mock_db = MagicMock()
        col = mock_db.collection.return_value
        col.where.return_value.stream.return_value = [
            _make_fs_doc({**APPROVED_RECORD_1, "resource_code": f"r-{i}"}, f"d{i}")
            for i in range(5)
        ]
        with patch("scripts.sync.httpx.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "success": True, "import_batch_id": "b", "job_id": "j"
            }
            mock_post.return_value.raise_for_status = MagicMock()
            run_sync(
                db=mock_db,
                compendium_url="https://cothesis.ai",
                api_key="key",
                batch_size=2,
            )
        # 5 records at batch_size=2 → 3 POST calls
        assert mock_post.call_count == 3
