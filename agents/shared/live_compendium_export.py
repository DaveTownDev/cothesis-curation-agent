"""
Export live Compendium resources for re-processing through the curation pipeline.

Sources (in priority order for ``fetch_live_resources``):
  1. Railway Postgres ``compendium.import_candidates`` (DATABASE_PUBLIC_URL)
  2. Neo4j HTTP API (NEO4J_HTTP_URL + NEO4J_USERNAME + NEO4J_PASSWORD)
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_NEO4J_HTTP = "https://neo4j-production-98cf.up.railway.app"
DEFAULT_COMPENDIUM_BASE = "https://compendium-web-production.up.railway.app"

_LIVE_STATUSES_PG = (
    "auto_accepted",
    "human_accepted",
    "enrichment_queued",
    "enriched",
    "accepted",
)

_NEO4J_PAGE = 200


def _pascal_to_snake(value: str | None) -> str:
    if not value:
        return "article"
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def compendium_public_url(resource_id: str, base_url: str | None = None) -> str:
    base = (base_url or os.environ.get("COMPENDIUM_BASE_URL") or DEFAULT_COMPENDIUM_BASE).rstrip("/")
    return f"{base}/library/resource/{resource_id}"


def to_pipeline_input(record: dict[str, Any]) -> dict[str, Any]:
    """Map a live Compendium export row → ``run_pipeline`` input dict."""
    resource_type = record.get("resource_type") or record.get("classified_type") or "article"
    if resource_type and resource_type[0].isupper():
        resource_type = _pascal_to_snake(str(resource_type))

    methodology = record.get("methodology_tags") or record.get("methodology_codes") or []
    if isinstance(methodology, str):
        methodology = [methodology]

    out: dict[str, Any] = {
        "title": record.get("title") or "",
        "url": record.get("url") or "",
        "description": record.get("description") or record.get("editorial_description") or "",
        "resource_type": resource_type,
        "methodology_tags": list(methodology),
        "doi": record.get("doi"),
        "pmid": record.get("pmid"),
        "isbn": record.get("isbn"),
    }
    rid = record.get("resource_id") or record.get("compendium_id")
    if rid:
        out["compendium_id"] = rid
        out["compendium_url"] = record.get("compendium_url") or record.get("public_url") or compendium_public_url(str(rid))
    return out


def normalize_export_row(row: dict[str, Any]) -> dict[str, Any]:
    """Ensure consistent keys on an export record."""
    rid = row.get("resource_id") or row.get("compendium_id")
    normalized = dict(row)
    if rid:
        normalized["resource_id"] = str(rid)
        normalized.setdefault("compendium_url", compendium_public_url(str(rid)))
    if normalized.get("resource_type"):
        rt = normalized["resource_type"]
        if isinstance(rt, str) and rt[0].isupper():
            normalized["resource_type"] = _pascal_to_snake(rt)
    return normalized


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------

_PG_SQL = """
    SELECT DISTINCT ON (ic.resource_id)
        ic.resource_id,
        ic.url,
        ic.title,
        ic.description,
        COALESCE(ic.classified_type, ic.raw_data->>'resource_type') AS resource_type,
        ic.methodology_tags,
        ic.specialty_tags,
        ic.doi,
        ic.pmid,
        ic.isbn,
        ic.access_type,
        ic.status,
        ic.raw_data
    FROM compendium.import_candidates ic
    WHERE ic.resource_id IS NOT NULL
      AND ic.url IS NOT NULL
      AND ic.title IS NOT NULL
      AND ic.status = ANY(%s)
    ORDER BY ic.resource_id, ic.imported_at DESC
"""


def fetch_from_postgres(
    conn: Any,
    *,
    limit: int = 0,
    statuses: tuple[str, ...] = _LIVE_STATUSES_PG,
) -> list[dict[str, Any]]:
    sql = _PG_SQL
    params: list[Any] = [list(statuses)]
    if limit > 0:
        sql = f"{_PG_SQL}\nLIMIT %s"
        params.append(limit)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        if rec.get("raw_data") and isinstance(rec["raw_data"], str):
            try:
                rec["raw_data"] = json.loads(rec["raw_data"])
            except json.JSONDecodeError:
                pass
        out.append(normalize_export_row(rec))
    logger.info("Postgres export: %d resources", len(out))
    return out


# ---------------------------------------------------------------------------
# Neo4j HTTP
# ---------------------------------------------------------------------------

def _neo4j_http_url() -> str:
    return (os.environ.get("NEO4J_HTTP_URL") or DEFAULT_NEO4J_HTTP).rstrip("/")


def _neo4j_auth_header() -> str:
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def neo4j_query(cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"statements": [{"statement": cypher}]}
    if params:
        payload["statements"][0]["parameters"] = params

    req = urllib.request.Request(
        f"{_neo4j_http_url()}/db/neo4j/tx/commit",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": _neo4j_auth_header(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise RuntimeError(f"Neo4j HTTP {exc.code}: {detail}") from exc

    errors = body.get("errors") or []
    if errors:
        err = errors[0]
        raise RuntimeError(f"Neo4j error {err.get('code')}: {err.get('message')}")

    results = body.get("results") or []
    if not results:
        return []

    columns = results[0].get("columns") or []
    rows = results[0].get("data") or []
    parsed: list[dict[str, Any]] = []
    for item in rows:
        row_vals = item.get("row") or []
        parsed.append(dict(zip(columns, row_vals)))
    return parsed


def fetch_from_neo4j(*, limit: int = 0) -> list[dict[str, Any]]:
    """Paginate all enriched CompendiumResource nodes."""
    out: list[dict[str, Any]] = []
    skip = 0
    cap = limit if limit > 0 else 10_000_000

    while len(out) < cap:
        page_limit = min(_NEO4J_PAGE, cap - len(out))
        rows = neo4j_query(
            """
            MATCH (r:CompendiumResource)
            WHERE r.status IN ['enriched', 'pending_enrichment', 'enrichment_pending']
              AND r.url IS NOT NULL AND r.title IS NOT NULL
            RETURN r.resource_id AS resource_id,
                   r.title AS title,
                   r.url AS url,
                   r.resource_type AS resource_type,
                   r.description AS description,
                   r.methodology_tags AS methodology_tags,
                   r.specialty_tags AS specialty_tags,
                   r.doi AS doi,
                   r.pmid AS pmid,
                   r.isbn AS isbn,
                   r.access_type AS access_type,
                   r.status AS neo4j_status
            ORDER BY r.resource_id
            SKIP $skip
            LIMIT $limit
            """,
            {"skip": skip, "limit": page_limit},
        )
        if not rows:
            break
        for row in rows:
            out.append(normalize_export_row(row))
        skip += len(rows)
        if len(rows) < page_limit:
            break

    logger.info("Neo4j export: %d resources", len(out))
    return out


def fetch_live_resources(
    *,
    source: str = "auto",
    limit: int = 0,
    pg_conn: Any | None = None,
) -> list[dict[str, Any]]:
    """
    Export live resources. ``source``: auto | postgres | neo4j.
    """
    if source in ("auto", "postgres"):
        conn = pg_conn
        if conn is None:
            db_url = os.environ.get("DATABASE_PUBLIC_URL", "")
            if db_url:
                import psycopg2
                import psycopg2.extras

                conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
                try:
                    return fetch_from_postgres(conn, limit=limit)
                finally:
                    conn.close()
        else:
            return fetch_from_postgres(conn, limit=limit)

    if source in ("auto", "neo4j"):
        if not os.environ.get("NEO4J_PASSWORD") and source == "neo4j":
            raise RuntimeError("NEO4J_PASSWORD required for neo4j source")
        try:
            return fetch_from_neo4j(limit=limit)
        except Exception as exc:
            if source == "neo4j":
                raise
            logger.warning("Neo4j export failed (%s); no postgres connection available", exc)

    raise RuntimeError(
        "No live export source available. Set DATABASE_PUBLIC_URL (preferred) or NEO4J_PASSWORD."
    )


def write_export_json(path: str, records: list[dict[str, Any]], *, source: str) -> None:
    from datetime import datetime, timezone
    from pathlib import Path

    doc = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "count": len(records),
        "resources": records,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
