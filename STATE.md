# STATE — live build state (update after every task)

> On "continue", read this file first and resume. Keep the modified-file list and test/deploy commands here so they survive compaction.

## Current phase
Day 4 — complete. Ready for Day 5 (console + dashboard).

## Completed
- [x] **Day 4 QC panel + arbiter + HITL + gold eval set** — arbiter: deterministic routing on 0-1 signals (relevance_score, classification_confidence) + 0-100 signals (quality_score, ai_confidence) + panel_agreement; 9 routing tests green; qc_panel: ai_pattern_scanner + voice_reviewer + plain_jargon_check + badge_check + 6 dimension scoring; HITL: write_review_queue_item / get_review_status Firestore tools; gold eval set: 20 cases (4 methods × 5 types), tool trajectory + rubric criteria; eval_config.json: tool_trajectory_avg_score ≥ 0.7, rubric_quality ≥ 0.7; full pipeline wires 8 agents via AgentTool; 158/158 tests green.
- [x] **Comprehensive test pass** — 142 tests, 87% coverage; added test_agents_config, test_discovery_tools (mocked HTTP), test_code_mapping (RS→SYN EVAL.md requirement), test_publish_checklist (EVAL.md requirement), test_appraisal_http, test_pipeline_integration, test_editorial_parse; added agents/shared/checklist.py (publish gate); zero LLM calls in test suite.
- [x] **Day 3 classification + editorial + reconciliation** — ClassificationResult (14 types, platform codes enforced, THESIS stages, skill_codes); EditorialOutput (editorial_description, summary, editorial_description_plain, proposed_badges max-3 enforced, difficulty_level); Reconciliation (title_similarity 0.9, assemble_draft_record with summary + skill_codes); code-reviewer found and fixed 3 bugs (Pydantic v2 list max, summary dropped in assembly, skill_codes missing); 51/51 tests green.
- [x] **Day 2 grounding + discovery + appraisal** — 18 documents uploaded to Vertex AI Search (4 methodology cards + 14 seed resources); grounding_agent (VertexAiSearchTool isolated); discovery_agent (OpenAlex + PubMed tools, MCPToolset wired for production); appraisal_agent (deterministic APIs + Firestore write); root_agent wires all three via AgentTool; 16/16 tests green.
- [x] **Day 1 scaffold** — ADK 2.1.0, Python 3.12 venv, skeleton pipeline agent, `adk web agents/` serving (HTTP 200), pre-commit blocking secrets, Firestore (default, us-central1), Vertex AI Search datastore (`cothesis-methodology-grounding`, global), GCP services enabled, git init + main branch.
- [x] Data drop-in: 13 field maps → `docs/field_maps/`
- [x] Data drop-in: 65 canonical entity files → `docs/reference/entities/` (May 17 — authoritative field shape)
- [x] Data drop-in: `database_schema_v4.md`, `compendium_enrichment_qc_spec.md`, `ENRICHMENT_SPEC_2026-05-29.md`, `gateway.md`, `cothesis_compendium_category_cross_reference.md` → `docs/reference/`
- [x] Data drop-in: `cothesis_complete_methodology_taxonomy.json`, `cothesis_thesis_stages.json` → `data/methodologies/_source/`
- [x] Data drop-in: 4 MRP full corpus JSONs (SYN-01/02, OBS-01, EVAL-01) → `data/methodologies/_mrp_full/` (staged optional, NOT indexed for MVP)
- [x] Data drop-in: `compendium_demo_content.json` → `data/resources_seed/` (14 records, all 14 resource types)
- [x] Methodology cards: `data/methodologies/syn-01.md`, `syn-02.md`, `obs-01.md`, `eval-01.md`
- [x] Schema reconciliation: `docs/reference/SCHEMA_RECONCILIATION.md`
- [x] `docs/SCHEMA.md` — fully updated to canonical entities (8 edits applied; `editorial_description_plain` preserved; `ebm_level` articles-only)
- [x] `docs/AGENTS_SPEC.md` — all field names updated to canonical
- [x] `agents/prompts/appraisal.md` — canonical field names: `ai_confidence` 0-100, `thesis_stage_signals`, `relevance_to_discipline_codes`, `proposed_badges`, `ai_subtype_signal`, `trainee_suitability_score`, `pipeline_run_id`; `ebm_level` articles-only
- [x] `agents/prompts/editorial.md` — `summary` (not `editorial_description_long`), `proposed_badges` (not `editorial_badges`); `editorial_note` flagged as human-only
- [x] `agents/prompts/classification.md` — `resource_type_code`, `resource_subtype_code`, `stage_codes`, `discipline_codes`
- [x] `agents/prompts/reconciliation.md` — canonical-name crosswalk added
- [x] `.claude/rules/console.md` — four-slot display contract: short/long/plain/Editor's note
- [x] `.env` — created; `VERTEX_DATASTORE_ID` empty (Day 1); `GOOGLE_CLOUD_LOCATION=global`
- [x] `research_database` resolved: subtype of `dataset` (v2.2) — 14-type enum unchanged

## In progress
- (none)

## Blockers / waiting on human
- (none — Day 1 complete)

## Decisions needing the human
- (none open)

## Next task
Day 5: Next.js + shadcn/ui review console (approve/reject → writes human-ratified Resource fields + provenance) + progress dashboard. plain description renders as labelled breakout card. editorial_note optional Editor's block on featured resources.

## Modified files this session
- `docs/field_maps/field_mapping_*.md` — 13 files added
- `docs/reference/` — 5 reference specs + SCHEMA_RECONCILIATION.md added
- `docs/reference/entities/` — 65 canonical entity files added
- `data/methodologies/_source/` — 2 JSON files added
- `data/methodologies/_mrp_full/` — 4 MRP JSON files added
- `data/methodologies/syn-01.md`, `syn-02.md`, `obs-01.md`, `eval-01.md` — new
- `data/resources_seed/compendium_demo_content.json` — added
- `docs/SCHEMA.md` — rewritten to canonical schema
- `docs/AGENTS_SPEC.md` — field names updated
- `agents/prompts/appraisal.md` — canonical field names + ebm_level
- `agents/prompts/editorial.md` — summary, proposed_badges, editorial_note note
- `agents/prompts/classification.md` — canonical field names
- `agents/prompts/reconciliation.md` — crosswalk added
- `agents/prompts/arbiter.md` — explicit `classification_confidence`/`relevance_score` names; do-not-route-on-ai_confidence note
- `.claude/rules/console.md` — four-slot display contract
- `.env` — created; `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent`
- `.env.example` — project ID updated to match
- `docs/SCHEMA.md` — two-layer score model section added (0-1 routing vs 0-100 quality/display)
- `pyproject.toml` — new; google-adk>=2.1.0,<2.2.0; Python 3.12; setuptools build
- `.python-version` — 3.12
- `.venv/` — Python 3.12 virtualenv (gitignored)
- `agents/pipeline/__init__.py`, `agents/pipeline/agent.py` — skeleton root agent
- `.env` — `VERTEX_DATASTORE_ID` set; `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent`

## Key commands
- Scaffold: `uvx google-agents-cli setup`
- Local dev UI: `adk web agents/`
- Run evals: `adk eval` (see docs/EVAL.md) or the /run-evals skill
- Deploy agent: `adk deploy cloud_run ...` (see docs/OPERATIONS.md)
- Secret scan: `gitleaks git -v`
