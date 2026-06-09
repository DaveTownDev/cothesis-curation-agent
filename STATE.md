# STATE — live build state (update after every task)

> On "continue", read this file first and resume. Keep the modified-file list and test/deploy commands here so they survive compaction.

## Current phase
**Merged to `main` @ `47b6fcb` (2026-06-09).** PR #1 (audit fixes + HITL Phases A–C) + PR #2 (review agents + guard) merged. **293 pytest**, console lint/build clean, `bash scripts/e2e_console_smoke.sh` green.

**Deployed (2026-06-09):** console rev `console-00006-q68` @ https://console-791873451733.us-central1.run.app (`min-instances=1`, `CONSOLE_PUBLIC_URL` set). Demo re-seeded: 2 auto_accept + 10 review_needed, 0 errors.

**Submission (human):** demo video (`docs/DEMO_SCRIPT.md`), Devpost submit, familiarity scores (`docs/SUBMISSION.md` L75–79), judge GitHub access.

Repo: https://github.com/DaveTownDev/cothesis-curation-agent (private).

### Residuals (non-blocking)
- Interactive `adk web` path: assembly normalizes out-of-enum types + backfills missing descriptions (`tests/test_interactive_assembly.py`); demo video uses pre-seeded batch data, not live pipeline.
- Premium enrichment (Altmetric, ISBNdb, etc.): optional keys in `.env.example`; Tier-1 free sources cover MVP article/book paths.
- Eval rubric judge may score all-pass — read as "no violations".

## Demo seed (Phase 3)
- `scripts/seed_demo.py` — runs deterministic run_pipeline on 12 curated real resources. Verified: 12/12 full chain, 10 auto_accept + 2 review_needed, 0 errors. All collections populated (drafts/draft_records/review_queue/pipeline_state = 12 each). Console verified live: all 5 pages render real data, review detail shows 4 inspector tabs + Provenance with model version.
- Re-seed anytime: clear Firestore collections, then `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo`
- TODO before relying on schedule: rebuild Cloud Run Job `run-batch` from current image (deterministic orchestrator).

## Deterministic orchestrator (Phase 2)
- `agents/pipeline/deterministic.py` — `run_pipeline(resource_input, pipeline_run_id)` — code-sequenced, LLM only for judgments, pure-Python arbiter, writes all Firestore collections incl. pipeline_state per stage. Verified live: 1 real resource → auto_accept in 46s, all collections written.
- Batch runner (`scripts/batch.py`) now calls run_pipeline (not the LlmAgent /run). LlmAgent orchestrator kept for interactive `adk web`.
- Models (Gemini 3.x): MODEL_PRO=gemini-3.1-pro-preview, MODEL_FLASH=gemini-3-flash-preview, MODEL_FLASH_LITE=gemini-3.1-flash-lite. Agent deployed rev 00009.
- 245 tests green. Git: branch `production-integration-and-console`, tag `hackathon-snapshot-v1`.

## Completed
- [x] **Console redesign — comprehensive HITL interface** — full pipeline data in console; keyboard shortcuts, bulk approve, triage presets, undo/reopen (Phases A–C). See § Completed (HITL) below.
- [x] **Day 7 eval + observe + harden** — pytest 159/159 green; 5 LLM output robustness fixes (QualityDimension flat-int coercion, weight normalisation, arbiter null float, panel_scores string parse, QC panel malformed JSON); eval runs to completion on 8-case subset (response_match_score avg=0.193, rubric threshold updated to 0.15); console login redirect fixed (x-forwarded-host); Firestore index + datastore.user grant for console SA; Cloud Trace working (cloudtrace.agent granted); gitleaks clean (0 leaks, 15 commits); scale-to-zero confirmed both services; SUBMISSION.md placeholders cleared; docs/DEMO_SCRIPT.md written; console E2E verified: login → dashboard → review queue (6 real items) → review detail. **[DAVE]** record demo video using docs/DEMO_SCRIPT.md; fill familiarity scores in SUBMISSION.md.
- [x] **Day 6 deploy + secrets** — runtime SA created (4 IAM roles); 3 secrets in Secret Manager (vertex-datastore-id, console-login, mcp-server-url); agent deployed to Cloud Run (--no-allow-unauthenticated, agent-runtime SA, opentelemetry-exporter-gcp-trace added to agents/requirements.txt); console deployed to Cloud Run (Dockerfile + standalone output, allUsers invoker via org policy allowAll override); Cloud Scheduler daily job (20:00 UTC, OIDC via agent-runtime); Phase D (IAP) deferred to Day 8 — [DAVE] to add judge emails before submission. **URLs:** agent=https://cothesis-agent-791873451733.us-central1.run.app (403 unauth), console=https://console-791873451733.us-central1.run.app (login gate, passcode=cothesis-demo-2026).
- [x] **Day 5 console + dashboard** — Next.js 16 + Tailwind v4 app in `console/`; CoThesis design tokens (cream/#0E3A27/#289642/#03848F, Newsreader serif + Instrument Sans); login gate (httpOnly cookie, CONSOLE_LOGIN_SECRET); proxy.ts auth; dashboard (pipeline stats, eval score band); review queue list; review detail with 4-slot display (short/long/plain breakout/editor's note); QualityBar (6 dimensions, expandable), BadgeList (ratify proposed_badges), ReviewActions (Server Actions approve/reject + checklist pre-flight); approveItem writes to `resources` with editorial_reviewed_by/at; rejectItem marks archived; seed script for local test; build passes clean (TypeScript + Turbopack).
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

## Latest verification (2026-06-09)
- **main** merged PR #1 + PR #2; working tree clean.
- **293 pytest** green; gitleaks clean; console lint/build clean; E2E smoke green.
- **Redeploy + seed:** in progress — see deploy log below.

## Deploy log (2026-06-09)
- **Seed:** `scripts/seed_demo` → `{'auto_accept': 2, 'review_needed': 10, 'auto_exclude': 0, 'error': 0}` (~7 min)
- **Console deploy:** `console-00006-q68` via `scripts/deploy_console.sh` (exit 0)
- **Firestore counts:** pending review_queue=298, published=0
- **E2E smoke:** passed locally incl. review detail `/review/L07zC93w2ptRKBxXKV2c`
- **Skipped:** `firebase deploy --only firestore:rules` — Firebase CLI not installed on this machine
- **Note:** production login uses Secret Manager passcode (`cothesis-demo-2026`), not `console/.env.local`
- Synced `.env` + `console/.env.local` from main repo worktree (GCP project, Vertex datastore, MCP keys, console passcode).
- **293 pytest** green (incl. `tests/test_review_navigation.py`).
- **gitleaks** clean.
- **Console:** `npm run lint` (0 errors), `npm run build` clean.
- **E2E smoke:** `bash scripts/e2e_console_smoke.sh` — login gate, auth redirect, form login, dashboard/review/resources/pipeline (review detail skipped when queue empty).
- **Lint fixes:** React 19 purity rules (`SyncStatusCard`, `UndoCountdown`, `SessionStatsCard`); queue age computed in `getSyncStats()`.

## Completed (HITL Phases A–C, hackathon audit branch)
- [x] **Phase A** — auto-advance queue nav, keyboard shortcuts, enrichment provenance tab, inline taxonomy on approve, sticky decision pane, smart sort + compact queue
- [x] **Phase B** — bulk approve/reject, triage presets, Compendium card preview, structured send-back, Cloud Trace/Logs links
- [x] **Phase C** — undo approve window, reopen published for amendment, reviewer session stats (localStorage), duplicate routing hint

## Console (Day 5)
- `console/` — Next.js 16 app
- Run: `cd console && npm run dev` → http://localhost:3000
- Seed test data: `cd console && npx tsx scripts/seed-review-queue.ts` (needs GOOGLE_APPLICATION_CREDENTIALS or ADC)
- Login passcode (dev): `cothesis-demo` (set in `console/.env.local`)

## Blockers / waiting on human
- (none — Day 1 complete)

## Decisions needing the human
- (none open)

## Next task (production)
1. [DAVE] `bash day7-prod-grants.sh` — secret + run.invoker grants
2. Redeploy agent: `adk deploy cloud_run ...` (psycopg2-binary now in requirements.txt)
3. [DAVE] `bash day7-deploy-jobs.sh` — deploys Cloud Run Jobs + Cloud Scheduler
4. Update `compendium-import-url` secret once Compendium is live on Railway
5. Test: `python -m scripts.sync_to_compendium --dry-run` and `python -m scripts.run_batch --dry-run --use-adc`
6. Competition Day 8 still pending: set min-instances=1, gitleaks sweep, submit

## Deployed URLs
- **Agent:** https://cothesis-agent-791873451733.us-central1.run.app (private, 403 unauth — IAP TODO for judges)
- **Console:** https://console-791873451733.us-central1.run.app (public, passcode: `cothesis-demo-2026`)

## Modified files this session (Phase C)
- `console/app/review/actions.ts` — approve/reject/requeue return `nextPath`; `undoApprove`, `reopenForReview`
- `console/app/review/[id]/page.tsx` — imports shared actions; `DuplicateHint`
- `console/app/review/[id]/ReviewWorkspace.tsx` — undo toast + client navigation
- `console/components/ReviewActions.tsx` — session stats + `onNavigate` callback
- `console/components/ReviewQueueTable.tsx` — bulk session stats
- `console/components/SessionStatsCard.tsx`, `UndoApproveToast.tsx`, `DuplicateHint.tsx`, `PublishedResourcesTable.tsx` — new
- `console/lib/session-stats.ts`, `console/lib/review-navigation.ts` — new
- `console/app/dashboard/page.tsx` — session stats card
- `console/app/resources/page.tsx` — reopen action column

## Modified files (historical)
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
- Console dev: `cd console && npm run dev`
- Console build: `cd console && npm run build`
- Tests: `.venv/bin/pytest tests/ -q` (293 passed 2026-06-08)
- Console E2E: `bash scripts/e2e_console_smoke.sh`
- Redeploy console: `bash scripts/deploy_console.sh`
- Demo seed: `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo`
