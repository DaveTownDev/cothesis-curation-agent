# CoThesis Curation Agent — Demo Script (5 min)

**Record against pre-seeded data — do NOT run the live pipeline in the video.**
The console, Cloud Trace, and Compendium sync are all reliable. The batch
pipeline is deterministic but slow (~45s/resource), so the queue is pre-populated.

## Setup before recording
- Console logged in: https://console-791873451733.us-central1.run.app (passcode `cothesis-demo-2026`)
- Cloud Trace open: https://console.cloud.google.com/traces/list?project=cothesis-curation-agent
- Compendium open: https://compendium-web-production.up.railway.app
- Seed data already loaded (`python -m scripts.seed_demo`): ~12 resources across the 4 methodologies in the review queue + pipeline_state.
- Screen recorder ready (Loom / OBS / QuickTime).

---

## Segment 1 — The problem (30s)

**Say:** "The CoThesis Compendium is a free, openly-searchable archive of research-methodology resources for medical trainees — especially those outside well-resourced institutions. Our own library has thousands of resources queued and not one has reached publishable quality, because the editorial work — appraising, classifying, and writing a findable description for each — doesn't scale by hand. This agent does that work."

**Show:** the dashboard — point to the queue count and 'oldest queued' card.

---

## Segment 2 — The architecture (45s)

**Say:** "Eight specialist ADK agents on Gemini 3.x: discovery, appraisal, classification, editorial, reconciliation, a QC evaluator panel, and an arbiter routing gate. Each runs on a model tier matched to its job — Flash-Lite for high-volume structured work, Flash for appraisal and editorial writing, 3.1 Pro for the arbiter."

**Say (the engineering insight):** "We run it in two modes that share the same agents and models. Interactive exploration uses an LLM orchestrator you can talk to. But for unattended batch curation we use a *code-sequenced* orchestrator — we found LLM orchestrators non-deterministically skip stages, and when every quality check and every write is mandatory, the LLM should make the judgments while code owns the sequencing. The arbiter's routing decision is pure code, not a model call — it's a deterministic threshold, not a matter of opinion."

**Show:** the `/pipeline` page — the provenance of every resource the pipeline has processed, each with its stage timeline.

---

## Segment 3 — Console walkthrough (2 min)

**Navigate:** Dashboard → Queue.

**Show the queue:** filters (type / methodology / quality / sort), the routing-signal mini-bars (relevance + classification confidence), quality scores.

**Open one `review_needed` item.** Walk the 3-pane review:
- **Left:** the four description slots. Highlight the **plain-language card** — "this is the jargon-free layer: the words a research-naive trainee would actually type. A search that only works if you already know 'retrospective chart review' is exactly the barrier we're removing." Click the pencil on a description to show **inline editing**.
- **Center:** the **Pipeline Inspector** — flip through the four tabs: Quality (dimensions with reasoning), Panel (each QC evaluator's pass/fail + reasoning), Classification (the model's relevance reasoning), Provenance (stage timeline + run ID + model version).
- **Right:** the decision pane — ratify badges, the quality-threshold indicator, then **Approve & publish**.

**Approve it.** Then go to **Published** (`/resources`) and show it there with your name as reviewer and a 'pending sync' badge.

---

## Segment 4 — Cloud Trace (30s)

**Navigate:** Cloud Trace → latest trace.

**Say:** "Every agent call, model call, and tool call emits an OpenTelemetry span. This is the full audit trail of one resource moving through the pipeline."

**Show:** the span waterfall.

---

## Segment 5 — Compendium sync (30s)

**Say:** "Approved resources sync to the live Compendium every 30 minutes — the bridge maps our internal record to the Compendium's import format."

**Show:** the approved resource live on the public Compendium (or the `/resources` page flipping to a 'synced' badge).

---

## Segment 6 — The mission (15s)

**Say:** "The free archive answers 'what exists and what is this called' — in the learner's own words. The curation agent is what makes building it at scale possible for a small team."

**End on:** the dashboard or the plain-language card.

---

## Tips
- Show real data, not mockups — the seeded queue is real pipeline output.
- Don't run the live pipeline in the video (the interactive orchestrator is non-deterministic and slow). Everything you demo — queue, review, approve, trace, sync — is reliable.
- Passcode for judges: `cothesis-demo-2026`.
