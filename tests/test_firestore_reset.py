"""Tests for agents.shared.firestore_reset."""
from __future__ import annotations

from unittest.mock import MagicMock, call

from agents.shared.firestore_reset import (
    PIPELINE_COLLECTIONS,
    RESOURCES_COLLECTION,
    clear_collections,
    collections_to_clear,
)


def test_collections_to_clear_includes_resources_by_default():
    names = collections_to_clear(include_resources=True)
    assert "review_queue" in names
    assert RESOURCES_COLLECTION in names


def test_collections_to_clear_can_omit_resources():
    names = collections_to_clear(include_resources=False)
    assert RESOURCES_COLLECTION not in names
    assert set(names) == set(PIPELINE_COLLECTIONS)


def test_clear_collections_deletes_in_batches():
    db = MagicMock()
    coll = MagicMock()
    db.collection.return_value = coll

    doc_a = MagicMock()
    doc_b = MagicMock()
    coll.limit.return_value.stream.side_effect = [[doc_a, doc_b], []]

    deleted = clear_collections(db, collections=["review_queue"], batch_size=400)

    assert deleted == {"review_queue": 2}
    db.batch.assert_called_once()
    batch = db.batch.return_value
    batch.delete.assert_has_calls([call(doc_a.reference), call(doc_b.reference)])
    batch.commit.assert_called_once()
