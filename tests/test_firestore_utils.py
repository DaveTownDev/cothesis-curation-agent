"""FIRESTORE_COLLECTION_PREFIX isolates non-prod (eval) runs from prod collections."""
import importlib


def test_no_prefix_by_default(monkeypatch):
    monkeypatch.delenv("FIRESTORE_COLLECTION_PREFIX", raising=False)
    from agents.shared import firestore_utils as F
    assert F.collection_name_for("review_queue") == "review_queue"
    assert F.collection_name_for("drafts") == "drafts"


def test_prefix_applied(monkeypatch):
    monkeypatch.setenv("FIRESTORE_COLLECTION_PREFIX", "eval_")
    from agents.shared import firestore_utils as F
    assert F.collection_name_for("review_queue") == "eval_review_queue"
    assert F.collection_name_for("draft_records") == "eval_draft_records"
    assert F.collection_name_for("pipeline_state") == "eval_pipeline_state"
