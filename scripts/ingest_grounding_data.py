"""
Upload grounding data to Vertex AI Search.

Run: python scripts/ingest_grounding_data.py

Uploads:
  1. Methodology cards (data/methodologies/syn-01.md etc.) — 4 documents
  2. Seed resource summaries (data/resources_seed/compendium_demo_content.json)

The datastore must already exist (created in Day 1).
VERTEX_DATASTORE_ID must be set in .env.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASTORE_ID = os.environ["VERTEX_DATASTORE_ID"]
# e.g. projects/cothesis-curation-agent/locations/global/...
# Extract just the datastore short ID for the client
DATASTORE_SHORT_ID = DATASTORE_ID.split("/dataStores/")[-1]
LOCATION = "global"

PARENT = (
    f"projects/{PROJECT}/locations/{LOCATION}/collections/default_collection"
    f"/dataStores/{DATASTORE_SHORT_ID}/branches/default_branch"
)

WORKSPACE = Path(__file__).parent.parent


def get_client():
    from google.cloud import discoveryengine_v1 as discoveryengine
    return discoveryengine.DocumentServiceClient()


def upsert_document(client, document_id: str, title: str, content: str, uri: str = "") -> None:
    from google.cloud import discoveryengine_v1 as discoveryengine

    document = discoveryengine.Document(
        name=f"{PARENT}/documents/{document_id}",
        content=discoveryengine.Document.Content(
            raw_bytes=content.encode("utf-8"),
            mime_type="text/plain",
        ),
        json_data=json.dumps({"title": title, "uri": uri}),
    )

    try:
        # Try update first
        client.update_document(
            request=discoveryengine.UpdateDocumentRequest(
                document=document,
                allow_missing=True,
            )
        )
        print(f"  updated: {document_id}")
    except Exception:
        # Fall back to create
        try:
            client.create_document(
                request=discoveryengine.CreateDocumentRequest(
                    parent=PARENT,
                    document=discoveryengine.Document(
                        content=discoveryengine.Document.Content(
                            raw_bytes=content.encode("utf-8"),
                            mime_type="text/plain",
                        ),
                        json_data=json.dumps({"title": title, "uri": uri}),
                    ),
                    document_id=document_id,
                )
            )
            print(f"  created: {document_id}")
        except Exception as exc:
            print(f"  ERROR {document_id}: {exc}")


def ingest_methodology_cards(client) -> int:
    print("\n--- Methodology cards ---")
    cards = {
        "syn-01": "SYN-01 Narrative Systematic Review",
        "syn-02": "SYN-02 Scoping Review",
        "obs-01": "OBS-01 Retrospective Chart Review",
        "eval-01": "EVAL-01 Standards-Based Clinical Audit",
    }
    count = 0
    for code, title in cards.items():
        path = WORKSPACE / "data" / "methodologies" / f"{code}.md"
        if not path.exists():
            print(f"  SKIP (not found): {path}")
            continue
        content = path.read_text()
        upsert_document(client, document_id=code, title=title, content=content)
        count += 1
    return count


def ingest_seed_resources(client) -> int:
    print("\n--- Seed resources ---")
    seed_path = WORKSPACE / "data" / "resources_seed" / "compendium_demo_content.json"
    if not seed_path.exists():
        print("  SKIP: seed file not found")
        return 0

    with open(seed_path) as f:
        data = json.load(f)

    items = data.get("resources", data.get("items", data if isinstance(data, list) else []))
    count = 0
    for item in items:
        resource_type = item.get("resource_type", "unknown")
        title = item.get("title", "Untitled")
        short_desc = item.get("editorial_description", "")
        long_desc = item.get("editorial_description_long", item.get("summary", ""))
        content = f"# {title}\n\nType: {resource_type}\n\n{short_desc}\n\n{long_desc}"
        doc_id = f"seed-{resource_type}"
        url = item.get("url", "")
        upsert_document(client, document_id=doc_id, title=title, content=content, uri=url)
        count += 1
    return count


def main() -> None:
    print(f"Ingesting into: {DATASTORE_ID}")
    print(f"Parent branch: {PARENT}")

    client = get_client()

    n_cards = ingest_methodology_cards(client)
    n_seed = ingest_seed_resources(client)

    print(f"\nDone. Uploaded {n_cards} methodology cards + {n_seed} seed resources.")
    print("Indexing typically completes within 1-2 minutes.")
    print("Verify at: https://console.cloud.google.com/gen-app-builder/data-stores")


if __name__ == "__main__":
    main()
