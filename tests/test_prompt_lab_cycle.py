"""Integration test: mock Firestore failure bucket → proposal → benchmark gate."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from agents.shared.firestore_schemas import prompt_lab_run_to_firestore, prompt_proposal_to_firestore
from agents.shared.firestore_utils import (
    COLLECTION_EVAL_FAILURE_BUCKET,
    COLLECTION_PROMPT_LAB_RUNS,
    COLLECTION_PROMPT_PROPOSALS,
    collection_name_for,
)


class _DocRef:
    def __init__(self, store: dict, coll: str, doc_id: str):
        self._store = store
        self._coll = coll
        self._doc_id = doc_id

    def update(self, data: dict) -> None:
        self._store.setdefault(self._coll, {}).setdefault(self._doc_id, {}).update(data)


class _Query:
    def __init__(self, store: dict, coll: str, filters: list, order_field: str | None, limit: int | None):
        self._store = store
        self._coll = coll
        self._filters = filters
        self._order_field = order_field
        self._limit = limit

    def where(self, field: str, op: str, value: Any) -> _Query:
        return _Query(
            self._store,
            self._coll,
            self._filters + [(field, op, value)],
            self._order_field,
            self._limit,
        )

    def order_by(self, field: str, direction: str = "ASCENDING") -> _Query:
        return _Query(self._store, self._coll, self._filters, field, self._limit)

    def limit(self, n: int) -> _Query:
        return _Query(self._store, self._coll, self._filters, self._order_field, n)

    def stream(self):
        docs = list(self._store.get(self._coll, {}).items())

        def _matches(doc_id: str, data: dict) -> bool:
            for field, op, value in self._filters:
                if op == "==" and data.get(field) != value:
                    return False
            return True

        filtered = [(did, d) for did, d in docs if _matches(did, d)]
        if self._order_field:
            filtered.sort(key=lambda x: x[1].get(self._order_field, ""), reverse=True)
        if self._limit is not None:
            filtered = filtered[: self._limit]

        for doc_id, data in filtered:
            yield type("Snap", (), {"id": doc_id, "to_dict": lambda self, d=data: dict(d)})()


class _Collection:
    def __init__(self, store: dict, name: str):
        self._store = store
        self._name = name

    def where(self, field: str, op: str, value: Any) -> _Query:
        return _Query(self._store, self._name, [(field, op, value)], None, None)

    def document(self, doc_id: str) -> _DocRef:
        return _DocRef(self._store, self._name, doc_id)

    def add(self, data: dict):
        coll = self._store.setdefault(self._name, {})
        doc_id = f"auto-{len(coll) + 1}"
        coll[doc_id] = dict(data)
        return (None, type("Ref", (), {"id": doc_id})())


class MockFirestore:
    def __init__(self):
        self._store: dict[str, dict[str, dict]] = {}

    def collection(self, name: str) -> _Collection:
        return _Collection(self._store, name)

    def seed_failure(self, doc_id: str, **fields) -> None:
        coll = collection_name_for(COLLECTION_EVAL_FAILURE_BUCKET)
        self._store.setdefault(coll, {})[doc_id] = {
            "resource_code": fields.get("resource_code", "RES-001"),
            "agent": fields.get("agent", "classification"),
            "field": fields.get("field", "methodology_codes"),
            "human_label": fields.get("human_label", "Wrong code"),
            "prompt_version": fields.get("prompt_version", "classification@1.0.0"),
            "created_at": fields.get(
                "created_at",
                datetime.now(timezone.utc).isoformat(),
            ),
            "origin": fields.get("origin", "hitl_flag"),
            "consumed_by_lab_run_id": fields.get("consumed_by_lab_run_id"),
        }

    def failures(self) -> dict:
        return self._store.get(collection_name_for(COLLECTION_EVAL_FAILURE_BUCKET), {})

    def proposals(self) -> dict:
        return self._store.get(collection_name_for(COLLECTION_PROMPT_PROPOSALS), {})

    def lab_runs(self) -> dict:
        return self._store.get(collection_name_for(COLLECTION_PROMPT_LAB_RUNS), {})


@pytest.fixture
def mock_db():
    return MockFirestore()


@pytest.fixture
def fixture_failures(mock_db):
    mock_db.seed_failure("fb-1", human_label="Software should omit methodology")
    mock_db.seed_failure("fb-2", field="discipline_codes", human_label="Use PSYCH not slug")
    return mock_db


def test_full_cycle_writes_proposal_and_consumes_failures(fixture_failures):
    from scripts.prompt_eval_loop import run_lab_cycle

    def fake_benchmark(subset: int, check_regression: bool) -> dict:
        return {
            "ok": True,
            "exit_code": 0,
            "subset": subset,
            "eval_delta": {
                "baseline_path": "eval/baseline.json",
                "subset_cases": subset,
                "passed": True,
                "rubric_scores": {},
                "response_match_score": 0.18,
                "notes": "mock gate",
            },
        }

    result = run_lab_cycle(
        max_cases=10,
        db=fixture_failures,
        benchmark_runner=fake_benchmark,
    )

    assert result["ok"] is True
    assert result["proposal_id"]
    assert result["failure_count"] == 2

    proposals = fixture_failures.proposals()
    assert len(proposals) == 1
    _pid, proposal = next(iter(proposals.items()))
    assert proposal["status"] == "pending"
    assert proposal["target_prompt_file"] == "agents/prompts/classification.md"
    assert proposal["unified_diff"].startswith("--- a/agents/prompts/")
    assert set(proposal["failure_bucket_ids"]) == {"fb-1", "fb-2"}
    assert proposal["eval_delta"]["passed"] is True
    assert proposal["lab_run_id"] == result["lab_run_id"]

    for fid in ("fb-1", "fb-2"):
        assert fixture_failures.failures()[fid]["consumed_by_lab_run_id"] == result["lab_run_id"]

    runs = fixture_failures.lab_runs()
    run = runs[result["lab_run_id"]]
    assert run["status"] == "succeeded"
    assert run["proposal_ids"] == [result["proposal_id"]]
    assert run["max_cases"] == 10


def test_cycle_skips_when_no_pending_failures(mock_db):
    from scripts.prompt_eval_loop import run_lab_cycle

    result = run_lab_cycle(db=mock_db)
    assert result["skipped"] is True
    assert len(mock_db.proposals()) == 0


def test_benchmark_failure_marks_lab_run_failed(fixture_failures):
    from scripts.prompt_eval_loop import run_lab_cycle

    def failing_gate(subset: int, check_regression: bool) -> dict:
        return {
            "ok": False,
            "exit_code": 1,
            "subset": subset,
            "eval_delta": {
                "baseline_path": "eval/baseline.json",
                "subset_cases": subset,
                "passed": False,
                "notes": "regression",
            },
        }

    result = run_lab_cycle(
        db=fixture_failures,
        benchmark_runner=failing_gate,
    )

    assert result["ok"] is False
    assert len(fixture_failures.proposals()) == 1
    run = fixture_failures.lab_runs()[result["lab_run_id"]]
    assert run["status"] == "failed"
    assert run["error"] == "benchmark gate failed"


def test_dry_run_no_firestore_writes(fixture_failures):
    from scripts.prompt_eval_loop import run_lab_cycle

    result = run_lab_cycle(dry_run=True, db=fixture_failures)
    assert result["dry_run"] is True
    assert result["failure_count"] == 2
    assert len(fixture_failures.proposals()) == 0
    assert fixture_failures.failures()["fb-1"]["consumed_by_lab_run_id"] is None


def test_firestore_schema_round_trip_on_proposal():
    from agents.shared.firestore_schemas import EvalDelta, PromptProposalDoc

    doc = PromptProposalDoc(
        target_prompt_file="agents/prompts/classification.md",
        unified_diff="--- a/x\n+++ b/x\n",
        rationale="test",
        failure_bucket_ids=["fb1"],
        eval_delta=EvalDelta(subset_cases=2, passed=True),
        lab_run_id="run-1",
    )
    payload = prompt_proposal_to_firestore(doc)
    assert payload["status"] == "pending"
    assert json.loads(json.dumps(payload))["eval_delta"]["passed"] is True


def test_lab_run_schema_round_trip():
    from agents.shared.firestore_schemas import PromptLabRunDoc

    doc = PromptLabRunDoc(max_cases=10, failure_bucket_ids=["a"])
    payload = prompt_lab_run_to_firestore(doc)
    assert payload["max_cases"] == 10
