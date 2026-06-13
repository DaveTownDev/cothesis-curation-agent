# CoThesis Curation Agent — Judge Guide

Quick orientation for evaluating the hackathon submission. For a scripted 5-minute video walkthrough, see [`DEMO_SCRIPT.md`](./DEMO_SCRIPT.md).

---

## What this is

A multi-agent curation pipeline (ADK 2.1 on Vertex AI) that enriches research-methodology resources and routes uncertain drafts to a human review console. Curator-approved records can be pushed to the live **CoThesis Compendium** — a free, openly searchable archive aimed at trainees who do not already know formal methodology jargon.

**Demo scope:** four MVP methodologies (Narrative Systematic Review, Scoping Review, Retrospective Chart Review, Clinical Audit). The pipeline and taxonomy support **148 methodologies** and **53 specialties** aligned with the live Compendium.

**Built, not planned:** **459** deterministic pytest tests, **90** commits, ADK gold eval **20/20** cases (`eval/baseline.json`), demo seed **12** real resources through the full pipeline.

---

## Try it yourself

| Surface | URL | Access |
|---|---|---|
| **Review console** | https://console-791873451733.us-central1.run.app | Passcode: `cothesis-demo-2026` |
| **Public Compendium** | https://compendium-web-production.up.railway.app | Open (no login) |
| **Cloud Trace** | https://console.cloud.google.com/traces/list?project=cothesis-curation-agent | GCP project access (optional) |
| **Agent API** | https://cothesis-agent-791873451733.us-central1.run.app | Private (403 without auth; IAP deferred) |
| **Source** | https://github.com/DaveTownDev/cothesis-curation-agent | Private — request access |

---

## Console layout (revision `console-00025-jnp`)

**Top bar (cream):** CoThesis logo · **Dashboard** · **Review queue** · **Published** · **Pipeline** · **Prompt lab** · **Launch Research Directory** (opens the public Compendium in a new tab).

**White sub-bar (per page):** page-specific actions — e.g. bulk approve on the queue, **Sync to Compendium** on Published, run filters on Pipeline. Queue **filters** (type, methodology, quality, sort) sit **between the page header and the table**, not in the sub-bar.

### Pages to click through

1. **Dashboard** (`/dashboard`) — queue depth, oldest item age, sync stats, eval scoreboard (ADK benchmark), session stats for the current reviewer.
2. **Review queue** (`/review`) — items the arbiter routed to human review (`review_needed`). Open any row for the 3-pane workspace.
3. **Review detail** (`/review/[id]`) — the core HITL experience:
   - **Left:** three agent-drafted description fields — **short** (`editorial_description`), **long** (`summary`), **plain-language** (`editorial_description_plain`) — plus a human-only **editor's note** slot. Inline editing on all cards.
   - **Centre:** **Pipeline Inspector** — tabs: Quality, Panel, Classification, Enrichment, Provenance (stage timeline, run ID, model version).
   - **Right:** decision pane — ratify badges, quality threshold, **Approve & publish**, reject, or requeue to a pipeline stage. QA report shortcuts (quick reject / send back) work from the inspector. Eval actions: export gold case, flag taxonomy error, send to prompt lab.
   - Keyboard shortcuts and bulk actions on the queue list.
4. **Published** (`/resources`) — curator-approved records with Compendium sync status (`pending` / `synced` / error). **Sync to Compendium** per row or in batch — this is the publish-to-live step. **Edit** opens the catalog editor.
5. **Pipeline** (`/pipeline`) — every resource the deterministic orchestrator has processed, with stage timeline. **View / edit** opens the catalog editor for any record regardless of review status.
6. **Prompt lab** (`/prompt-lab`) — prompt-improvement proposals from the failure bucket; diff viewer with approve/reject (writes instructions only — never auto-merges prompts).
7. **Catalog editor** (`/pipeline/[resourceCode]`) — view or amend any pipeline record; save draft, publish, unpublish, republish, push to Compendium.

---

## What to look for (rubric alignment)

Google for Startups AI Agents Challenge scoring weights (approximate):

| Weight | Dimension | Where to see it in this project |
|---|---|---|
| **30%** | **Technical depth** | Dual-mode orchestration (`agents/pipeline/agent.py` vs `deterministic.py`); tiered Gemini 3.x on Vertex global; Vertex AI Search grounding; **459 pytest** + ADK **20/20** eval; Cloud Trace waterfall |
| **20%** | **Innovation** | Plain-language equity layer (novice-vocabulary search surface); QC evaluator panel + disagreement-based routing; insight that production pipelines need code-sequenced orchestration when every stage is mandatory |
| **20%** | **Impact** | Real backlog (1,479+ ingested resources, 2,505+ queued); mission for trainees outside well-resourced institutions; honest free-archive + paid-product funnel |
| **20%** | **Demo & presentation** | Pre-seeded console data; 5-tab Pipeline Inspector; approve → manual sync → live Compendium; optional Cloud Trace span waterfall |
| **10%** | **Google stack usage** | ADK 2.1 multi-agent, Cloud Run (agent + console + Jobs), Firestore draft store, Secret Manager, Cloud Scheduler, OpenTelemetry → Cloud Trace |

| Theme | Where to see it |
|---|---|
| **Multi-agent orchestration** | Pipeline Inspector → Provenance tab; Cloud Trace waterfall |
| **Grounded classification** | Pipeline Inspector → Classification; taxonomy codes match `data/taxonomy/live_*.json` |
| **Quality control panel** | Pipeline Inspector → Panel + Quality tabs |
| **Human-in-the-loop** | Review queue → approve/reject/requeue; only uncertain items surface (`auto_accept` does not enqueue) |
| **Equity / findability** | Plain-language description card on review detail |
| **Production path** | Approve → Published → **Sync to Compendium** (manual push; scheduled job catches up unsynced rows) |
| **Deterministic batch mode** | `/pipeline` provenance; `agents/pipeline/deterministic.py` (`run_pipeline()` — code-sequenced, LLM for judgments only) |
| **Eval credibility** | Dashboard eval card; `eval/baseline.json`; `scripts/run_benchmark.py --check-regression` |

---

## Demo data

The console is backed by **real Firestore data**, not mocks. For judging, data is pre-seeded so you are not waiting on a ~45s/resource live pipeline run:

```bash
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo
```

Typical seed result: **12 resources** through the full pipeline — **10** in the review queue (`review_needed`), **2** auto-accepted by the arbiter, **0** errors (~7 minutes).

**Do not** run the live batch pipeline during a demo video; use pre-seeded queue data.

---

## Compendium sync

**Approve & publish** writes the ratified record to Firestore (`resources` collection, `editorial_status: "published"`). It does **not** automatically POST to the Compendium — sync is a deliberate curator action.

To push live: go to **Published** (`/resources`) and click **Sync to Compendium** (per row or batch). Sync status badges show `pending` / `synced` / error. A Cloud Run Job (`sync-to-compendium`, every 30 min) and CLI (`python -m scripts.sync_to_compendium`) catch up any unsynced published rows.

Field mapping and HTTP contract: [`COMPENDIUM_INTEGRATION.md`](./COMPENDIUM_INTEGRATION.md).

---

## Architecture (one paragraph)

Eight specialist ADK agents (discovery → appraisal → classification → editorial → reconciliation → QC panel → arbiter) run on tiered **Gemini 3.x** models on the **Vertex AI global** endpoint: `gemini-3.1-pro-preview` (orchestrator shell), `gemini-3.5-flash` (appraisal, editorial, grounding), `gemini-3.1-flash-lite` (discovery, classification, reconciliation, QC panel). **Interactive** exploration uses an `LlmAgent` orchestrator (`adk web` / ADK `/run` UI). **Batch** curation uses `run_pipeline()` in `agents/pipeline/deterministic.py` — code-sequenced because LLM orchestrators non-deterministically skip mandatory stages. The arbiter routing gate is pure Python thresholds (`agents/arbiter/tools.py`), not a model call. **Discovery** uses MCP connectors to PubMed, bioRxiv, and ClinicalTrials.gov in production; **enrichment** merges metadata via direct HTTP APIs (OpenAlex, PubMed, CrossRef, Unpaywall, iCite, and type-specific free-tier sources in `agents/enrichment/sources.py`). Observability: OpenTelemetry → Cloud Trace.

Specs: [`AGENTS_SPEC.md`](./AGENTS_SPEC.md), [`ARCHITECTURE_BRIEF.md`](./ARCHITECTURE_BRIEF.md), [`BUILD_PLAN.md`](./BUILD_PLAN.md), [`OPERATIONS.md`](./OPERATIONS.md).

---

## What's live vs in progress

| Live now | In progress / deferred |
|---|---|
| Full deterministic pipeline + Firestore draft store | Agent Cloud Run IAP for judge ADK UI access |
| Console HITL with passcode gate | Full 1,512-record live reprocess (ops tooling exists) |
| Manual + scheduled Compendium sync | Premium enrichment APIs (Altmetric, ISBNdb) — optional keys only |
| ADK eval 20/20 + regression-gated benchmark | Prompt lab GCP Job deploy (code + console UI wired) |
| Prompt lab console page + failure-bucket writes | Auto-sync on approve (intentionally manual for curator control) |

---

## Known limitations (honest)

- Agent Cloud Run service is **private** (`--no-allow-unauthenticated`); **IAP is deferred** — judges use the public console, not the ADK `/run` UI.
- Console auth is a **passcode** (`CONSOLE_LOGIN_SECRET`), not Google Identity-Aware Proxy.
- Premium enrichment APIs (Altmetric, ISBNdb, etc.) are optional; MVP article paths use free Tier-1 HTTP sources.
- Background reprocess of all ~1,500 live Compendium records is ops tooling, not required for the demo.
- `compendium-import-url` visibility endpoint may 404 until the Compendium deploys unpublish support.
- Interactive `adk web` path is non-deterministic and slow (~45s/resource) — demo uses pre-seeded batch output, not live runs.
