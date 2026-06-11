"""Firestore client helpers for the curation pipeline."""
import os

# gRPC aborts a forked CHILD process if forking happens after its threads start
# (google-auth credential refresh, c-ares DNS). Enable fork support so local
# batch/eval runs don't emit SIGABRT crash reports. Set before importing gRPC.
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "1")
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")

from functools import lru_cache
from google.cloud import firestore

COLLECTION_DRAFTS = "drafts"
COLLECTION_RESOURCES = "resources"
COLLECTION_PIPELINE_STATE = "pipeline_state"
COLLECTION_REVIEW_QUEUE = "review_queue"
COLLECTION_EVAL_FAILURE_BUCKET = "eval_failure_bucket"
COLLECTION_PROMPT_PROPOSALS = "prompt_proposals"
COLLECTION_PROMPT_LAB_RUNS = "prompt_lab_runs"


@lru_cache(maxsize=1)
def get_firestore_client() -> firestore.Client:
    return firestore.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])


def collection_name_for(collection_name: str) -> str:
    """Apply FIRESTORE_COLLECTION_PREFIX (if set) so non-prod runs are isolated."""
    return os.environ.get("FIRESTORE_COLLECTION_PREFIX", "") + collection_name


def get_firestore_collection(collection_name: str) -> firestore.CollectionReference:
    # FIRESTORE_COLLECTION_PREFIX isolates non-prod runs (e.g. ADK eval) from the
    # demo/prod collections: set it to "eval_" so the pipeline writes to
    # eval_review_queue / eval_drafts / … and never pollutes the real queue.
    return get_firestore_client().collection(collection_name_for(collection_name))
