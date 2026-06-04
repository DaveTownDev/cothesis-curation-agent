# ARCHITECTURE

## Data flow
`sources → Discovery → Appraisal → Classification → Editorial → Reconciliation → QC evaluator panel → Arbiter → routing gate → (auto-publish | review queue | human author) → published`, with two monitoring loops feeding back in (source monitoring and link-health).

## Agents (ADK, under one Orchestrator)
- **Discovery** — finds candidate resources per methodology/type using the existing MCP server (17 academic APIs, SearXNG, Crawl4AI). Deterministic-API-first; emits raw metadata. Flash-Lite.
- **Appraisal** — consumes API/tool signals (OpenAlex, PubMed, Semantic Scholar; self-hosted RobotReviewer/URSE/MedJEx for articles) first, then Flash for what's left. Produces quality_score (0-100) and the canonical 6 dimensions with reasoning. Per-type rubric (docs/AGENTS_SPEC.md).
- **Classification** — assigns resource_type (14), subtype, methodology_codes (platform SYN/OBS/EVAL), thesis_stages, foundation skills, specialty_tags, difficulty, access_type, relevance + confidence. Flash-Lite.
- **Editorial** — writes editorial_description (short), editorial_description_long, and editorial_description_plain (jargon-free card); proposes badges (max 3); sets difficulty. Flash; Pro for polish where needed.
- **Reconciliation** — dedup against existing resources (title similarity 0.9; stop, no merge for MVP); assembles the final draft record.
- **QC evaluator panel** — specialist evaluators, one per quality dimension, plus the ready-made members (ai-pattern-scanner, voice-reviewer, claim-verifier, ref_checker). Each scores + reasons. Implemented with ADK eval primitives.
- **Arbiter** — composite score + panel agreement → routing decision via the gate. Pro. Panel disagreement is itself an escalation signal.

## Routing gate (thresholds live here)
Using the calibrated baseline (overridable via env): `IMPORT_RELEVANCE_AUTO_ACCEPT=0.6`, `IMPORT_RELEVANCE_AUTO_EXCLUDE=0.3`, `IMPORT_CONFIDENCE_AUTO_ACCEPT=0.8`, `IMPORT_CONFIDENCE_REVIEW=0.5`, `IMPORT_TITLE_SIMILARITY_THRESHOLD=0.9`.
```
skip_reason set                         -> auto_exclude
confidence >= 0.8 and relevance >= 0.6  -> auto_accept (-> publish gate)
confidence >= 0.8 and relevance < 0.3   -> auto_exclude
confidence < 0.5  OR panel disagreement -> review_needed (human)
else                                    -> review_needed
```
These are the *routing* layer. The 0-100 composite quality_score is the *display* layer (hidden on the card below 60). They are not the same number.

## Monitoring layer
- **Source monitoring** — n8n Cloud watches RSS/source feeds (journals, YouTube, podcasts), dedups, keyword-filters, and enqueues new candidates into Discovery.
- **Link-health** — Cloud Scheduler triggers periodic link checks; classify 404/403/SSL/drift; archival snapshot + retest loop.

## Runtime topology
ADK agents deploy to **Cloud Run** (scale-to-zero), private (`--no-allow-unauthenticated` + IAP). The **Next.js console** is a second Cloud Run service, public with a login gate, calling the agent API via the runtime SA. **Firestore** is the draft store + pipeline-state machine + review queue. **Vertex AI Search** is the grounding datastore. Grounding is isolated in its own sub-agent because `VertexAiSearchTool` is exclusive.

## AI-proposes / human-ratifies
Agents write a draft **AIAssessment** record (`editorial_status: proposed`). The arbiter routes it. The human review console writes the ratified **Resource** fields and the provenance (model, reviewer, timestamps) and moves it `in_review -> published`. See docs/SCHEMA.md.
