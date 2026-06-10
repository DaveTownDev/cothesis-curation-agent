"""Batch-delete Firestore pipeline collections for a clean re-run."""
from __future__ import annotations

import logging
from typing import Iterable

logger = logging.getLogger(__name__)

# In-flight and completed pipeline artefacts (keyed by resource_code or auto-id).
PIPELINE_COLLECTIONS: tuple[str, ...] = (
    "drafts",
    "draft_records",
    "review_queue",
    "pipeline_state",
)

# Curated / published copies written by approve + sync (not the live Compendium DB).
RESOURCES_COLLECTION = "resources"


def collections_to_clear(*, include_resources: bool = True) -> list[str]:
    names = list(PIPELINE_COLLECTIONS)
    if include_resources:
        names.append(RESOURCES_COLLECTION)
    return names


def clear_collections(
    db,
    *,
    include_resources: bool = True,
    collections: Iterable[str] | None = None,
    batch_size: int = 400,
) -> dict[str, int]:
    """Delete all documents in the given collections. Returns per-collection counts."""
    names = list(collections) if collections is not None else collections_to_clear(
        include_resources=include_resources,
    )
    deleted: dict[str, int] = {}
    for name in names:
        count = 0
        while True:
            docs = list(db.collection(name).limit(batch_size).stream())
            if not docs:
                break
            batch = db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            count += len(docs)
        deleted[name] = count
        logger.info("cleared %s: %d docs", name, count)
    return deleted
