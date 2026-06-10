# Compendium → CoThesis Curation Agent — Integration Response

**Audience:** CoThesis Curation Agent team (HITL console + ADK pipeline)  
**From:** Compendium engineering (`compendium-web`)  
**Date:** 2026-06-09  
**In reply to:** [`docs/COMPENDIUM_INTEGRATION.md`](COMPENDIUM_INTEGRATION.md)  
**Source:** `compendium-web/docs/CURATION_AGENT_HANDOFF.md` (mirror in this repo)

---

## 1. Executive summary

Compendium has implemented the P0/P1/P2 items from our handoff. Ratified agent payloads (`source_tool: "claude"`) now:

1. **Return per-resource IDs and URLs synchronously** from `POST /api/import/json`
2. **Skip LLM re-classification** — platform methodology codes (SYN-01, OBS-01, …) are preserved
3. **Skip redundant enrichment** — human-ratified editorial copy is written directly to Neo4j
4. **Render correctly on the website** — field mapping from Neo4j → frontend is fixed

Our bridge (`compendium_bridge.py` / `compendium-sync.ts`) requires **no schema changes**. **Re-sync** published resources from the console Published page (or CLI) to populate `compendium_id` and `compendium_url` on records synced under the old batch-only API.

**Agent-side updates (2026-06-09):**

- URL fallback fixed: `/library/resource/{id}` (singular), not `/library/resources/`
- Re-sync enabled when `compendium_synced_at` is set but `compendium_id` / `compendium_url` are missing

---

## 2. Answers to our §7 asks

### §7.1 Per-resource response fields — **DONE**

`POST /api/import/json` now returns:

```json
{
  "success": true,
  "import_batch_id": "uuid",
  "batch_id": "uuid",
  "stored_count": 1,
  "skipped_count": 0,
  "resources": [
    {
      "resource_id": "uuid",
      "compendium_id": "uuid",
      "public_url": "https://compendium-web-production.up.railway.app/library/resource/{uuid}",
      "compendium_url": "https://compendium-web-production.up.railway.app/library/resource/{uuid}",
      "url": "https://doi.org/10.1136/bmj.n71",
      "title": "PRISMA 2020 statement…"
    }
  ]
}
```

**Aliases:** Both `resource_id`/`compendium_id` and `public_url`/`compendium_url` — our existing response parser works without changes.

**URL shape:** Live pages are at `/library/resource/{resource_id}` (singular). Prefer `public_url` from the API response.

**Async polling:** `GET /api/import?batch_id={uuid}` includes a `resources[]` array once candidates are stored.

### §7.2 Classify worker outdated — **DONE**

For `source_tool: "claude"|"manus"` with editorial `description` and platform `methodology_tags` (`^[A-Z]{2,6}-\d{2}$`) → **LLM classification skipped**. Legacy RS-/OD- prompt not invoked.

### §7.3 Auth header — **CONFIRMED**

| Header | Value |
|---|---|
| `Authorization` | `Bearer {IMPORT_API_KEY}` ← **keep using this** |
| `x-import-key` | `{IMPORT_API_KEY}` ← legacy compat |

### §7.4 Idempotency / dedup — **DOCUMENTED**

| Scenario | Behaviour |
|---|---|
| Duplicate URL within same batch | Skipped; `skipped_count` incremented |
| Re-POST same URL in new batch | Dedup marks duplicate; no new Neo4j node |
| Agent retry after sync error | Re-POST safe |
| Stable external ID (`resource_code`) | **Not yet supported** — dedup on URL/DOI/ISBN |

### §7.5 Enrichment skip path — **DONE**

Trusted upstream (`source_tool: claude|manus`) maps editorial fields directly to Neo4j; enrichment LLM skipped; status `enriched`.

| ImportCandidate field | Neo4j / website |
|---|---|
| `description` | `editorial_description` / Editor's note |
| `discovery_context` | `editorial_description_long` |
| `methodology_tags` | `methodology_tags` + `USES_METHODOLOGY` edges |
| `specialty_tags` | `specialty_tags` + `RELEVANT_TO_SPECIALTY` edges |

**Not mapped (unless we extend bridge):** `quality_score`, `editorial_badges`, `stage_codes`, `skill_codes`.

---

## 3. What we should do now

1. **Re-sync the 39 records** synced under the old API (batch-only response) — Published page → select all needing sync → **Sync to Compendium**, or:
   ```bash
   GOOGLE_CLOUD_PROJECT=cothesis-curation-agent python -m scripts.sync_to_compendium --batch-size 50
   ```
2. **Verify one record:** approve in console → toast should show **Open in Compendium →** with live URL.
3. **Redeploy console** after agent-side re-sync logic changes (if not already live).

---

## 4. Traceability — old batches (re-sync recommended)

| import_batch_id | Notes |
|---|---|
| `f7e8e345-6ed1-4e94-9739-8b9210cf93b5` | Single SYN-02 scoping review |
| `5a9b3861-a498-4eb9-a2cb-e2f6e1d52cf3` | Bulk chunk 1 (21) |
| `1d65dbd9-61ee-4a0d-8422-37e78ffe79fa` | Bulk chunk 2 (14) |
| `a21fd74f-e01f-42c8-9f71-d0194169b866` | Bulk chunk 3 (11) |

Ingested under old API (batch-only, LLM re-classify). Re-sync from Firestore for correct behaviour.

---

## 5. Open items (future)

| Item | Priority | Notes |
|---|---|---|
| `resource_code` dedup key | P2 | Tell Compendium field name if we want cross-system matching |
| Pre-populate `quality_score` / badges | P2 | Extend bridge; Compendium maps to Neo4j + UI |
| Webhook on accept complete | P3 | Alternative to `GET /api/import?batch_id=` |
| Backfill script for old batches | P1 ops | Compendium can requeue if needed |

---

*Questions → Compendium engineering. Outbound handoff: [`docs/COMPENDIUM_INTEGRATION.md`](COMPENDIUM_INTEGRATION.md)*
