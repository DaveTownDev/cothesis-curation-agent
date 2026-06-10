# CoThesis Curation Agent — Judge Guide

Quick orientation for evaluating the hackathon submission. For a scripted 5-minute video walkthrough, see [`DEMO_SCRIPT.md`](./DEMO_SCRIPT.md).

---

## What this is

A multi-agent curation pipeline (ADK on Vertex AI) that enriches research-methodology resources and routes uncertain drafts to a human review console. Approved records sync to the live **CoThesis Compendium** — a free, openly searchable archive aimed at trainees who do not already know formal methodology jargon.

**Demo scope:** four MVP methodologies (Narrative Systematic Review, Scoping Review, Retrospective Chart Review, Clinical Audit). The pipeline and taxonomy support **148 methodologies** and **53 specialties** aligned with the live Compendium.

---

## Try it yourself

| Surface | URL | Access |
|---|---|---|
| **Review console** | https://console-791873451733.us-central1.run.app | Passcode: `cothesis-demo-2026` |
| **Public Compendium** | https://compendium-web-production.up.railway.app | Open (no login) |
| **Cloud Trace** | https://console.cloud.google.com/traces/list?project=cothesis-curation-agent | GCP project access (optional) |
| **Agent API** | https://cothesis-agent-791873451733.us-central1.run.app | Private (403 without IAP) |
| **Source** | https://github.com/DaveTownDev/cothesis-curation-agent | Private — request access |

---

## Console layout (revision `console-00015-496`)

**Top bar (cream):** CoThesis logo · **Dashboard** · **Review queue** · **Published** · **Pipeline** · **Launch Research Directory** (opens the public Compendium in a new tab).

**White sub-bar (per page):** page-specific actions — e.g. bulk approve on the queue, sync controls on Published, run filters on Pipeline. Queue **filters** (type, methodology, quality, sort) sit **between the page header and the table**, not in the sub-bar.

### Pages to click through

1. **Dashboard** (`/dashboard`) — queue depth, oldest item age, sync stats, session stats for the current reviewer.
2. **Review queue** (`/review`) — items the arbiter routed to human review (`review_needed`). Open any row for the 3-pane workspace.
3. **Review detail** (`/review/[id]`) — the core HITL experience:
   - **Left:** four description slots (short, long, **plain-language**, editor's note) with inline editing.
   - **Centre:** **Pipeline Inspector** — tabs: Quality, Panel, Classification, Enrichment, Provenance (stage timeline, run ID, model version).
   - **Right:** decision pane — ratify badges, quality threshold, **Approve & publish**, reject, or requeue to a pipeline stage. QA report shortcuts (quick reject / send back) work from the inspector.
   - Keyboard shortcuts and bulk actions on the queue list.
4. **Published** (`/resources`) — curator-approved records with sync status (`pending` / `synced` / error). Retry sync per row or in batch. **Edit** opens the catalog editor.
5. **Pipeline** (`/pipeline`) — every resource the deterministic orchestrator has processed, with stage timeline. **View / edit** opens the catalog editor for any record regardless of review status.
6. **Catalog editor** (`/pipeline/[resourceCode]`) — view or amend any pipeline record; save draft, publish, unpublish, republish, push to Compendium.

---

## What to look for (rubric alignment)

| Theme | Where to see it |
|---|---|
| **Multi-agent orchestration** | Pipeline Inspector → Provenance tab; Cloud Trace waterfall |
| **Grounded classification** | Pipeline Inspector → Classification; taxonomy codes match `data/taxonomy/live_*.json` |
| **Quality control panel** | Pipeline Inspector → Panel + Quality tabs |
| **Human-in-the-loop** | Review queue → approve/reject/requeue; only uncertain items surface |
| **Equity / findability** | Plain-language description card on review detail |
| **Production path** | Approve → Published → Compendium sync (immediate on approve, not batch-only) |
| **Deterministic batch mode** | `/pipeline` provenance; `agents/pipeline/deterministic.py` (code-sequenced, LLM for judgments only) |

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

On **Approve & publish**, the console POSTs to the Compendium import API immediately (`trySyncAfterApprove`). The Published page shows sync status and supports manual retry. A Cloud Run Job (`sync-to-compendium`) and CLI (`python -m scripts.sync_to_compendium`) catch up any missed rows.

Field mapping and HTTP contract: [`COMPENDIUM_INTEGRATION.md`](./COMPENDIUM_INTEGRATION.md).

---

## Architecture (one paragraph)

Eight specialist ADK agents (discovery → appraisal → classification → editorial → reconciliation → QC panel → arbiter) run on tiered Gemini 3.x models. **Interactive** exploration uses an LLM orchestrator (`adk web`). **Batch** curation uses a **code-sequenced** orchestrator because LLM orchestrators non-deterministically skip mandatory stages. The arbiter routing gate is pure Python thresholds, not a model call. Observability: OpenTelemetry → Cloud Trace.

Specs: [`AGENTS_SPEC.md`](./AGENTS_SPEC.md), [`BUILD_PLAN.md`](./BUILD_PLAN.md), [`OPERATIONS.md`](./OPERATIONS.md).

---

## Known limitations (honest)

- Agent Cloud Run service is **private** (IAP planned; judges use the public console).
- Premium enrichment APIs (Altmetric, ISBNdb, etc.) are optional; MVP article paths use free Tier-1 sources.
- Background reprocess of all ~1,500 live Compendium records is ops tooling, not required for the demo.
- `compendium-import-url` visibility endpoint may 404 until the Compendium deploys unpublish support.
