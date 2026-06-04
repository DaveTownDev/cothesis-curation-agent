"""
Human-in-the-loop helpers.

When the arbiter routes review_needed, the pipeline writes to the
Firestore `review_queue` collection and stops for that resource.
The human console (Day 5) reads from review_queue, approves/rejects,
and writes back to `resources`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from agents.shared.firestore_utils import get_firestore_collection, COLLECTION_REVIEW_QUEUE

logger = logging.getLogger(__name__)


def write_review_queue_item(
    resource_code: str,
    routing: str,
    reason: str,
    panel_result: dict,
    draft_record: dict,
) -> str:
    """
    Write an item to the Firestore review_queue collection.
    Returns the Firestore document ID.
    """
    col = get_firestore_collection(COLLECTION_REVIEW_QUEUE)
    item = {
        "resource_code": resource_code,
        "routing": routing,
        "reason": reason,
        "panel_result": panel_result,
        "draft_record": draft_record,
        "status": "pending",
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    _, doc_ref = col.add(item)
    logger.info(
        "Review queue item written: resource=%s routing=%s doc_id=%s",
        resource_code, routing, doc_ref.id,
    )
    return doc_ref.id


def get_review_status(resource_code: str) -> str:
    """
    Check the status of a resource in the review queue.
    Returns: 'pending' | 'approved' | 'rejected' | 'not_found'
    """
    col = get_firestore_collection(COLLECTION_REVIEW_QUEUE)
    try:
        docs = col.where("resource_code", "==", resource_code).limit(1).stream()
        for doc in docs:
            return doc.get("status", "pending")
        return "not_found"
    except Exception as exc:
        logger.warning("Failed to get review status for %r: %s", resource_code, exc)
        return "not_found"
