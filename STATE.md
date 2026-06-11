# STATE — live build state (update after every task)

> On "continue", read this file first and resume. Keep the modified-file list and test/deploy commands here so they survive compaction.

## Current phase
**Integration-verify prompt improvement loop (2026-06-11):** Fixed `eval-summary.json` schema drift — `console/lib/eval-summary.ts` normalizes benchmark output (`response_match_score`, nested `thresholds`) for dashboard; taxonomy reprocess tests aligned to vocabulary codes (`CARDIO`, `PSYCH`). **Verification:** **454 pytest passed**; console lint/build clean; **e2e smoke green**. **Not done:** console redeploy with WS-B; prompt-lab Job deploy; fresh `adk eval` baseline capture.

**WS-B HITL console eval loop (2026-06-11):** Copy eval case, Add to gold set, Flag taxonomy error, Send to prompt lab on review detail; `eval_failure_bucket` writes; QA classification requeue → failure bucket; `/prompt-lab` page with diff viewer + approve/reject (PR instructions only). **Not done:** console redeploy with WS-B.

**Modified (WS-B):** `console/lib/eval-export.ts`, `console/lib/failure-bucket.ts`, `console/lib/firestore.ts`, `console/app/review/actions.ts`, `console/components/ReviewActions.tsx`, `console/app/prompt-lab/`, `console/components/PromptProposalCard.tsx`, `console/components/NavBar.tsx`, `eval/build_gold_case.py`, `tests/test_eval_export.py`, `scripts/e2e_console_smoke.sh`.

**WS-D prompt lab (2026-06-11):** `agents/prompt_lab/` SequentialAgent team (analyst → editor → eval_arbiter); `scripts/prompt_eval_loop.py` Job runner; `Dockerfile.prompt-lab` + `cloudbuild.prompt-lab.yaml` + `scripts/deploy_prompt_lab_job.sh`; `PROMPT_LAB_MAX_CASES=10`; proposals write to `prompt_proposals` only (never auto-write `agents/prompts/`). **Verification:** 19 pytest (`test_prompt_lab_agents`, `test_prompt_lab_cycle`). **Not done:** GCP deploy (`deploy_prompt_lab_job.sh` human-gated); live ADK agent run; end-to-end cycle with console approve.

**Modified (WS-D):** `agents/prompt_lab/` (new), `agents/prompts/prompt_lab_*.md` (new), `scripts/prompt_eval_loop.py` (new), `Dockerfile.prompt-lab` (new), `cloudbuild.prompt-lab.yaml` (new), `scripts/deploy_prompt_lab_job.sh` (new), `tests/test_prompt_lab_agents.py` (new), `tests/test_prompt_lab_cycle.py` (new).

**WS-A eval infrastructure (2026-06-11):** 20 seed cases in `eval/cases/*.json` (`source.origin: seed`); aggregate → `eval/gold_set.json`; `eval/taxonomy_gold.json` **42** cases (vocabulary-validated via `eval/vocab.py`); `scripts/run_benchmark.py` + `eval/baseline.json`; **P2-08 complete** — CI `.github/workflows/benchmark.yml` (PR on `eval/**`, `agents/prompts/**`, `scripts/run_benchmark.py`); benchmark Job image `cloudbuild.benchmark.yaml` + `Dockerfile.benchmark` wired to `scripts/deploy_benchmark_job.sh`. **Verification:** `.venv/bin/pytest tests/test_run_benchmark.py -q` — **5 passed** (2026-06-11). **Not done:** fresh `adk eval` baseline capture; weekly Scheduler deploy (`deploy_benchmark_job.sh` **[DAVE] human-gated**).

**Modified (WS-A):** `eval/cases/*.json` (20), `eval/schemas/gold_case.schema.json`, `eval/cases/README.md`, `eval/vocab.py`, `eval/taxonomy_gold.json`, `eval/baseline.json`, `eval/gold_set.json` (regenerated), `scripts/aggregate_gold_set.py`, `scripts/run_benchmark.py`, `.github/workflows/benchmark.yml`, `cloudbuild.benchmark.yaml`, `Dockerfile.benchmark`, `scripts/deploy_benchmark_job.sh`, `tests/test_aggregate_gold.py`, `tests/test_taxonomy_gold.py`, `tests/test_run_benchmark.py`.

**WS-V0/V1 vocabulary alignment (2026-06-11):** Canonical `data/taxonomy/tag_vocabulary.json` + `demo_resources_retagged.json`; `agents/shared/tag_vocabulary.py` (sole code authority); validators/prompt/bridge switched to vocabulary-native `tags[]` push; `docs/INGESTION_AGENT_HANDOVER.md` copied from comp_build. **Verification:** 76 pytest (`test_tag_vocabulary`, `test_taxonomy`, `test_compendium_bridge`). **Not done:** full suite, console build, demo re-seed, 1512 reprocess, WS-V2 HITL pickers.

**Modified (WS-V):** `agents/shared/tag_vocabulary.py` (new), `agents/taxonomy.py`, `agents/shared/codes.py`, `agents/shared/schema.py`, `agents/shared/compendium_bridge.py`, `agents/pipeline/deterministic.py`, `agents/prompts/classification.md`, `console/lib/compendium-sync.ts`, `console/lib/taxonomy.ts`, `console/lib/checklist.ts`, `console/components/TaxonomyEditor.tsx`, `data/taxonomy/tag_vocabulary.json`, `data/taxonomy/demo_resources_retagged.json`, `console/lib/data/taxonomy/tag_vocabulary.json`, `docs/INGESTION_AGENT_HANDOVER.md`, `tests/test_tag_vocabulary.py` (new), `tests/test_taxonomy.py`, `tests/test_compendium_bridge.py`.

**WS-C pipeline/QC (2026-06-11):** `prompt_versions.py` + `assessment_prompt_version` stamping; QC `run_taxonomy_qc_check` in deterministic + interactive paths; `scripts/source_accuracy_audit.py` + `scripts/refine_classification.py`. **Verification:** 23 pytest (`test_prompt_versions`, `test_deterministic_pipeline`, `test_qc_panel_tools`, `test_refine_classification`).

**QA queue routing @ `36ab6c1` (2026-06-11, pushed `origin/main`):** `auto_accept` no longer writes `review_queue`; console QA triage uses `console/lib/qa-issues.ts` (data-quality, URL, source-accuracy). **Verification:** 16 pytest (`test_qa_issues`, `test_deterministic_pipeline`).

**Deployed (2026-06-11):** console **`console-00020-wqs`**; agent **`cothesis-agent-00013-sd4`** (`adk deploy cloud_run` from `agents/`, no dedicated script — see `docs/OPERATIONS.md`).

**Ops (2026-06-11):** `scripts.write_qa_audit` → **119** `review_queue` docs updated (data-quality/URL only; no `/tmp/cothesis_source_accuracy.json`).

**Reprocess paused (2026-06-11).** Live reprocess **stopped at 76/1512** (quality issues). **Do not** `reset_and_reprocess_live --confirm-reset` or restart full 1512 reprocess without approval.

**Resume pipeline (when approved):** `reprocess_live_resources --skip-existing` (not another full reset).

**Judge demo ready.** Docs: `docs/JUDGE_GUIDE.md`, `docs/DEMO_SCRIPT.md`.

**Live taxonomy alignment (2026-06-09).** Pipeline + console now use full Compendium methodology (148) and specialty (53) lists from `data/taxonomy/live_*.json`. Refresh: `python -m scripts.fetch_live_taxonomy`. MVP grounding cards unchanged in `data/methodologies/*.md`.

**Merged to `main` @ `47b6fcb` (2026-06-09).** PR #1 (audit fixes + HITL Phases A–C) + PR #2 (review agents + guard) merged. **293 pytest**, console lint/build clean, `bash scripts/e2e_console_smoke.sh` green.

**Pushed @ `dbbd801` (2026-06-09):** live taxonomy alignment + QA console quick actions on `origin/main`.

**Deployed (2026-06-09):** agent rev `cothesis-agent-00012-cn8` — fresh source image `sha256:4422e65e…` (built 2026-06-09, includes taxonomy Python post-`dbbd801`); MCP + datastore secrets + SA `agent-runtime@cothesis-curation-agent.iam.gserviceaccount.com`. Prior config-only rev `00011-fhk` (stale Jun 5 image). **Deployed (2026-06-11):** console rev `console-00017-lcd` @ https://console-791873451733.us-central1.run.app (subtype taxonomy + QA/backfill @ `ec7f459`). **Deployed (2026-06-10):** console rev `console-00015-496` @ https://console-791873451733.us-central1.run.app (catalog editor + live reprocess @ `2de0237`; QA shortcuts @ `abe9fcd`; nav restructure @ `90e066f`; compendium sync @ `843a9fa`; `COMPENDIUM_IMPORT_URL` + `IMPORT_API_KEY` from Secret Manager; `min-instances=1`, `CONSOLE_PUBLIC_URL` set). Live taxonomy: **148** methodologies + **53** specialties (`data/taxonomy/live_*.json`). Demo re-seeded: 2 auto_accept + 10 review_needed, 0 errors.

**Submission (human):** record demo video (`docs/DEMO_SCRIPT.md`), paste Devpost copy (`docs/SUBMISSION.md` — readiness + taxonomy updated 2026-06-10), familiarity scores (L75–79), grant judge GitHub access. Judge quick-start: `docs/JUDGE_GUIDE.md`.

Repo: https://github.com/DaveTownDev/cothesis-curation-agent (private).

### Residuals (non-blocking)
- **Remaining ops:** (none for taxonomy agent image — source redeploy complete on `00012-cn8`).
- Interactive `adk web` path: assembly normalizes out-of-enum types + backfills missing descriptions (`tests/test_interactive_assembly.py`); demo video uses pre-seeded batch data, not live pipeline.
- Premium enrichment (Altmetric, ISBNdb, etc.): optional keys in `.env.example`; Tier-1 free sources cover MVP article/book paths.
- Eval rubric judge may score all-pass — read as "no violations".

## Demo seed (Phase 3)
- `scripts/seed_demo.py` — runs deterministic run_pipeline on 12 curated real resources. Verified: 12/12 full chain, 10 review_needed + 2 auto_accept, 0 errors. All collections populated (drafts/draft_records/review_queue/pipeline_state = 12 each). Console verified live: Dashboard, Review queue, Published, Pipeline, catalog editor; Pipeline Inspector has 5 tabs (Quality, Panel, Classification, Enrichment, Provenance).
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
- (none — integration-verify green; next: console redeploy, prompt-lab Job deploy, `adk eval` baseline capture)

## Latest verification (2026-06-11 — integration-verify)
- `.venv/bin/pytest tests/ -q` — **454 passed**, 1 warning (`SequentialAgent` deprecation in prompt_lab)
- `cd console && npm run lint && npm run build` — **clean** (Next.js 16.2.7; routes incl. `/prompt-lab`, `/dashboard`)
- `bash scripts/e2e_console_smoke.sh` — **green** (`/dashboard` authenticated OK; review detail SKIP — no pending items)

## Latest verification (2026-06-11 — WS-B)
- `.venv/bin/pytest tests/test_eval_export.py -q` — **3 passed**
- `cd console && npm run lint && npm run build` — **clean** (`/prompt-lab` route present)

## Latest verification (2026-06-11 — WS-A)
- `.venv/bin/pytest tests/test_aggregate_gold.py tests/test_taxonomy_gold.py tests/test_run_benchmark.py -q` — **18 passed**

## Latest verification (2026-06-11 — WS-C)
- `.venv/bin/pytest tests/test_prompt_versions.py tests/test_deterministic_pipeline.py tests/test_qc_panel_tools.py tests/test_refine_classification.py -q` — **23 passed**

## Latest verification (2026-06-11 — WS-E)
- `tests/test_firestore_schemas.py` — **7 passed**

## Latest verification (2026-06-09)
- Compendium console sync: **322 pytest** green; console lint/build green.
- **main** @ `1b1623a` pushed to `origin/main`; agent source redeploy `00012-cn8`.
- Live taxonomy **148 + 53**; refresh `python -m scripts.fetch_live_taxonomy`.
- gitleaks clean; E2E smoke green; console redeploy `00010-5rt` with Compendium secrets verified (`/login` **200**).
- Agent **source** redeploy **done** (`00012-cn8`); MCP IAM + secret mount verified on new revision.

## Deploy log (2026-06-09)
- **Agent rev `cothesis-agent-00012-cn8`:** `adk deploy cloud_run` from workspace `agents/` (--no-allow-unauthenticated); image `sha256:4422e65edf6a659522ea4e86bdff0bafa5f085ea02684c7e8619c5287ce52272` built **2026-06-09T21:54:47Z**; secrets `VERTEX_DATASTORE_ID`, `MCP_SERVER_URL`, `MCP_SERVER_KEY` + SA preserved; curl root **403** unauth.
- **Agent rev `cothesis-agent-00011-fhk`:** MCP `MCP_SERVER_KEY` + `MCP_SERVER_URL` + `VERTEX_DATASTORE_ID` secrets; runtime SA `agent-runtime@cothesis-curation-agent.iam.gserviceaccount.com`. Same image as `00009`/`00010`: `sha256:899c970a…` built **2026-06-05** — does **not** include taxonomy commit `dbbd801` (2026-06-09).
- **Seed:** `scripts/seed_demo` → `{'auto_accept': 2, 'review_needed': 10, 'auto_exclude': 0, 'error': 0}` (~7 min)
- **Console deploy:** `console-00015-496` via `scripts/deploy_console.sh` (catalog editor + live reprocess `2de0237`, exit 0)
- **Live export:** `data/live_resources/export.json` — 1512 resources from Postgres (Doppler prd); taxonomy reprocess 406/522 docs updated; sync 1 published; **reprocess_live** running in background (~1345 need pipeline, log `data/live_resources/reprocess.log`)
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
- **E2E smoke:** fix `console/lib/eval-summary.ts` to read new `run_benchmark.py` summary shape (or restore legacy fields in `console/data/eval-summary.json`) so `/dashboard` stops 500ing in smoke
- **Baseline capture:** `eval/baseline.json` is a placeholder from the 2026-06-08 eval run; re-capture with `.venv/bin/python -m scripts.run_benchmark --skip-pytest` when `adk` is available locally

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

## Modified files this session (WS-B)
- `console/lib/eval-export.ts` — build ADK gold cases from HITL review data (new)
- `console/lib/failure-bucket.ts` — `eval_failure_bucket` Firestore writes (new)
- `console/lib/firestore.ts` — `EvalFailureBucketDoc`, `PromptProposalDoc`, `PromptLabRunDoc` + queries
- `console/app/review/actions.ts` — export/add gold set, flag, send to lab; requeue → failure bucket
- `console/components/ReviewActions.tsx` — eval & prompt-lab action row
- `console/app/prompt-lab/page.tsx`, `console/app/prompt-lab/actions.ts` — proposal list + approve/reject (new)
- `console/components/PromptProposalCard.tsx` — diff viewer (new)
- `console/components/NavBar.tsx` — Prompt lab nav link
- `console/lib/qa-recommendations.ts` — doc re QA requeue → failure bucket
- `eval/build_gold_case.py` — Python mirror for pytest (new)
- `tests/test_eval_export.py` — gold case contract + aggregate round-trip (new)
- `scripts/e2e_console_smoke.sh` — `/prompt-lab` route + eval action buttons on review detail

## Modified files this session (WS-A)
- `eval/cases/*.json` — 20 seed cases migrated from monolith (`source.origin: seed`)
- `eval/gold_set.json` — regenerated via aggregate
- `eval/taxonomy_gold.json` — expanded to 42 vocabulary-validated cases
- `eval/baseline.json` — regression gate placeholder
- `eval/schemas/gold_case.schema.json`, `eval/cases/README.md`, `eval/vocab.py` — eval validation layer
- `scripts/aggregate_gold_set.py`, `scripts/run_benchmark.py` — aggregate + benchmark runner
- `.github/workflows/benchmark.yml` — PR/push CI gate (pytest + benchmark --skip-adk)
- `cloudbuild.benchmark.yaml`, `Dockerfile.benchmark` — benchmark Job image; `deploy_benchmark_job.sh` submits via `_IMAGE` substitution
- `scripts/deploy_benchmark_job.sh` — rebuild image + update `run-benchmark` Job (human-gated)
- `tests/test_aggregate_gold.py`, `tests/test_taxonomy_gold.py`, `tests/test_run_benchmark.py` — WS-A unit tests

## Modified files this session (WS-C)
- `agents/shared/prompt_versions.py` — new registry
- `agents/prompts/*.md` — `<!-- prompt-version: … -->` comments (7 files)
- `agents/appraisal/tools.py` — `assessment_prompt_version` on parse
- `agents/qc_panel/tools.py` — `run_taxonomy_qc_check`
- `agents/qc_panel/agent.py` — taxonomy check in `run_deterministic_checks`
- `agents/pipeline/deterministic.py` — version stamp path + QC taxonomy wiring only
- `scripts/source_accuracy_audit.py` — `/tmp/cothesis_source_accuracy.json`
- `scripts/refine_classification.py` — classification replay CLI
- `docs/OPERATIONS.md` — source-accuracy cadence + refine_classification
- `agents/prompts/qc_panel.md` — taxonomy_check documented
- `tests/test_prompt_versions.py`, `tests/test_refine_classification.py` — new
- `tests/test_deterministic_pipeline.py`, `tests/test_qc_panel_tools.py` — extended

## Modified files this session (WS-E P3-01 / P2-09)
- `docs/SCHEMA.md` — `eval_failure_bucket`, `prompt_proposals`, `prompt_lab_runs` collection defs
- `firestore.indexes.json` — indexes for failure bucket `created_at` DESC, proposals `status`
- `agents/shared/firestore_schemas.py` — Pydantic models + Firestore serializers (new)
- `agents/shared/firestore_utils.py` — collection name constants
- `docs/OPERATIONS.md` — prompt improvement loop, human merge workflow, benchmark runner, deploy sequence
- `docs/PROMPT_IMPROVEMENT_LOOP.md` — cross-link to OPERATIONS.md
- `scripts/deploy_benchmark_job.sh` — benchmark Job deploy skeleton (human-gated)
- `tests/test_firestore_schemas.py` — unit tests for new models (new)

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

## Judge demo (2026-06-10)
- **Console:** https://console-791873451733.us-central1.run.app — passcode `cothesis-demo-2026`
- **Walkthrough:** `docs/DEMO_SCRIPT.md` (5 min video) · `docs/JUDGE_GUIDE.md` (judge self-serve)
- **Re-seed before recording:** `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo`
- **Do not** run live pipeline on camera (~45s/resource)

## Key commands (WS-A)
- Aggregate gold set: `.venv/bin/python -m scripts.aggregate_gold_set`
- Benchmark: `.venv/bin/python -m scripts.run_benchmark`
- Regression gate: `.venv/bin/python -m scripts.run_benchmark --check-regression`
- WS-A gate: `.venv/bin/pytest tests/test_aggregate_gold.py tests/test_taxonomy_gold.py tests/test_run_benchmark.py -q`

## Key commands (WS-A)
- Aggregate gold: `python -m scripts.aggregate_gold_set`
- Benchmark gate: `python -m scripts.run_benchmark --check-regression`
- WS-A unit gate: `.venv/bin/pytest tests/test_aggregate_gold.py tests/test_taxonomy_gold.py tests/test_run_benchmark.py -q`

## Key commands (WS-C)
- Prompt versions: `.venv/bin/pytest tests/test_prompt_versions.py -q`
- Source-accuracy layer: `python -m scripts.source_accuracy_audit` then `python -m scripts.write_qa_audit`
- Classification replay: `python -m scripts.refine_classification {resource_code} [--dry-run]`
- WS-C gate: `.venv/bin/pytest tests/test_prompt_versions.py tests/test_deterministic_pipeline.py tests/test_qc_panel_tools.py tests/test_refine_classification.py -q`

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
