# DECISIONS — settled decisions & resolved inconsistencies

## Locked build decisions
- **Region/models:** global endpoint, Vertex AI Search. Public data, so no AU residency requirement. **Model tiering (Gemini 3.x):** arbiter (+ interactive orchestrator) = `gemini-3.1-pro-preview`; appraisal + editorial = `gemini-3-flash-preview`; discovery, classification, reconciliation, QC panel, grounding = `gemini-3.1-flash-lite`. Verified available on the global endpoint via live API call (2026-06-06).
- **ADK is GA** (2.x): pin `google-adk==2.1.x`, never below 2.0.1; verify APIs live via Context7.
- **Deploy to Cloud Run** (not Agent Engine). Judge access via Cloud Run IAP / console passcode; agent API + MCP stay private.
- **Day 0 billing kill-switch** (Pub/Sub + Cloud Function) alongside budget alerts.
- **`VertexAiSearchTool` is exclusive** — isolate grounding in its own sub-agent / AgentTool.
- **Scope:** all 14 resource types fully built; grounding + demo across the 4 MVP methodologies (SYN-01, SYN-02, OBS-01, EVAL-01).

## Resolved inconsistencies (build to the canonical side)
- **quality_score = 0-100** (not 0.0-1.0).
- **6 canonical quality dimensions**: relevance, accuracy, authority, currency, accessibility, practical_utility (not the legacy credibility/clarity/practicality set).
- **Methodology codes = platform** (SYN/OBS/EVAL), not legacy RS/OD display codes. Mapping in docs/TAXONOMY.md.
- **Editorial badges = canonical set**: editors_choice, best_free, best_beginners, best_time_poor, essential, expert_pick (max 3).
- **Editorial = three fields**: short, long, and the jargon-free plain card (`editorial_description_plain`).
- **difficulty_level**: beginner/intermediate/advanced (pipeline does not emit expert/mixed).

## [HUMAN] defaults for the demo (change if desired)
- Dimension weights: equal for the demo; per-type weighting is later.
- Editorial style guide: none exists — the anchor is `data/editorial_examples/editorial_examples.md`.
- Publish checklist: see docs/SCHEMA.md.
- Dedup: stop on duplicate (no merge) for MVP.
- `source_authority` tiering: deferred.

## Editorial voice rules (from the examples review)
Short + long use full terminology, pitched for a trainee with some footing. The plain card is jargon-free. Never judgemental or negative in any field. The plain card explains a method only when teaching it is the resource's purpose. Page renders the plain version as a labelled breakout card beneath the long description.

## Design tokens (confirm against the design system file)
Cream background, forest green `#0E3A27`, primary green `#289642`, teal accent `#03848F`; Newsreader/Lora serif headings, Instrument Sans body.
