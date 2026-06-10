"""Tests for enrichment_queue_sync."""
from __future__ import annotations

from unittest.mock import MagicMock

from agents.shared.enrichment_queue_sync import (
    merge_live_catalog,
    preview_sync,
    sync_to_enrichment_queue,
    _pascal_type,
)


def test_pascal_type_from_snake():
    assert _pascal_type("reporting_guideline") == "ReportingGuideline"
    assert _pascal_type("Article") == "Article"


def test_merge_live_catalog_neo4j_fills_gaps():
    pg = [{"resource_id": "aaa", "title": "From PG"}]
    neo = [{"resource_id": "bbb", "title": "From Neo4j"}]
    merged = merge_live_catalog(postgres_rows=pg, neo4j_rows=neo)
    assert set(merged) == {"aaa", "bbb"}
    assert merged["aaa"]["title"] == "From PG"


def test_preview_sync_counts():
    conn = MagicMock()
    mock_cur = conn.cursor.return_value.__enter__.return_value
    mock_cur.fetchall.return_value = [
        {"resource_id": "aaa", "status": "complete", "queue_id": "q1"},
        {"resource_id": "bbb", "status": "pending", "queue_id": "q2"},
    ]
    catalog = {
        "aaa": {"resource_type": "article"},
        "bbb": {"resource_type": "book"},
        "ccc": {"resource_type": "article"},
    }
    preview = preview_sync(conn, catalog)
    assert preview == {"catalog": 3, "insert": 1, "requeue": 1, "unchanged_pending": 1}


def test_sync_replaces_existing_rows():
    conn = MagicMock()
    mock_cur = conn.cursor.return_value.__enter__.return_value
    mock_cur.fetchall.return_value = [
        {"resource_id": "aaa", "status": "complete", "queue_id": "q1"},
    ]
    catalog = {
        "aaa": {"resource_type": "article"},
        "bbb": {"resource_type": "book"},
    }
    mock_cur.rowcount = 1
    stats = sync_to_enrichment_queue(conn, catalog, reset_existing=True)
    assert stats["inserted"] == 2
    sqls = [c.args[0] for c in mock_cur.execute.call_args_list]
    assert any("DELETE FROM compendium.enrichment_queue" in s for s in sqls)
    conn.commit.assert_called_once()
    assert mock_cur.executemany.called
