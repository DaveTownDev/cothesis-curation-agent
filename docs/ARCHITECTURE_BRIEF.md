# CoThesis Curation Agent — Architecture Brief

Diagram-ready reference for Devpost submission. All values are taken from the codebase (`agents/`, `console/`, `scripts/`, `docs/ARCHITECTURE.md`) as of 2026-06-12.

**GCP project:** `cothesis-curation-agent`  
**Model env defaults:** `MODEL_FLASH=gemini-3.5-flash`, `MODEL_FLASH_LITE=gemini-3.1-flash-lite`, `MODEL_PRO=gemini-3.1-pro-preview`, `GOOGLE_CLOUD_LOCATION=global`

---

## 1. COMPONENTS

| Component | Description | Google Cloud service | Gemini model |
|---|---|---|---|
| **Orchestrator** (`agents/pipeline/agent.py` → `root_agent`) | ADK `LlmAgent` that sequences the curation pipeline via `AgentTool` wrappers; supports Mode A (curate known URL) and Mode B (discover then curate). | Cloud Run service `cothesis-agent` (private) | `gemini-3.1-pro-preview` (`MODEL_PRO`) |
| **Discovery** (`agents/discovery/agent.py`) | Finds candidate resources for a `(methodology_code × resource_type)` pair; deterministic API-first, LLM for relevance/dedupe. | Cloud Run (via orchestrator) | `gemini-3.1-flash-lite` (`MODEL_FLASH_LITE`) |
| **Appraisal** (`agents/appraisal/agent.py`) | Scores quality (0–100), six canonical dimensions, `ai_confidence`; fetches OpenAlex/PubMed metadata first; writes `drafts`. | Cloud Run (via orchestrator) | `gemini-3.5-flash` (`MODEL_FLASH`) |
| **Classification** (`agents/classification/agent.py`) | Assigns `resource_type_code`, subtype, `methodology_codes` (SYN/OBS/EVAL), stages, skills, difficulty, access, `relevance_score` + `classification_confidence` (0–1). | Cloud Run (via orchestrator) | `gemini-3.1-flash-lite` (`MODEL_FLASH_LITE`) |
| **Editorial** (`agents/editorial/agent.py`) | Writes `editorial_description`, `summary`, `editorial_description_plain`; proposes badges (max 3). Never writes `editorial_note`. | Cloud Run (via orchestrator) | `gemini-3.5-flash` (`MODEL_FLASH`) |
| **Reconciliation** (`agents/reconciliation/agent.py`) | Dedup by title similarity ≥ 0.9; assembles final draft record; persists to `draft_records`. | Cloud Run (via orchestrator) | `gemini-3.1-flash-lite` (`MODEL_FLASH_LITE`) |
| **QC Panel** (`agents/qc_panel/agent.py`) | Runs deterministic checks (AI-pattern, voice, jargon, badges, taxonomy) plus six dimension evaluators; aggregates `panel_scores` and `panel_agreement`. | Cloud Run (via orchestrator) | `gemini-3.1-flash-lite` (`MODEL_FLASH_LITE`) |
| **Arbiter** (`agents/arbiter/agent.py`) | Pure-Python routing gate (`agents/arbiter/tools.py`); writes `review_queue` on `review_needed`; composite score for display. | Cloud Run (via orchestrator) | `gemini-3.1-pro-preview` (`MODEL_PRO`) — agent shell; routing is deterministic code |
| **Grounding agent** (`agents/grounding/agent.py`) | Isolated `VertexAiSearchTool` sub-agent for methodology definitions and reporting standards (exclusive tool constraint). | Cloud Run (via orchestrator `AgentTool`) | `gemini-3.5-flash` (`MODEL_FLASH`) |
| **Deterministic orchestrator** (`agents/pipeline/deterministic.py`) | Production batch entrypoint `run_pipeline()`; Python-sequenced stages, LLM only for judgments, mandatory Firestore writes. | Cloud Run Job `run-batch`, local CLI | Same tiering as agents above |
| **Console** (`console/`) | Next.js HITL review console: queue triage, edit/ratify drafts, publish checklist, Compendium sync, pipeline dashboard. | Cloud Run service `console` (public + passcode) | None (reads Firestore; optional Vertex via server actions) |
| **Compendium bridge** (`agents/shared/compendium_bridge.py`) | Maps Firestore `resources` → Compendium `ImportCandidate` for `POST /api/import/json`; builds vocabulary-native `tags[]`. | Invoked by sync service and console | None |
| **Batch runner** (`scripts/batch.py`, `scripts/run_batch.py`) | Pulls `compendium.enrichment_queue` (Railway Postgres), runs `run_pipeline()` in-process, updates queue status. | Cloud Run Job `run-batch` | Uses deterministic orchestrator models |
| **Sync service** (`scripts/sync.py`, `scripts/sync_to_compendium.py`) | Fetches published unsynced `resources`, transforms via bridge, POSTs to Compendium, writes sync metadata back. | Cloud Run Job `sync-to-compendium` | None |

**Supporting components (not in required list but present):**

| Component | Path | Role |
|---|---|---|
| Enrichment layer | `agents/enrichment/enrich.py`, `agents/enrichment/sources.py` | Free metadata APIs merged into `type_fields` before appraisal (batch path) |
| Source verification | `agents/shared/source_check.py` | HTTP/DOI liveness check at pipeline start (batch path) |
| Prompt lab | `agents/prompt_lab/` | Offline prompt-improvement agents; Cloud Run Job `prompt-lab-run` |
| HITL helpers | `agents/shared/hitl.py` | `write_review_queue_item`, `get_review_status` |

---

## 2. DATA STORES

All Firestore collections use project `cothesis-curation-agent`, default database, region `us-central1`. Optional prefix via `FIRESTORE_COLLECTION_PREFIX` (e.g. `eval_` for isolated eval runs).

### `drafts`

| Aspect | Detail |
|---|---|
| **Written by** | Appraisal agent (`write_draft_assessment` in `agents/appraisal/tools.py`) |
| **Document shape** | `AIAssessmentDraft`: `resource_code`, `quality_score`, `ai_confidence`, `quality_dimensions` (6 + optional `ebm_level`), `model_version`, `assessment_prompt_version`, `pipeline_run_id`, strengths/limitations, etc. |
| **Read by** | Console Pipeline Inspector (`getDraftAssessment` in `console/lib/firestore.ts`); review workspace provenance tab |
| **Key** | Auto-generated doc ID; queried by `resource_code` |

### `draft_records`

| Aspect | Detail |
|---|---|
| **Written by** | Reconciliation (`assemble_record` tool + `deterministic.run_pipeline` stage 4) |
| **Document shape** | Full assembled draft Resource: identity, editorial fields, classification, quality, `proposed_badges`, `type_fields`, `enrichment_sources`, `editorial_status: "proposed"`, `tags[]` |
| **Document ID** | `{resource_code}` (kebab-case + 6-char hash from `derive_resource_code`) |
| **Read by** | Arbiter (fallback if orchestrator didn't thread record); console catalog editor (`getDraftRecordDoc`); dedup (`fetch_existing_keys`) |

### `review_queue`

| Aspect | Detail |
|---|---|
| **Written by** | Arbiter / HITL (`write_review_queue_item` in `agents/shared/hitl.py`); deterministic pipeline on `review_needed`, dead source, or appraisal failure |
| **Document shape** | `{ resource_code, routing, reason, panel_result, draft_record, status, queued_at }`; optional `qa_audit`, `rejected_reason`, requeue fields |
| **Status values** | `pending`, `approved`, `rejected`, `requeued` |
| **Read by** | Console review queue (`getReviewQueue`, `getReviewQueueItem`); dashboard stats |
| **Note** | `auto_accept` and `auto_exclude` do **not** write here (outcome in `pipeline_state` only) |

### `resources`

| Aspect | Detail |
|---|---|
| **Written by** | Console on approve (`console/app/review/actions.ts` → `approveItem`, `bulkApproveAsDrafted`); reject sets `editorial_status: "archived"` |
| **Document shape** | Ratified Resource: all draft fields + `editorial_badges`, `editorial_note`, `editorial_reviewed_by`, `editorial_reviewed_at`, `editorial_status: "published"`, Compendium sync fields |
| **Document ID** | `{resource_code}` |
| **Read by** | Console Published page; dedup (`fetch_existing_titles`, `fetch_existing_keys`); sync service (`fetch_unsynced_records`); Compendium bridge |

### `pipeline_state`

| Aspect | Detail |
|---|---|
| **Written by** | Deterministic orchestrator (`_write_state` in `agents/pipeline/deterministic.py`); console on reject (`state: "hitl_rejected"`) |
| **Document ID** | `{resource_code}` |
| **Document shape** | Stage machine: `current_stage` / `state`, `stages_completed`, `stages_remaining`, per-stage timestamps (`appraised_at`, `classified_at`, …), `arbiter_decision`, `outcome`, `pipeline_run_id`, `classification_result` |
| **Stages** | `appraisal` → `classification` → `editorial` → `reconciliation` → `qc_panel` → `arbiter` |
| **Read by** | Console `/pipeline` dashboard and Pipeline Inspector (`getPipelineState`, `getPipelineRuns`) |

### Other Firestore collections (supporting)

| Collection | Purpose |
|---|---|
| `eval_failure_bucket` | HITL-flagged failures for prompt lab |
| `eval_gold_cases` | Gold eval cases exported from console |
| `prompt_proposals` | Prompt lab diff proposals |
| `prompt_lab_runs` | Prompt lab job audit trail |

### External: Railway Postgres `compendium.enrichment_queue`

| Aspect | Detail |
|---|---|
| **Read by** | Batch runner (`scripts/batch.py` → `fetch_pending_items`) |
| **Joined with** | `compendium.import_candidates` for title, URL, DOI, PMID, methodology_tags |
| **Updated by** | Batch runner: `status` → `processing` / `complete` / `failed` |

---

## 3. EXTERNAL CONNECTIONS

### MCP server (production discovery + enrichment gateway)

| Aspect | Detail |
|---|---|
| **Connection** | ADK `MCPToolset` over SSE (`agents/discovery/agent.py`); env `MCP_SERVER_URL`, auth `MCP_SERVER_KEY` |
| **When used** | Discovery agent in production; expands beyond local direct-API fallback |
| **APIs exposed (17+ per `docs/AGENTS_SPEC.md`, `docs/DATA_SOURCES.md`)** | PubMed/E-utilities, CrossRef, OpenAlex, Unpaywall, iCite, Altmetric, Semantic Scholar, ISBNdb, Google Books, OpenLibrary, Springer, GitHub, bio.tools, Zenodo, Figshare, DataCite, protocols.io, YouTube Data API, podcast RSS, Reddit, Stack Exchange, NIH RePORTER, SearXNG (metasearch), Crawl4AI (web scrape/extract), Marker/Docling (PDF) |
| **Self-hosted appraisal tools (articles)** | RobotReviewer (risk of bias), URSE (GRADE), MedJEx (jargon) — via MCP in production |

### Direct HTTP APIs (local dev + batch enrichment)

Used directly in `agents/discovery/tools.py`, `agents/appraisal/tools.py`, `agents/enrichment/sources.py`:

| API | Endpoint / use |
|---|---|
| **OpenAlex** | `https://api.openalex.org/works` — discovery search, metadata, citations |
| **PubMed** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` — esearch, esummary |
| **CrossRef** | `https://api.crossref.org/works/{doi}` |
| **Unpaywall** | `https://api.unpaywall.org/v2/{doi}` |
| **iCite** | `https://icite.od.nih.gov/api/pubs` |
| **OpenLibrary** | `https://openlibrary.org/api/books`, `/search.json` |
| **Google Books** | `https://www.googleapis.com/books/v1/volumes` |
| **GitHub** | `https://api.github.com/repos/{owner}/{repo}` |
| **bio.tools** | `https://bio.tools/api/tool/` |
| **DataCite** | `https://api.datacite.org/dois/{doi}` |

**Premium sources listed but not implemented without API keys:** Altmetric, Dimensions, Scite, ISBNdb (`NEEDS_API_KEY` in `agents/enrichment/sources.py`).

### Vertex AI Search (grounding)

| Aspect | Detail |
|---|---|
| **Tool** | `VertexAiSearchTool` in `agents/grounding/agent.py` (exclusive — no other tools on that agent) |
| **Datastore ID** | `projects/cothesis-curation-agent/locations/global/collections/default_collection/dataStores/cothesis-methodology-grounding` (env override: `VERTEX_DATASTORE_ID`) |
| **Content** | Methodology definitions, reporting standards, seed resources (18 documents ingested per build plan) |
| **Access** | Via `AgentTool(grounding_agent)` from orchestrator |

### Compendium live API

| Aspect | Detail |
|---|---|
| **Endpoint** | `POST {COMPENDIUM_IMPORT_URL}/api/import/json` |
| **Auth** | Bearer `IMPORT_API_KEY` |
| **Payload** | `{ source_file, source_tool: "claude", resources: [ImportCandidate…] }` |
| **Called by** | Sync service (`scripts/sync.py`), console (`console/lib/compendium-sync-actions.ts` on approve) |

### Railway Postgres (Compendium backing store)

| Aspect | Detail |
|---|---|
| **Connection** | `DATABASE_PUBLIC_URL` |
| **Tables** | `compendium.enrichment_queue`, `compendium.import_candidates` |
| **Used by** | Batch runner, `agents/shared/enrichment_queue_sync.py`, live catalog export scripts |

---

## 4. FLOW — Single resource: discovery to publication

### Entry points

1. **Interactive:** `adk web agents/` → user message to `root_agent` (Mode A or B).
2. **Batch:** Railway queue row → `scripts/run_batch.py` → `run_pipeline()` in `agents/pipeline/deterministic.py`.
3. **Live reprocess:** `scripts/reset_and_reprocess_live.py` reads Postgres export, calls `run_pipeline()` directly.

### Stage sequence (deterministic path — canonical production flow)

| Step | Agent / code | Reads | Writes | Model |
|---|---|---|---|---|
| **0. Source verify** | `verify_source()` | URL, DOI | — | None |
| **0b. Enrichment** | `enrich()` | DOI, PMID, ISBN, URL, title | Merged metadata dict | None (HTTP APIs) |
| **1. Appraisal** | Appraisal | Resource input + enrichment metadata | `drafts` (assessment), `pipeline_state` stage=`appraisal` | `gemini-3.5-flash` |
| **2. Classification** | Classification | Resource + metadata + vocabulary guide | `pipeline_state` stage=`classification`, `classification_result` | `gemini-3.1-flash-lite` |
| **3. Editorial** | Editorial | Resource + classification | `pipeline_state` stage=`editorial` | `gemini-3.5-flash` |
| **4. Reconciliation** | Reconciliation (code) | `resources` + `draft_records` titles for dedup | `draft_records/{resource_code}`, `pipeline_state` stage=`reconciliation` | None (dedup is `difflib`; similarity ≥ `IMPORT_TITLE_SIMILARITY_THRESHOLD=0.9`) |
| **5. QC Panel** | QC Panel (code) | Assembled `draft_record` | `pipeline_state` stage=`qc_panel` | None (deterministic checks + dimension pass-through from appraisal) |
| **6. Arbiter** | `compute_routing_decision()` | Classification scores, appraisal scores, panel agreement | `pipeline_state` stage=`arbiter`, `outcome`, `arbiter_decision` | None (pure Python) |
| **7. Outcome** | HITL helper | — | `review_queue` if `review_needed`; else outcome only in `pipeline_state` | None |

**Discovery path (interactive Mode B only):** Discovery agent runs first (`gemini-3.1-flash-lite` + OpenAlex/PubMed or MCP), emits candidates `{ title, url, source, type_hint, raw_metadata, skip_reason }`; orchestrator skips candidates with `skip_reason` set, then runs steps 1–7 per candidate.

**Interactive path differences:** LlmAgent orchestrator may invoke grounding via `AgentTool`; stage order is prompt-driven (same agents); arbiter's `write_review_queue` tool handles `review_needed` writes; non-deterministic early-stop possible (why batch uses code orchestrator).

### Routing gate logic (`agents/arbiter/tools.py`)

**Env thresholds (0–1 routing layer):**

```
IMPORT_RELEVANCE_AUTO_ACCEPT=0.6
IMPORT_RELEVANCE_AUTO_EXCLUDE=0.3
IMPORT_CONFIDENCE_AUTO_ACCEPT=0.8
IMPORT_CONFIDENCE_REVIEW=0.5
IMPORT_TITLE_SIMILARITY_THRESHOLD=0.9  (dedup, not routing)
```

**Hardcoded quality thresholds (0–100 display layer):**

```
QUALITY_AUTO_ACCEPT=80.0
QUALITY_EXCLUDE=60.0
AI_CONFIDENCE_REVIEW=70.0
PANEL_AGREE_THRESHOLD=0.7
QC panel pass threshold per dimension: 60.0
```

**Decision tree (in order):**

1. `skip_reason` set → **`auto_exclude`**
2. `methodology_required` and empty `methodology_codes` and `quality_score ≥ 60` → **`review_needed`** (never silent auto-accept without methodology)
3. `quality_score < 60` → **`auto_exclude`**
4. `classification_confidence ≥ 0.8` AND `relevance_score < 0.3` → **`auto_exclude`**
5. ALL of: `classification_confidence ≥ 0.8`, `relevance_score ≥ 0.6`, `quality_score ≥ 80`, `ai_confidence ≥ 70`, `panel_agreement ≥ 0.7` → **`auto_accept`**
6. Else → **`review_needed`** (with reason listing failed signals)

**Composite score (display, 0–100):**  
`quality_score×0.40 + ai_confidence×0.20 + relevance_score×100×0.15 + classification_confidence×100×0.15 + panel_agreement×100×0.10`

**Publication gate:** Nothing is live on Compendium without human ratification. `auto_accept` records outcome in `pipeline_state` only; human must still approve via console (publish checklist) before `resources.editorial_status=published`.

### Post-approval sync

| Step | Component | Action |
|---|---|---|
| 8. Human approve | Console | Write `resources/{resource_code}` with `editorial_status: "published"`, provenance fields |
| 9. Immediate sync | Console `trySyncAfterApprove` | POST Compendium via bridge |
| 10. Batch catch-up | `sync-to-compendium` job | `scripts/sync.py` every 30 min (scheduled) for unsynced published rows |

---

## 5. HUMAN-IN-THE-LOOP

### Console role

Next.js app at `console/` deployed to Cloud Run (`console-791873451733.us-central1.run.app`). Passcode login via `CONSOLE_LOGIN_SECRET` → session cookie `cothesis_session` (`console/lib/auth.ts`).

### What the human sees

| Page | Path | Content |
|---|---|---|
| **Dashboard** | `/dashboard` | Pipeline stats, sync status, session stats |
| **Review queue** | `/review` | Pending items (`status=pending`, `routing≠auto_accept`); filters by type, quality, methodology, QA presets |
| **Review detail** | `/review/[id]` | Draft editor, taxonomy editor, Compendium card preview, QC panel scores, pipeline inspector (Quality / Panel / Classification / Enrichment / Provenance tabs), QA audit banner |
| **Pipeline** | `/pipeline` | Active runs from `pipeline_state` |
| **Pipeline record** | `/pipeline/[resourceCode]` | Per-resource stage timeline |
| **Published** | `/resources` | Ratified resources + Compendium sync badges |
| **Prompt lab** | `/prompt-lab` | Prompt proposals from failure bucket |

### Human actions

| Action | Server action | Firestore effect |
|---|---|---|
| **Approve & publish** | `approveItem` | `resources/{code}` ← edited draft + `editorial_status: "published"` + provenance; `review_queue` → `approved`; optional immediate Compendium POST |
| **Bulk approve** | `bulkApproveAsDrafted` | Same, with publish checklist preflight |
| **Reject** | `rejectItem` | `review_queue` → `rejected`; `resources` → `archived`; `pipeline_state` → `hitl_rejected` |
| **Requeue** | `requeueItem` | `review_queue` → `requeued` with stage hint; may write `eval_failure_bucket` |
| **Undo approve** | `undoApprove` | Revert to `pending` / `proposed` (time-limited toast) |
| **Reopen** | `reopenForReview` | Re-enqueue published resource for amendment |
| **Flag taxonomy / Send to lab** | `flagTaxonomyError`, `sendToPromptLab` | `eval_failure_bucket` entry |
| **Manual sync** | `syncToCompendium`, `syncBatchToCompendium` | POST + update `compendium_synced_at`, `compendium_id`, `compendium_url` |

### Publish checklist (`console/lib/checklist.ts` / `agents/shared/checklist.py`)

Required before approve: non-empty `editorial_description`, ≥1 live platform methodology code (type-aware), `quality_score ≥ 60`, URL present, reviewer identity. Methodology optional for: `software`, `community`, `funding`, `dataset`, `template`, `visual_reference`.

### AI-proposes / human-ratifies model

Agents produce drafts with `editorial_status: "proposed"`. Human edits descriptions, taxonomy, badges; sets `editorial_reviewed_by` / `editorial_reviewed_at`. Only then does Compendium sync run.

---

## 6. DEPLOYMENT TOPOLOGY

```
┌─────────────────────────────────────────────────────────────────────────┐
│  GCP project: cothesis-curation-agent                                   │
│                                                                         │
│  us-central1                          global                            │
│  ┌──────────────────────┐            ┌─────────────────────────────┐  │
│  │ Cloud Run: cothesis- │            │ Vertex AI (Gemini 3.x)      │  │
│  │ agent (PRIVATE)      │──models───▶│ GOOGLE_CLOUD_LOCATION=global│  │
│  │ --no-allow-unauth    │            └─────────────────────────────┘  │
│  │ SA: agent-runtime    │            ┌─────────────────────────────┐  │
│  │ ADK 2.1.x + /run UI  │            │ Vertex AI Search datastore  │  │
│  └──────────────────────┘            │ cothesis-methodology-       │  │
│  ┌──────────────────────┐            │ grounding (global collection)│  │
│  │ Cloud Run: console   │            └─────────────────────────────┘  │
│  │ (PUBLIC + passcode)  │                                              │
│  │ min-instances=1      │            ┌─────────────────────────────┐  │
│  └──────────┬───────────┘            │ Firestore (default,         │  │
│             │ reads/writes           │ us-central1)                │  │
│             └───────────────────────▶│ drafts, draft_records,      │  │
│                                      │ review_queue, resources,    │  │
│  ┌──────────────────────┐            │ pipeline_state, …           │  │
│  │ Cloud Run Jobs:      │            └─────────────────────────────┘  │
│  │ • run-batch          │                                              │
│  │ • sync-to-compendium │            ┌─────────────────────────────┐  │
│  │ • prompt-lab-run     │            │ Secret Manager              │  │
│  │ • run-benchmark      │            │ vertex-datastore-id,        │  │
│  └──────────────────────┘            │ mcp-server-url/key,         │  │
│                                        │ console-login,              │  │
│  Cloud Scheduler ──▶ Jobs            │ compendium-import-url,      │  │
│  (batch 2×/day, sync 30min)          │ import-api-key              │  │
│                                        └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │                                    │
         │ MCP SSE (private)                  │ POST /api/import/json
         ▼                                    ▼
   MCP server (17 APIs)              CoThesis Compendium (live)
         │
         ▼
   Railway Postgres (enrichment_queue)
```

| Service | URL / name | Auth |
|---|---|---|
| Agent API | `https://cothesis-agent-791873451733.us-central1.run.app` | Private (`--no-allow-unauthenticated`); IAP planned; OIDC for Scheduler |
| Console | `https://console-791873451733.us-central1.run.app` | Public Cloud Run invoker; app passcode (`cothesis-demo-2026` demo value) |
| Runtime SA | `agent-runtime@cothesis-curation-agent.iam.gserviceaccount.com` | `aiplatform.user`, `discoveryengine.viewer`, `datastore.user`, `secretmanager.secretAccessor`, `logging.logWriter` |
| Firestore | Default DB, `us-central1` | Console + agents via ADC / SA |
| Vertex AI Search | `locations/global`, datastore `cothesis-methodology-grounding` | Via `VERTEX_DATASTORE_ID` secret |
| Gemini endpoint | `GOOGLE_CLOUD_LOCATION=global` | All LLM calls |

---

## 7. DUAL-MODE ARCHITECTURE

### Interactive mode

| Aspect | Detail |
|---|---|
| **Entry** | `adk web agents/` or ADK `/run` on deployed Cloud Run agent |
| **Orchestrator** | `LlmAgent` `root_agent` (`agents/pipeline/agent.py`) — `gemini-3.1-pro-preview` |
| **Control flow** | LLM decides tool invocation order via natural-language instructions (Mode A: skip discovery; Mode B: discovery first) |
| **Sub-agents** | Wrapped as `AgentTool`: grounding, discovery, appraisal, classification, editorial, reconciliation, qc_panel, arbiter |
| **Strengths** | Exploratory curation, demo walkthrough, judge-facing ADK UI, grounding queries |
| **Weakness** | Non-deterministic — may stop after early stages; unacceptable for unattended batch |

### Production batch mode

| Aspect | Detail |
|---|---|
| **Entry** | `python -m scripts.run_batch` or Cloud Run Job `run-batch` |
| **Orchestrator** | `run_pipeline()` in `agents/pipeline/deterministic.py` |
| **Control flow** | Python hard-sequences stages; LLM used only for appraisal/classification/editorial JSON judgments (`_judge_with_retry`); arbiter is pure Python |
| **Queue source** | Railway Postgres `compendium.enrichment_queue` JOIN `import_candidates` |
| **Strengths** | Every stage mandatory; every Firestore write guaranteed; retry/fallback models; dead-source and appraisal-failure short-circuits to `review_queue` |
| **Why both exist** | Same prompts and model tiers; interactive for exploration and demos; deterministic for scheduled production volume and eval reproducibility |

**Note:** `scripts/batch.py` header still documents legacy ADK `/run` HTTP path; current implementation calls `run_pipeline()` in-process (verified in `run_batch.py` comments and `run_batch` function).

---

## 8. FULL TECHNICAL SPEC

### 8.1 Repository layout

```
agents/
  agent.py                 # re-exports root_agent
  pipeline/
    agent.py               # LlmAgent orchestrator
    deterministic.py       # production run_pipeline()
  discovery/ appraisal/ classification/ editorial/
  reconciliation/ qc_panel/ arbiter/ grounding/
  enrichment/              # free API enrichment (batch)
  shared/                  # Firestore, schema, bridge, HITL, taxonomy
  prompts/                 # agent system prompts (*.md)
console/
  app/                     # Next.js App Router pages + server actions
  lib/                     # Firestore queries, auth, checklist, compendium sync
  components/              # Review UI, pipeline inspector, dashboard
scripts/
  batch.py run_batch.py    # enrichment queue batch
  sync.py sync_to_compendium.py  # Compendium push
  deploy_*.sh              # Cloud Run deploy helpers
docs/
  ARCHITECTURE.md          # source architecture summary
  SCHEMA.md                # record shapes
  OPERATIONS.md            # GCP runbook
```

### 8.2 Agent tool surfaces

| Agent | Tools |
|---|---|
| Discovery | `search_openalex`, `search_pubmed`, optional `MCPToolset` |
| Appraisal | `fetch_openalex`, `fetch_pubmed`, `write_assessment` |
| Classification | `validate_classification` |
| Editorial | `check_jargon`, `validate_editorial` |
| Reconciliation | `check_duplicate`, `assemble_record` |
| QC Panel | `run_deterministic_checks`, `score_dimension`, `aggregate` |
| Arbiter | `route`, `write_review_queue`, `check_review_status` |
| Grounding | `VertexAiSearchTool` only |

### 8.3 QC panel evaluators

**Deterministic (no LLM):**

- `ai_pattern_scanner` — regex AI-tell patterns
- `voice_reviewer` — banned brand phrases
- `plain_jargon_check` — jargon terms in plain description
- `badge_check` — canonical badge set (`agents/shared/codes.py`)
- `taxonomy_qc_check` — taxonomy validation rules

**Dimension evaluators (from appraisal):** relevance, accuracy, authority, currency, accessibility, practical_utility — pass if score ≥ 60.

**Panel agreement:** fraction of evaluators with `pass: true` (empty panel → 0.0).

### 8.4 Resource code derivation

```python
# agents/pipeline/deterministic.py — derive_resource_code()
slug = kebab-case(title)[:52]
hash = sha1(doi or url or title)[:6]
resource_code = f"{slug}-{hash}"
```

### 8.5 Record lifecycle states

```
discovered → appraised → classified → edited → reconciled → qc_panel → arbiter
  ├─ auto_exclude → pipeline_state.outcome (terminal)
  ├─ auto_accept → pipeline_state.outcome (awaiting human publish checklist)
  └─ review_needed → review_queue (pending)
        ├─ approved → resources (published) → Compendium sync
        └─ rejected → resources (archived), pipeline_state (hitl_rejected)
```

### 8.6 Model tiering rationale

| Tier | Default model | Agents / stages |
|---|---|---|
| Flash-Lite | `gemini-3.1-flash-lite` | Discovery, classification, reconciliation, QC panel |
| Flash | `gemini-3.5-flash` | Appraisal, editorial, grounding |
| Pro | `gemini-3.1-pro-preview` | Orchestrator shell, arbiter agent (routing itself is code) |

Fallback on 504: cross-fallback among Gemini 3.x preview models (`_FALLBACK_MODEL` in `deterministic.py`). LLM timeout: `LLM_TIMEOUT_MS=90000`.

### 8.7 Compendium bridge mapping

`to_compendium_record()` (`agents/shared/compendium_bridge.py`) emits:

- Core: `title`, `url`, `editorial_description`, `access_type`, `doi`/`isbn`/`pmid`
- Tags: vocabulary-native `{ taxonomy, code, confidence }` from methodology, specialty, thesis stage, foundation_skill, cross_specialty_domain
- `source_tool: "claude"` (Compendium import API convention)

### 8.8 Console ↔ agent boundary

Console does **not** call the private agent API for routine HITL. It reads/writes Firestore directly via Firebase Admin SDK. Compendium sync uses server-side `COMPENDIUM_IMPORT_URL` + `IMPORT_API_KEY` from Secret Manager. Agent Cloud Run is for interactive ADK sessions and (legacy doc) Scheduler triggers.

### 8.9 Scheduled jobs (Cloud Scheduler → Cloud Run Jobs)

| Job | Script entrypoint | Schedule (documented) |
|---|---|---|
| `run-batch` | `python -m scripts.run_batch` | Twice daily |
| `sync-to-compendium` | `python -m scripts.sync_to_compendium` | Every 30 minutes |
| `run-benchmark` | `scripts/run_benchmark.py` | Weekly (Sun 21:00 UTC) |
| `prompt-lab-run` | `scripts/prompt_eval_loop.py` | On demand |

### 8.10 Security posture

- Agent + MCP: private network path; no secrets in repo
- Console: public invoker, application-level passcode; secrets server-side only
- Outbound URL safety: `agents/shared/url_safety.py` blocks SSRF on enrichment/source checks
- Human-gated: `gcloud billing`, IAM grants, `--force`, `--allow-unauthenticated` on agent

### 8.11 Key file index

| Concern | Primary files |
|---|---|
| Orchestrator (interactive) | `agents/pipeline/agent.py` |
| Orchestrator (batch) | `agents/pipeline/deterministic.py` |
| Routing gate | `agents/arbiter/tools.py` |
| Firestore collections | `agents/shared/firestore_utils.py` |
| Review queue write | `agents/shared/hitl.py` |
| Compendium transform | `agents/shared/compendium_bridge.py` |
| Batch queue | `scripts/batch.py`, `scripts/run_batch.py` |
| Compendium sync | `scripts/sync.py`, `scripts/sync_to_compendium.py` |
| Console approve/reject | `console/app/review/actions.ts` |
| Firestore queries | `console/lib/firestore.ts` |
| Deploy | `scripts/deploy_console.sh`, `scripts/deploy_batch_job.sh`, `docs/OPERATIONS.md` |

---

*Generated for Devpost submission. For operational runbooks see `docs/OPERATIONS.md`; for record schemas see `docs/SCHEMA.md`.*
