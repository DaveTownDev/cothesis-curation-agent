"""Sync live Compendium catalog resources into Postgres ``compendium.enrichment_queue``."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_CODE = "curation_agent_requeue"
DEFAULT_PRIORITY = 5
DEFAULT_MAX_RETRIES = 3


def _pascal_type(value: str | None) -> str:
    """Match enrichment_queue convention (e.g. Article, ReportingGuideline)."""
    if not value:
        return "Article"
    if value[0].isupper() and "_" not in value:
        return value
    parts = value.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts if p)


def merge_live_catalog(
    *,
    postgres_rows: list[dict[str, Any]],
    neo4j_rows: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Union live catalog rows by ``resource_id``.

  Postgres (import_candidates) is authoritative for metadata; Neo4j adds any
  public-site resources missing from Postgres.
    """
    catalog: dict[str, dict[str, Any]] = {}
    for row in postgres_rows:
        rid = row.get("resource_id") or row.get("compendium_id")
        if rid:
            catalog[str(rid)] = row
    for row in neo4j_rows or []:
        rid = row.get("resource_id") or row.get("compendium_id")
        if rid and str(rid) not in catalog:
            catalog[str(rid)] = row
    return catalog


def fetch_live_catalog(
    conn: Any | None = None,
    *,
    source: str = "merge",
    limit: int = 0,
) -> dict[str, dict[str, Any]]:
    """Load live catalog from Postgres and/or Neo4j (public library backing stores)."""
    import os

    from agents.shared.live_compendium_export import (
        fetch_from_neo4j,
        fetch_from_postgres,
    )

    pg_rows: list[dict[str, Any]] = []
    neo_rows: list[dict[str, Any]] | None = None

    if source in ("auto", "merge", "postgres"):
        if conn is not None:
            pg_rows = fetch_from_postgres(conn, limit=limit)
        else:
            db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
            if db_url:
                import psycopg2
                import psycopg2.extras

                pg_conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
                try:
                    pg_rows = fetch_from_postgres(pg_conn, limit=limit)
                finally:
                    pg_conn.close()

    if source in ("auto", "merge", "neo4j"):
        try:
            neo_rows = fetch_from_neo4j(limit=limit)
        except Exception as exc:
            if source == "neo4j":
                raise
            logger.warning("Neo4j catalog fetch skipped: %s", exc)

    if source == "postgres":
        return merge_live_catalog(postgres_rows=pg_rows, neo4j_rows=None)
    if source == "neo4j":
        return merge_live_catalog(postgres_rows=[], neo4j_rows=neo_rows or [])
    return merge_live_catalog(postgres_rows=pg_rows, neo4j_rows=neo_rows)


def _resource_type_for_row(row: dict[str, Any]) -> str:
    raw = row.get("resource_type") or row.get("classified_type") or "article"
    return _pascal_type(str(raw))


def preview_sync(conn: Any, catalog: dict[str, dict[str, Any]]) -> dict[str, int]:
    """Count insert vs requeue vs unchanged without writing."""
    existing = _load_queue_index(conn)
    insert = 0
    requeue = 0
    unchanged = 0
    for rid in catalog:
        row = existing.get(rid)
        if row is None:
            insert += 1
        elif row["status"] == "pending":
            unchanged += 1
        else:
            requeue += 1
    return {
        "catalog": len(catalog),
        "insert": insert,
        "requeue": requeue,
        "unchanged_pending": unchanged,
    }


def _load_queue_index(conn: Any) -> dict[str, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT resource_id::text, status, id::text AS queue_id
            FROM compendium.enrichment_queue
            """,
        )
        rows = cur.fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        data = dict(row)
        out[data["resource_id"]] = data
    return out


def sync_to_enrichment_queue(
    conn: Any,
    catalog: dict[str, dict[str, Any]],
    *,
    reset_existing: bool = True,
    source_code: str = DEFAULT_SOURCE_CODE,
) -> dict[str, int]:
    """
    Ensure each catalog resource has exactly one ``pending`` enrichment_queue row.

    When ``reset_existing`` is true (default), deletes all existing queue rows for
    catalog ``resource_id`` values first — avoids ``unique_queue_item`` conflicts
  when multiple rows exist per resource (different source_code / status).

    Also sets ``import_candidates.status = 'enrichment_queued'`` for matched resources.
    """
    existing = _load_queue_index(conn)
    stats = {
        "deleted": 0,
        "inserted": 0,
        "requeued": 0,
        "unchanged_pending": 0,
        "import_candidates_updated": 0,
    }
    now = datetime.now(timezone.utc)
    resource_ids = list(catalog.keys())

    to_insert: list[tuple] = []
    for rid, row in catalog.items():
        queue_row = existing.get(rid)
        if queue_row is None:
            to_insert.append(
                (
                    str(uuid.uuid4()),
                    rid,
                    _resource_type_for_row(row),
                    source_code,
                    DEFAULT_PRIORITY,
                    now,
                    DEFAULT_MAX_RETRIES,
                ),
            )
        elif queue_row["status"] == "pending" and not reset_existing:
            stats["unchanged_pending"] += 1
        else:
            to_insert.append(
                (
                    str(uuid.uuid4()),
                    rid,
                    _resource_type_for_row(row),
                    source_code,
                    DEFAULT_PRIORITY,
                    now,
                    DEFAULT_MAX_RETRIES,
                ),
            )
            if queue_row and queue_row["status"] != "pending":
                stats["requeued"] += 1

    with conn.cursor() as cur:
        if reset_existing and resource_ids:
            cur.execute(
                "DELETE FROM compendium.enrichment_queue WHERE resource_id = ANY(%s::uuid[])",
                (resource_ids,),
            )
            stats["deleted"] = cur.rowcount
            stats["requeued"] = stats["deleted"]  # replaced rows count as requeued

        if to_insert:
            cur.executemany(
                """
                INSERT INTO compendium.enrichment_queue (
                    id, resource_id, resource_type, source_code,
                    priority, status, scheduled_at, retry_count, max_retries
                ) VALUES (%s, %s, %s, %s, %s, 'pending', %s, 0, %s)
                """,
                to_insert,
            )
            stats["inserted"] = len(to_insert)

        if catalog:
            cur.execute(
                """
                UPDATE compendium.import_candidates
                SET status = 'enrichment_queued'
                WHERE resource_id = ANY(%s::uuid[])
                  AND status NOT IN ('duplicate', 'human_rejected', 'auto_excluded')
                """,
                (resource_ids,),
            )
            stats["import_candidates_updated"] = cur.rowcount

    conn.commit()
    return stats
