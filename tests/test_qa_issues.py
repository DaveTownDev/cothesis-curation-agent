"""Mirror of console/lib/qa-issues.ts — QA triage helpers for CI."""

from __future__ import annotations

from pathlib import Path


def has_qa_issues(qa: dict | None) -> bool:
    if not qa:
        return False
    sv = qa.get("source_verdict")
    if sv in ("fail", "warn"):
        return True
    dq = qa.get("data_quality")
    if dq in ("fail", "warn"):
        return True
    url = qa.get("url_status")
    if url in ("dead", "unreachable"):
        return True
    return False


def qa_display_verdict(qa: dict | None) -> str:
    if not qa:
        return "pending"
    if qa.get("source_verdict") == "fail" or qa.get("data_quality") == "fail":
        return "fail"
    if (
        qa.get("source_verdict") == "warn"
        or qa.get("data_quality") == "warn"
        or qa.get("url_status") in ("dead", "unreachable")
    ):
        return "warn"
    if qa.get("source_verdict") == "pass" or qa.get("data_quality") == "ok":
        return "pass"
    return "pending"


def test_qa_issues_includes_data_quality_fail():
    assert has_qa_issues({"data_quality": "fail", "url_status": "live"})


def test_qa_issues_includes_dead_url():
    assert has_qa_issues({"data_quality": "ok", "url_status": "dead"})


def test_qa_issues_source_only_still_works():
    assert has_qa_issues({"source_verdict": "warn"})


def test_qa_issues_ok_pass_is_not_issue():
    assert not has_qa_issues({"source_verdict": "pass", "data_quality": "ok"})


def test_qa_display_verdict_prefers_fail():
    assert qa_display_verdict({"source_verdict": "pass", "data_quality": "fail"}) == "fail"


def test_ts_mirror_exists():
    assert (Path(__file__).resolve().parents[1] / "console/lib/qa-issues.ts").is_file()
