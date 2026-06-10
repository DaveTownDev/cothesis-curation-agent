# CoThesis Curation Agent — Demo Script (5 min)

**Record against pre-seeded data — do NOT run the live pipeline in the video.**
The console, Cloud Trace, and Compendium sync are reliable. The batch pipeline is deterministic but slow (~45s/resource), so the queue is pre-populated.

## Setup before recording

- Console logged in: https://console-791873451733.us-central1.run.app (passcode `cothesis-demo-2026`)
- Cloud Trace open: https://console.cloud.google.com/traces/list?project=cothesis-curation-agent
- Compendium open: https://compendium-web-production.up.railway.app
- Seed data loaded: `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo` → 12 resources, 10 in review queue, 2 auto-accepted (~7 min)
- Screen recorder ready (Loom / OBS / QuickTime)

**Console layout:** cream top bar with Dashboard · Review queue · Published · Pipeline · **Launch Research Directory** (public Compendium). Each page has a white sub-bar for page actions; queue filters sit between the header and the table.

---

## Segment 1 — The problem (30s)

**Say:** "The CoThesis Compendium is a free, openly searchable archive of research-methodology resources for medical trainees — especially those outside well-resourced institutions. Our own library has thousands of resources queued and not one has reached publishable quality, because the editorial work — appraising, classifying, and writing a findable description for each — doesn't scale by hand. This agent does that work."

**Show:** **Dashboard** — point to queue count and oldest-queued card.

---

## Segment 2 — The architecture (45s)

**Say:** "Eight specialist ADK agents on Gemini 3.x: discovery, appraisal, classification, editorial, reconciliation, a QC evaluator panel, and an arbiter routing gate. Each runs on a model tier matched to its job — Flash-Lite for high-volume structured work, Flash for appraisal and editorial writing, 3.1 Pro where we need deeper reasoning."

**Say (the engineering insight):** "We run it in two modes that share the same agents and models. Interactive exploration uses an LLM orchestrator you can talk to. For unattended batch curation we use a *code-sequenced* orchestrator — we found LLM orchestrators non-deterministically skip stages, and when every quality check and every write is mandatory, the LLM should make the judgments while code owns the sequencing. The arbiter's routing decision is pure code, not a model call — it's a deterministic threshold, not a matter of opinion."

**Show:** **Pipeline** (`/pipeline`) — provenance of every processed resource; optional click **View / edit** to show the catalog editor for any record.

---

## Segment 3 — Console walkthrough (2 min)

**Navigate:** Dashboard → **Review queue**.

**Show the queue:** filters (type / methodology / quality / sort) between the header and table; routing-signal mini-bars (relevance + classification confidence); quality scores. Mention bulk approve if time allows.

**Open one `review_needed` item.** Walk the 3-pane review:

- **Left:** four description slots. Highlight the **plain-language card** — "this is the jargon-free layer: the words a research-naive trainee would actually type. A search that only works if you already know 'retrospective chart review' is exactly the barrier we're removing." Click the pencil to show **inline editing**.
- **Centre:** **Pipeline Inspector** — flip through tabs: **Quality** (six dimensions + reasoning), **Panel** (each QC evaluator pass/fail), **Classification** (relevance reasoning + taxonomy codes), **Enrichment** (source APIs used), **Provenance** (stage timeline + run ID + model version). Optionally click a QA shortcut under the report to show structured send-back.
- **Right:** decision pane — ratify badges, quality-threshold indicator, then **Approve & publish**.

**Approve it.** Go to **Published** (`/resources`) — show the row with your reviewer name. Sync fires immediately on approve; badge shows `pending` then `synced` (refresh if needed). Click **Edit** to show the catalog editor.

---

## Segment 4 — Cloud Trace (30s)

**Navigate:** Cloud Trace → latest trace.

**Say:** "Every agent call, model call, and tool call emits an OpenTelemetry span. This is the full audit trail of one resource moving through the pipeline."

**Show:** the span waterfall.

---

## Segment 5 — Compendium sync (30s)

**Say:** "When a curator approves, the console POSTs to the live Compendium import API immediately — no waiting for a batch job. The bridge maps our internal record to the Compendium's import format."

**Show:** the approved resource on the public Compendium (or the Published page with a `synced` badge). Optionally click **Launch Research Directory** in the top bar to open the public library.

---

## Segment 6 — The mission (15s)

**Say:** "The free archive answers 'what exists and what is this called' — in the learner's own words. The curation agent is what makes building it at scale possible for a small team."

**End on:** the dashboard or the plain-language card.

---

## Tips

- Show real data, not mockups — the seeded queue is real pipeline output.
- Don't run the live pipeline in the video (interactive orchestrator is non-deterministic and slow). Queue, review, approve, trace, and sync are reliable.
- Passcode for judges: `cothesis-demo-2026`.
- Judge quick-start: [`JUDGE_GUIDE.md`](./JUDGE_GUIDE.md).
