# Compendium Integration — Response from Compendium Team

**Date:** 2026-06-09  
**In reply to:** [COMPENDIUM_INTEGRATION.md](./COMPENDIUM_INTEGRATION.md)  
**Full technical detail:** See also `compendium-web/docs/CURATION_AGENT_HANDOFF.md` in the Compendium repo

---

## Status: Ready to re-sync

Compendium has deployed changes addressing all P0 items from our handoff. **No changes required to `compendium_bridge.py` or `compendium-sync.ts` field mapping.**

### What's fixed on Compendium side

| Your ask | Status |
|---|---|
| §7.1 Per-resource `resource_id` + `public_url` in POST response | ✅ Done |
| §7.2 Skip LLM re-classify for `source_tool: claude` + platform codes | ✅ Done |
| §7.3 Bearer auth | ✅ Confirmed (keep using `Authorization: Bearer`) |
| §7.4 Dedup behaviour | ✅ Documented (URL/DOI/ISBN dedup; re-sync safe) |
| §7.5 Skip enrichment for ratified payloads | ✅ Done |
| Empty content pages | ✅ Fixed (Neo4j field mapping + taxonomy query fixes) |

### POST response shape (new)

```json
{
  "success": true,
  "import_batch_id": "uuid",
  "resources": [
    {
      "resource_id": "uuid",
      "compendium_id": "uuid",
      "public_url": "https://…/library/resource/{uuid}",
      "compendium_url": "https://…/library/resource/{uuid}",
      "url": "…",
      "title": "…"
    }
  ]
}
```

Your existing response parser should work — we emit all aliases you check for.

### URL correction

Live resource pages: **`/library/resource/{resource_id}`** (singular)

Your fallback using `/library/resources/{id}` (plural) will 404. Prefer `public_url` from the API response.

### Action required on agent side

1. **Re-sync all published resources** from the HITL console (Published page → retry sync)
   - Previous syncs marked success but left `compendium_id` / `compendium_url` null
   - New sync will populate both immediately

2. **No bridge code changes needed** unless you want to fix the URL fallback constructor (optional)

3. **Verify workers are running** on Compendium Railway (`pnpm workers`) — without them, IDs return but Neo4j nodes aren't created until queue processes

### Batch status polling

```
GET {COMPENDIUM_IMPORT_URL}/api/import?batch_id={uuid}
```

Now returns `resources[]` with IDs/URLs plus pipeline counters.

### Fields we map from your payload

| You send | Appears on Compendium page |
|---|---|
| `description` | Editor's note |
| `discovery_context` | Long description |
| `methodology_tags` (SYN-01, …) | Methodology chips + taxonomy links |
| `specialty_tags` | Specialty relationships |
| `year`, `authors`, `journal_name`, etc. | Sidebar / cards |

Still Firestore-only unless you extend the bridge: `quality_score`, `editorial_badges`, `stage_codes`.

---

*Deployed via compendium-web master → Railway GitHub Actions, 2026-06-09*
