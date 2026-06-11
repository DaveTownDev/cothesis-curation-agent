# Ingestion / Enrichment Agent → compendium-web Handover

**Audience:** Engineers building and maintaining the standalone ingestion/enrichment agent (separate build) that POSTs ratified resources to compendium-web.

**Purpose:** Bridge the four `tags/` handoff files to the live compendium-web import API. You already have the vocabulary and tagging rules; this document covers **what to send, how compendium-web consumes it, and what is not wired yet**.

**Last verified against compendium-web:** commit `6cbe9ce` (`Persist canonical resource tags on accept`) and later.

---

## 1. Context

### Taxonomy migration is complete

Production taxonomy is aligned with the ingestion vocabulary:

| Taxonomy | Leaf / filterable level | Count |
|---|---|---|
| `methodology` | methodology (category → methodology) | **140** methodologies, 13 categories |
| `specialty` | specialty (grouping → specialty) | **78** specialties |
| `resource_type` | subtype (type → subtype) | **74** subtypes, **13** types |
| `thesis` | stage (phase → stage) | **25** stages, 6 phases |
| `cross_specialty_domain` | domain (flat) | 11 |
| `foundation_skill` | skill (flat) | 16 |

### This agent is standalone

The ingestion agent is **not** `compendium-web/src/pipeline/workers/classify.ts` or `litellm.ts`. Those are the **legacy** in-app classifier:

| Concern | Ingestion agent (this build) | Legacy `classify.ts` |
|---|---|---|
| Methodology codes | Vocabulary codes (`OBS-11`, `SYN-04`, …) | RS-/OD-/QR- prefix codes |
| Thesis | Stage codes (`EV-03`, …) or phase (`HI`, `SH`) | Six phase codes only (`TH` … `SH`) |
| Specialty | Vocabulary **codes** (`PSYCH`, `ICU`) | URL **slugs** (`psychiatry`) |

Your agent emits the **forward model**. compendium-web accepts it via the vocabulary-native parser added in `ec90a07+`.

### What `ec90a07+` added

`compendium-web/src/pipeline/parsers/vocabulary-tags.ts` and updates to `parsers/json.ts` recognise a native `tags[]` array on each resource:

```json
{ "taxonomy": "methodology", "code": "OBS-11", "confidence": 0.9 }
```

The parser expands these into legacy-compatible import columns **and** preserves the structured form in `raw_data` for future write paths.

---

## 2. Files to use

### Agent handoff bundle (`tags/`)

| File | Role |
|---|---|
| `tags/cothesis_tag_vocabulary.json` | **Authoritative vocabulary** — every `code` you emit must exist here |
| `tags/cothesis_tag_vocabulary_spec.md` | Precise tagging rules, match priority, output contract |
| `tags/ingestion_agent_prompt.md` | Conversational prompt + worked examples for the agent |
| `tags/cothesis_demo_resources_retagged.json` | **Answer key** — 14 resources tagged correctly; self-check before submit |

### Production taxonomy export (repo root)

| File | Role |
|---|---|
| `cothesis_taxonomy_library.json` | Live taxonomy snapshot exported from production Neo4j (counts, slugs, hierarchy). Use for cross-checking specialty slug resolution and browse-tab counts — **not** as the agent emit contract (use `cothesis_tag_vocabulary.json` for that). |

Regenerate from compendium-web (requires Doppler + Neo4j):

```bash
cd compendium-web
doppler run --project dave-ai-stack --config prd -- \
  pnpm exec tsx src/pipeline/cli/export-taxonomy-library.ts
```

Output lands at `../cothesis_taxonomy_library.json` (repo root).

### Migration addenda (schema intent)

These define the **forward persistence model** (`resource_tag`, `taxonomy_closure`, `TAGGED_AS`). The ingestion agent should understand them; compendium-web writes `resource_tag` + `TAGGED_AS` on accept as of `6cbe9ce` (see §5). `taxonomy_closure` rollup queries are separate.

| File | Topic |
|---|---|
| `files/migration_addendum_tagging_model.md` | Rollup tagging model, `resource_tag`, `taxonomy_closure`, `TAGGED_AS` |
| `files/migration_addendum_thesis_taxonomy.md` | Thesis phase/stage taxonomy structure |
| `migration_addendum_specialty_reconciliation.md` | Specialty code reconciliation (78 canonical codes, PATH split) |

---

## 3. API contract

### Endpoint

```
POST https://compendium-web-production.up.railway.app/api/import/json
```

(Local / staging: same path on your `NEXT_PUBLIC_SITE_URL` host.)

### Authentication

| Header | Value |
|---|---|
| `Authorization` | `Bearer {IMPORT_API_KEY}` ← **preferred** |
| `x-import-key` | `{IMPORT_API_KEY}` ← legacy compat |

Retrieve the key:

```bash
IMPORT_API_KEY=$(doppler secrets get IMPORT_API_KEY --plain -p dave-ai-stack -c prd)
```

(`compendium-web` route: `src/app/(payload)/api/import/json/route.ts`)

### Request body (top level)

```json
{
  "source_file": "agent-batch-2026-06-11.json",
  "source_tool": "claude",
  "resources": [ /* ... */ ]
}
```

| Field | Required | Notes |
|---|---|---|
| `source_file` | Recommended | Traceability label; defaults to `"inline.json"` |
| `source_tool` | Required | One of: `gemini`, `claude`, `manus`, `manual`, `discovery_prompt` |
| `resources` | Required | Non-empty array |

Use **`source_tool: "claude"`** or **`"manus"`** for ratified agent payloads (trusted path — see below).

### Per-resource fields

**Minimum:** at least one of `url` or `title`. Invalid URLs are dropped unless `title` is present.

#### Recommended shape (vocabulary-native)

```json
{
  "url": "https://www.covidence.org",
  "title": "Covidence",
  "editorial_description": "Web-based platform for managing systematic reviews…",
  "editorial_description_long": "Optional longer discovery context for the resource page.",
  "tags": [
    { "taxonomy": "resource_type", "code": "systematic_review_tool", "confidence": 0.98 },
    { "taxonomy": "methodology", "code": "SYN-04", "confidence": 0.85 },
    { "taxonomy": "thesis", "code": "HI-02", "confidence": 0.8 },
    { "taxonomy": "specialty", "code": "PSYCH", "confidence": 0.7 },
    { "taxonomy": "foundation_skill", "code": "FS-02", "confidence": 0.6 },
    { "taxonomy": "cross_specialty_domain", "code": "DIGHEALTH", "confidence": 0.55 }
  ],
  "access_type": "freemium",
  "doi": null,
  "authors": ["…"],
  "publication_year": 2024
}
```

#### Native `tags[]` shape

```json
{ "taxonomy": "<taxonomy>", "code": "<vocabulary_code>", "confidence": 0.0-1.0 }
```

- `taxonomy` — one of the six taxonomies (see §4).
- `code` — must exist in `cothesis_tag_vocabulary.json` for that taxonomy.
- `confidence` — optional float; stored but not used for routing today (see §6).

Detection: `tags` is treated as vocabulary-native when **every** element has `taxonomy` and `code` strings (`isVocabularyTagArray` in `vocabulary-tags.ts`).

#### Alternate shape (flat fields — still supported)

You may send expanded flat fields instead of or in addition to `tags[]`:

| Flat field | Aliases accepted by parser |
|---|---|
| `resource_type` / `subtype` | `type`, `category`, `kind`, `format` / `sub_type`, `subcategory` |
| `methodology_tags` | `tags`, `methodology`, `methods` (only when **not** vocabulary-native array) |
| `thesis_stages` | `stages`, `thesis_stage` |
| `specialty_tags` | `specialties`, `specialty` |
| `editorial_description` | `description`, `summary`, `abstract`, `notes` |
| `editorial_description_long` | `discovery_context`, `description_long` |

If you send **both** `tags[]` and flat fields, vocabulary expansion merges thesis stages and specialties (deduped).

### What compendium-web expands `tags[]` into

`expandVocabularyTags()` (`vocabulary-tags.ts`) maps native tags to import-candidate columns:

| Native `taxonomy` | Expanded to | Notes |
|---|---|---|
| `methodology` | `methodology_tags[]` | Codes as-is (`OBS-11`, `SYN-04`, …) |
| `thesis` | `thesis_stages[]` | Stage or phase codes (`EV-03`, `SH`, …) |
| `specialty` | `specialty_tags[]` | **Code → slug** via `resolveSpecialtySlugFromCode` (e.g. `CARDIO` → `cardiology`) |
| `resource_type` | `resource_type` + `subtype` | Subtype codes resolve to Neo4j type + subtype (e.g. `guideline_article` → `article` + `guideline_article`) |
| `foundation_skill` | `raw_data.vocabulary_tags.foundation_skill[]` | Also persisted on accept → `resource_tag` + `TAGGED_AS` → `FoundationSkill` |
| `cross_specialty_domain` | `raw_data.vocabulary_tags.cross_specialty_domain[]` | Also persisted on accept → `resource_tag` (taxonomy `domain`) + `TAGGED_AS` → `CrossSpecialtyDomain` |

Also preserved in `raw_data`:

- `structured_tags` — original `tags[]` array
- `tag_confidence` — map keyed `"taxonomy:code"` → float

### Trusted upstream path (`source_tool: claude` | `manus`)

To **skip the legacy LLM classifier** (`classify.ts`), all of the following must be true:

1. `source_tool` is `"claude"` or `"manus"`
2. `description` / `editorial_description` is **non-empty** (required for trusted enrichment skip too)
3. At least one `methodology_tags` entry matches platform leaf pattern `^[A-Z]{2,6}-\d{2}$` (e.g. `SYN-04`, `OBS-11`)

When trusted:

- Classify worker skips LiteLLM; sets `classifier_model = 'upstream-trusted'`
- `classification_confidence` and `relevance_score` pre-set to `1.0` / `0.95` at ingest
- Accept worker marks node `status = 'enriched'` immediately (no enrichment LLM)
- Sync path (`sync-import.ts`) may run dedup → accept in-process without Redis

**Implication for your agent:** always include a **leaf methodology code** in `tags[]` when you want the trusted fast path, even if methodology is not the primary signal. Also always send `editorial_description` (maps to `description` on the candidate).

`resource_type` from vocabulary expansion satisfies `classified_type` for trusted detection when methodology leaf is present.

### Response shape

```json
{
  "success": true,
  "import_batch_id": "uuid",
  "batch_id": "uuid",
  "source_file": "…",
  "source_tool": "claude",
  "resource_count": 1,
  "stored_count": 1,
  "skipped_count": 0,
  "resources": [
    {
      "resource_id": "uuid",
      "compendium_id": "uuid",
      "public_url": "https://compendium-web-production.up.railway.app/library/resource/{uuid}",
      "compendium_url": "https://compendium-web-production.up.railway.app/library/resource/{uuid}",
      "url": "…",
      "title": "…"
    }
  ],
  "message": "Accepted N resource(s). Dedup → classify → accept pipeline queued."
}
```

- IDs and `public_url` are assigned **synchronously at ingest** (before workers finish).
- Live page: `/library/resource/{resource_id}` (singular `resource`).
- Batch status: `GET /api/import?batch_id={uuid}`

### Copy-paste submit example

```bash
IMPORT_API_KEY=$(doppler secrets get IMPORT_API_KEY --plain -p dave-ai-stack -c prd)
BASE=https://compendium-web-production.up.railway.app

curl -s -X POST "$BASE/api/import/json" \
  -H "Authorization: Bearer $IMPORT_API_KEY" \
  -H "Content-Type: application/json" \
  -d @payload.json | jq .
```

---

## 4. Tagging rules (brief)

Full rules live in `tags/cothesis_tag_vocabulary_spec.md` and `tags/ingestion_agent_prompt.md`. Non-negotiables:

1. **Leaf only, up-only rollup** — tag the finest level you are confident about; never also tag the parent. Rollup is query-time, not your job.
2. **Six independent taxonomies** — `methodology`, `resource_type`, `specialty`, `thesis`, `cross_specialty_domain`, `foundation_skill`.
3. **Specialty: emit codes, not slugs** — e.g. `PSYCH`, `ICU`. compendium-web resolves code → directory slug (`adult-psychiatry`, `cardiology`, …) at import.
4. **Omit rather than guess** — especially specialty and thesis.
5. **Thesis is special** — match on `deliverables` + `search_terms`, not stage display names.
6. **Validate every code** against `cothesis_tag_vocabulary.json` before emit.

Self-check against `tags/cothesis_demo_resources_retagged.json` (14 worked examples).

---

## 5. What compendium-web does vs does not do yet

### DOES (today, on accept)

| Action | Detail |
|---|---|
| Parse vocabulary-native `tags[]` | `parsers/json.ts` → `expandVocabularyTags()` |
| Insert `compendium.import_candidates` | Full normalised payload in `raw_data` including `structured_tags`, `tag_confidence`, `vocabulary_tags` |
| Skip LLM classify | Trusted `claude`/`manus` + description + platform methodology leaf code |
| Neo4j `CompendiumResource` node | `methodology_tags`, `thesis_stages` properties; type label from `classified_type` |
| **`compendium.resource_tag` rows** | Written on accept via `persist-resource-tags.ts` — all six taxonomies including `foundation_skill` and `cross_specialty_domain` (PG taxonomy `domain`) |
| **`(Resource)-[:TAGGED_AS]->(TaxonomyNode)` edges** | Written on accept for vocabulary tags → `CompendiumMethodology`, `Specialty`, `ThesisStage`/`ThesisPhase`, `ResourceSubtype`/`ResourceType`, `FoundationSkill`, `CrossSpecialtyDomain` |
| `USES_METHODOLOGY` edges | **Leaf methodology codes only** (`methodologyLeafCodes` — pattern `^[A-Z]{2,6}-\d{2}$`) — **legacy parallel write** |
| `RELEVANT_TO_SPECIALTY` edges | Match on slug **or** code — **legacy parallel write** |
| `discovery_records` row | Provenance / discovery context |
| Trusted enrichment skip | `status = 'enriched'` when `source_tool` is trusted and `editorial_description` present |

**Transition note:** Accept still dual-writes legacy node properties (`methodology_tags`, `thesis_stages`) and legacy edges (`USES_METHODOLOGY`, `RELEVANT_TO_SPECIALTY`) alongside the canonical `resource_tag` + `TAGGED_AS` path. Both remain active until browse/query paths fully migrate off the legacy shapes.

### DOES NOT YET

| Gap | Current behaviour |
|---|---|
| `taxonomy_closure` rollup queries | Browse rollup via closure table not wired; filters use direct `TAGGED_AS` / legacy edges |
| Backfill of existing resources | Only **new accepts** after `6cbe9ce` get `resource_tag` + `TAGGED_AS`; older resources retain legacy shapes until backfill |
| Retire legacy dual-write | `USES_METHODOLOGY`, `RELEVANT_TO_SPECIALTY`, and node property arrays still written in parallel |

### Legacy classify path (non-trusted)

If `source_tool` is not `claude`/`manus`, or trusted criteria fail, `classify.ts` invokes LiteLLM with **RS-/OD-/QR- methodology codes**, phase-only thesis, and slug-based specialties. Do not rely on this path for vocabulary-native payloads.

---

## 6. Confidence

### Per-tag confidence (your agent)

- Emit `confidence` on each tag object (0–1).
- Stored in `raw_data.tag_confidence` as `"taxonomy:code"` → float.
- **Not used for routing or filtering** in compendium-web today. Intended for downstream QA / HITL thresholding in your agent console.

Suggested agent thresholds (from spec — enforce in your build, not in compendium-web):

| Range | Suggested action |
|---|---|
| ≥ 0.8 | Auto-accept tag |
| 0.5 – 0.8 | Queue for review |
| < 0.5 | Drop tag |

### Resource-level classification confidence (classify path only)

If a resource falls through to `classify.ts`, routing uses env-configurable thresholds (`types.ts`):

| Threshold | Default | Env var |
|---|---|---|
| Auto-accept confidence | **0.8** | `IMPORT_CONFIDENCE_AUTO_ACCEPT` |
| Review-needed confidence | **0.5** | `IMPORT_CONFIDENCE_REVIEW` |
| Auto-accept relevance | **0.6** | `IMPORT_RELEVANCE_AUTO_ACCEPT` |
| Auto-exclude relevance | **0.3** | `IMPORT_RELEVANCE_AUTO_EXCLUDE` |

Trusted upstream payloads bypass this entirely (pre-set to 1.0 / 0.95).

---

## 7. Production URLs and ops commands

### URLs

| Service | URL |
|---|---|
| **compendium-web (import API)** | `https://compendium-web-production.up.railway.app` |
| Import endpoint | `POST …/api/import/json` |
| Public resource page | `…/library/resource/{resource_id}` |
| Future production domain | `https://cothesis.ai` (DNS cutover pending) |

### Doppler project

Project: `dave-ai-stack`, config: `prd`

```bash
# API key for agent submit
IMPORT_API_KEY=$(doppler secrets get IMPORT_API_KEY --plain -p dave-ai-stack -c prd)

# Export live taxonomy library → repo root
cd compendium-web
doppler run --project dave-ai-stack --config prd -- \
  pnpm exec tsx src/pipeline/cli/export-taxonomy-library.ts

# Validate taxonomy alignment (PG + Neo4j counts vs aligned JSON)
doppler run --project dave-ai-stack --config prd -- \
  pnpm validate:taxonomy-aligned
```

---

## 8. Testing

### Answer key: demo JSON

`tags/cothesis_demo_resources_retagged.json` — 14 resources with expected `tags[]`. Before submitting a batch, diff your agent output structure and codes against this file.

### compendium-web smoke test script

Runs parser expansion without hitting the API:

```bash
cd compendium-web
pnpm exec tsx src/pipeline/scripts/test-vocabulary-tags.ts
```

Exercises `normaliseImportResource()` with a mixed `tags[]` payload (methodology category + leaf, thesis phase + stage, specialty, resource_type, foundation_skill, domain). Expects:

- `methodology_tags: ['EXP', 'EXP-01']`
- `thesis_stages: ['SH', 'SH-01']`
- `specialty_tags: ['cardiology']` (from `CARDIO`)
- `resource_type: 'article'`, `subtype: 'guideline_article'`
- `vocabulary_tags.foundation_skill` / `cross_specialty_domain` populated
- `tag_confidence['methodology:EXP-01']` present

### End-to-end API test

```bash
IMPORT_API_KEY=$(doppler secrets get IMPORT_API_KEY --plain -p dave-ai-stack -c prd)
curl -s -X POST "https://compendium-web-production.up.railway.app/api/import/json" \
  -H "Authorization: Bearer $IMPORT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source_file": "smoke-test.json",
    "source_tool": "claude",
    "resources": [{
      "url": "https://example.org/smoke-test",
      "title": "Smoke test resource",
      "editorial_description": "Temporary smoke test — delete me.",
      "tags": [
        {"taxonomy": "methodology", "code": "SYN-04", "confidence": 0.9},
        {"taxonomy": "resource_type", "code": "methodology_guide", "confidence": 0.9}
      ]
    }]
  }' | jq .
```

Open returned `public_url`; expect title, editor's note, methodology chips (if workers healthy).

---

## 9. Known gaps and roadmap

| Item | Status | Notes |
|---|---|---|
| `resource_tag` + `TAGGED_AS` write path | **Done** (`6cbe9ce`) | Accept worker calls `persistResourceTags()` — PG `resource_tag` + Neo4j `TAGGED_AS` for all six taxonomies including `foundation_skill` and `cross_specialty_domain` |
| Legacy dual-write retirement | **Open** | `methodology_tags`/`thesis_stages` properties and `USES_METHODOLOGY`/`RELEVANT_TO_SPECIALTY` edges still written alongside canonical path during transition |
| Backfill existing resources | **Open** | Pre-`6cbe9ce` resources lack `resource_tag`/`TAGGED_AS` until a backfill job runs |
| `PATH` → discipline disambiguation | **Partial** | `PATH` retired; split into 5 pathology disciplines (`ANAT_PATH`, …). Existing PATH-tagged resources defaulted to `ANAT_PATH` with `_needs_retag` — see `migration_addendum_specialty_reconciliation.md` |
| `taxonomy_closure` rollup browse | **Open** | Closure-table rollup queries per tagging-model addendum not wired |
| Stable external dedup key | **Not supported** | Dedup matches normalised URL, DOI, ISBN |
| `compendium-import` legacy service | **Decommission pending** | Use `compendium-web-production` `/api/import/json` only |

---

## 10. compendium-web code map

| Concern | File |
|---|---|
| Import API route | `compendium-web/src/app/(payload)/api/import/json/route.ts` |
| Sync ingest + ID assignment | `compendium-web/src/pipeline/lib/ingest-json.ts` |
| JSON normalisation + tag detection | `compendium-web/src/pipeline/parsers/json.ts` |
| Vocabulary tag expansion | `compendium-web/src/pipeline/parsers/vocabulary-tags.ts` |
| Code → slug / type maps | `compendium-web/src/pipeline/lib/tag-vocabulary.ts` |
| Trusted classify skip | `compendium-web/src/pipeline/workers/classify.ts` |
| Sync trusted accept (no Redis) | `compendium-web/src/pipeline/lib/sync-import.ts` |
| Neo4j accept + edges | `compendium-web/src/pipeline/workers/accept.ts` |
| Canonical tag persist (`resource_tag`, `TAGGED_AS`) | `compendium-web/src/pipeline/lib/persist-resource-tags.ts` |
| Routing thresholds | `compendium-web/src/pipeline/types.ts` |
| Parser smoke test | `compendium-web/src/pipeline/scripts/test-vocabulary-tags.ts` |
| Tag persist smoke test | `compendium-web/src/pipeline/scripts/test-persist-resource-tags.ts` |
| Curation integration notes | `compendium-web/docs/CURATION_AGENT_HANDOFF.md` |

---

## Quick checklist before submit

- [ ] Every `code` exists in `tags/cothesis_tag_vocabulary.json`
- [ ] Leaf-only tags (no parent+child pairs in same taxonomy)
- [ ] Specialty emitted as **codes** (`PSYCH`), not slugs
- [ ] `source_tool` is `claude` or `manus` for trusted path
- [ ] `editorial_description` present (non-empty)
- [ ] At least one **leaf** methodology code in `tags[]` (e.g. `SYN-04`, not category-only `SYN` alone — category codes do not match `^[A-Z]{2,6}-\d{2}$`)
- [ ] Compared output to `cothesis_demo_resources_retagged.json`
- [ ] `IMPORT_API_KEY` in `Authorization: Bearer` header
