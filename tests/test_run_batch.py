"""
Tests for scripts/batch.py (Railway Postgres enrichment_queue → agent pipeline).

Committed before implementation — all tests must fail initially.
Mocks Postgres and HTTP so no external calls are made.

Cloud Scheduler triggers this via the agent's /trigger/batch endpoint.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

QUEUE_ROW_1 = {
    "queue_id": "eq-uuid-001",
    "resource_id": "res-uuid-001",
    "resource_type": "article",
    "title": "PRISMA 2020 statement",
    "url": "https://doi.org/10.1136/bmj.n71",
    "description": "Updated systematic review reporting guideline.",
    "methodology_tags": ["SYN-01"],
    "doi": "10.1136/bmj.n71",
    "pmid": "33782057",
    "access_type": "free",
}

QUEUE_ROW_2 = {
    "queue_id": "eq-uuid-002",
    "resource_id": "res-uuid-002",
    "resource_type": "book",
    "title": "Designing Clinical Research",
    "url": "https://www.wolterskluwer.com/en/solutions/ovid/designing-clinical-research-101",
    "description": "Practical guide to clinical research design.",
    "methodology_tags": ["OBS-01"],
    "doi": None,
    "pmid": None,
    "access_type": "paid",
}

AGENT_RUN_RESPONSE = {
    "sessionId": "test-session-123",
    "appName": "agents",
    "userId": "batch-runner",
    "events": [{"content": {"parts": [{"text": "Pipeline complete. 1 candidate processed."}]}}],
}


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

from scripts.batch import (
    fetch_pending_items,
    build_agent_message,
    call_agent,
    mark_item_processing,
    mark_item_complete,
    mark_item_failed,
    run_batch,
    BatchResult,
)


# ---------------------------------------------------------------------------
# fetch_pending_items
# ---------------------------------------------------------------------------

class TestFetchPendingItems:
    def test_returns_pending_items(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [
            {k: v for k, v in QUEUE_ROW_1.items()},
            {k: v for k, v in QUEUE_ROW_2.items()},
        ]
        rows = fetch_pending_items(mock_conn, batch_size=10)
        assert len(rows) == 2
        assert rows[0]["resource_id"] == "res-uuid-001"

    def test_queries_pending_status(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = []
        fetch_pending_items(mock_conn, batch_size=5)
        sql = mock_cur.execute.call_args.args[0].lower()
        assert "pending" in sql
        assert "enrichment_queue" in sql

    def test_respects_batch_size(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = []
        fetch_pending_items(mock_conn, batch_size=25)
        sql_args = mock_cur.execute.call_args.args
        # batch_size passed as param
        assert 25 in sql_args[1] or "25" in str(sql_args)


# ---------------------------------------------------------------------------
# build_agent_message
# ---------------------------------------------------------------------------

class TestBuildAgentMessage:
    def test_includes_title_and_url(self):
        msg = build_agent_message(QUEUE_ROW_1)
        text = msg["newMessage"]["parts"][0]["text"]
        assert "PRISMA 2020" in text
        assert "doi.org" in text

    def test_includes_resource_type(self):
        msg = build_agent_message(QUEUE_ROW_1)
        text = msg["newMessage"]["parts"][0]["text"]
        assert "article" in text.lower()

    def test_includes_methodology_tags(self):
        msg = build_agent_message(QUEUE_ROW_1)
        text = msg["newMessage"]["parts"][0]["text"]
        assert "SYN-01" in text

    def test_session_id_includes_resource_id(self):
        msg = build_agent_message(QUEUE_ROW_1)
        assert "res-uuid-001" in msg["sessionId"]

    def test_correct_app_and_user(self):
        msg = build_agent_message(QUEUE_ROW_1)
        assert msg["appName"] == "agents"
        assert msg["userId"] == "batch-runner"

    def test_missing_optional_fields_ok(self):
        row = {"queue_id": "q1", "resource_id": "r1", "resource_type": "book",
               "title": "A Book", "url": "https://example.com"}
        msg = build_agent_message(row)
        assert msg["newMessage"]["parts"][0]["text"]


# ---------------------------------------------------------------------------
# call_agent
# ---------------------------------------------------------------------------

class TestCallAgent:
    def test_posts_to_run_endpoint(self):
        with patch("scripts.batch.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status = MagicMock()
            mock_post.return_value.json.return_value = AGENT_RUN_RESPONSE
            call_agent(
                message=build_agent_message(QUEUE_ROW_1),
                agent_url="https://cothesis-agent.run.app",
                bearer_token="test-token",
            )
        url = mock_post.call_args.args[0]
        assert url.endswith("/run")

    def test_uses_bearer_auth(self):
        with patch("scripts.batch.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status = MagicMock()
            mock_post.return_value.json.return_value = AGENT_RUN_RESPONSE
            call_agent(
                message=build_agent_message(QUEUE_ROW_1),
                agent_url="https://cothesis-agent.run.app",
                bearer_token="my-token",
            )
        headers = mock_post.call_args.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer my-token"

    def test_returns_response_json(self):
        with patch("scripts.batch.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status = MagicMock()
            mock_post.return_value.json.return_value = AGENT_RUN_RESPONSE
            result = call_agent(
                message=build_agent_message(QUEUE_ROW_1),
                agent_url="https://cothesis-agent.run.app",
                bearer_token="t",
            )
        assert result == AGENT_RUN_RESPONSE


# ---------------------------------------------------------------------------
# mark_item_processing / complete / failed
# ---------------------------------------------------------------------------

class TestStatusUpdates:
    def test_mark_processing_sets_status(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mark_item_processing(mock_conn, "eq-uuid-001")
        sql = mock_cur.execute.call_args.args[0].lower()
        assert "processing" in sql

    def test_mark_complete_sets_status_and_timestamp(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mark_item_complete(mock_conn, "eq-uuid-001")
        sql = mock_cur.execute.call_args.args[0].lower()
        assert "complete" in sql

    def test_mark_failed_records_error(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mark_item_failed(mock_conn, "eq-uuid-001", "Vertex AI quota exceeded")
        sql = mock_cur.execute.call_args.args[0].lower()
        assert "failed" in sql
        params = mock_cur.execute.call_args.args[1]
        assert "Vertex AI quota exceeded" in str(params)


# ---------------------------------------------------------------------------
# run_batch integration
# ---------------------------------------------------------------------------

class TestRunBatch:
    def test_returns_batch_result(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [QUEUE_ROW_1]
        with patch("scripts.batch.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status = MagicMock()
            mock_post.return_value.json.return_value = AGENT_RUN_RESPONSE
            result = run_batch(
                conn=mock_conn,
                agent_url="https://cothesis-agent.run.app",
                bearer_token="t",
                batch_size=10,
            )
        assert isinstance(result, BatchResult)
        assert result.processed == 1
        assert result.failed == 0

    def test_dry_run_skips_agent_call(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [QUEUE_ROW_1, QUEUE_ROW_2]
        with patch("scripts.batch.httpx.post") as mock_post:
            result = run_batch(
                conn=mock_conn,
                agent_url="https://cothesis-agent.run.app",
                bearer_token="t",
                batch_size=10,
                dry_run=True,
            )
        mock_post.assert_not_called()
        assert result.processed == 0
        assert result.dry_run is True

    def test_marks_failed_on_agent_error(self):
        import httpx
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [QUEUE_ROW_1]
        with patch("scripts.batch.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=MagicMock()
            )
            result = run_batch(
                conn=mock_conn,
                agent_url="https://cothesis-agent.run.app",
                bearer_token="t",
                batch_size=10,
            )
        assert result.failed == 1
        assert result.processed == 0

    def test_no_items_returns_zero_result(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = []
        result = run_batch(
            conn=mock_conn,
            agent_url="https://cothesis-agent.run.app",
            bearer_token="t",
        )
        assert result.processed == 0
        assert result.failed == 0
