"""Firestore client helpers for the curation pipeline."""
import os
from functools import lru_cache
from google.cloud import firestore

COLLECTION_DRAFTS = "drafts"
COLLECTION_RESOURCES = "resources"
COLLECTION_PIPELINE_STATE = "pipeline_state"
COLLECTION_REVIEW_QUEUE = "review_queue"


@lru_cache(maxsize=1)
def get_firestore_client() -> firestore.Client:
    return firestore.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])


def get_firestore_collection(collection_name: str) -> firestore.CollectionReference:
    return get_firestore_client().collection(collection_name)
