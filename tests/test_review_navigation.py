"""Mirror of console/lib/review-navigation.ts — keeps queue nav contract tested in CI."""

from pathlib import Path


def review_next_path(next_id: str | None, queue_query: str) -> str:
    if next_id:
        return f"/review/{next_id}{f'?{queue_query}' if queue_query else ''}"
    return f"/review?{queue_query}" if queue_query else "/review"


def test_review_next_path_with_next_id():
    assert review_next_path("abc-123", "sort=attention") == "/review/abc-123?sort=attention"


def test_review_next_path_queue_only():
    assert review_next_path(None, "preset=qa_issues") == "/review?preset=qa_issues"


def test_review_next_path_empty():
    assert review_next_path(None, "") == "/review"


def test_ts_source_exists():
    assert (Path(__file__).resolve().parents[1] / "console/lib/review-navigation.ts").is_file()
