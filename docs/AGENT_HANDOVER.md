# Agent Handover — CoThesis Curation Agent

**Audience:** A new coding agent taking over `/Users/dtownsend/dev/cothesis_agent`.  
**Read first:** `STATE.md` (live build state), then this file.  
**Source of truth:** `docs/` specs — especially `BUILD_PLAN.md`, `AGENTS_SPEC.md`, `SCHEMA.md`, `OPERATIONS.md`, `CLAUDE.md`.

**Git HEAD (2026-06-13):** `20881fa` — `fix(console): serialize compendium_synced_at for Published page`  
**Repo:** https://github.com/DaveTownDev/cothesis-curation-agent (private)  
**GCP project:** `cothesis-curation-agent`

---

## 1. Current production state

| Component | Revision / detail | Commit / notes |
|---|---|---|
| **Agent (Cloud Run)** | `cothesis-agent-00015-zpr` | `eff634c` — vocabulary prompt fixes (appraisal, refine_classification, orchestrator, guide builders) |
| **Console (Cloud Run)** | `console-00026-5zh` (target) | `20881fa` — Published page `compendium_synced_at` serialization; prior `console-00025-jnp` @ `113730c` (dashboard stats + HITL rejected label) |
| **Agent URL** | https://cothesis-agent-791873451733.us-central1.run.app | Private (`--no-allow-unauthenticated`); curl root → **403** |
| **Console URL** | https://console-791873451733.us-central1.run.app | Public + passcode (`cothesis-demo-2026` in Secret Manager) |

### Cloud Run Jobs

| Job | Purpose |
|---|---|
| `run-batch` | Pull enrichment queue → `run_pipeline()` per resource |
| `sync-to-compendium` | POST published `resources` to Compendium import API |
| `run-benchmark` | ADK eval + regression gate (`--check-regression`) |
| `prompt-lab-run` | Offline prompt-improvement cycle (proposals only) |

### Cloud Scheduler

- **`benchmark-weekly`** — Sunday 21:00 UTC → `run-benchmark --check-regression` (OIDC via `agent-runtime@`)

### Runtime SA

`agent-runtime@cothesis-curation-agent.iam.gserviceaccount.com` — `aiplatform.user`, `datastore.user`, `discoveryengine.viewer`, `secretmanager.secretAccessor`, `logging.logWriter`.

---

## 2. What was built (prompt improvement loop)

All workstreams **WS-V through WS-E** are complete on `main`.

### WS-V0/V1 — Vocabulary-native taxonomy

- Canonical `data/taxonomy/tag_vocabulary.json` + `agents/shared/tag_vocabulary.py` (sole code authority)
- Validators, prompts, and `compendium_bridge` switched to vocabulary-native `tags[]` push
- `docs/INGESTION_AGENT_HANDOVER.md` — bridge doc for Compendium import API

### WS-A — Eval infrastructure

- **20** seed cases in `eval/cases/*.json` + **30** total gold cases (5 HITL + 5 synthetic + 20 seed)
- `eval/taxonomy_gold.json` — **42** vocabulary-validated cases
- `scripts/run_benchmark.py` + `eval/baseline.json` — **20/20** pass; `response_match_score` **0.174**, `rubric_pass_rate` **0.99**
- CI: `.github/workflows/benchmark.yml`; Cloud Run Job `run-benchmark`

### WS-B — HITL console eval loop

- Review detail: Copy eval case, Add to gold set, Flag taxonomy error, Send to prompt lab
- `eval_failure_bucket` Firestore writes; `/prompt-lab` page with diff viewer + approve/reject (instructions only)

### WS-C — Pipeline / QC

- `prompt_versions.py` + `assessment_prompt_version` stamping
- QC `run_taxonomy_qc_check`; `scripts/source_accuracy_audit.py`, `scripts/refine_classification.py`

### WS-D — Prompt lab agents

- `agents/prompt_lab/` SequentialAgent team (analyst → editor → eval_arbiter)
- `scripts/prompt_eval_loop.py` Job runner; `Dockerfile.prompt-lab`
- **Never auto-writes** `agents/prompts/` — proposals go to `prompt_proposals` only

### WS-E — Firestore schemas

- `eval_failure_bucket`, `prompt_proposals`, `prompt_lab_runs` collections + indexes

### Verification baseline (last green full gate)

```bash
.venv/bin/pytest tests/ -q          # 459 passed (1 SequentialAgent deprecation warning)
.venv/bin/python -m scripts.run_benchmark --check-regression  # 20/20; see eval/baseline.json
cd console && npm run lint && npm run build
bash scripts/e2e_console_smoke.sh
```

---

## 3. Recent fixes (2026-06-12)

| SHA | Fix |
|---|---|
| `1d3e081` | Dashboard pipeline stats aligned with queue visibility; new `scripts/reconcile_pipeline_state.py` |
| `113730c` | HITL rejected label on pipeline stats card |
| `20881fa` | Published page crash — `compendium_synced_at` Firestore Timestamp serialization |
| `eff634c` | Prompt taxonomy alignment — appraisal, refine_classification, tag_vocabulary guides |

**`reconcile_pipeline_state.py`:** Backfilled **56** `pipeline_state` rows stuck at arbiter/editorial after bulk HITL rejects → `hitl_rejected`. Run with `--apply` after future bulk rejects.

---

## 4. Running / in-progress work

### Full 1512 reprocess — **NOT RUNNING / STALLED**

- User approved full reset; attempt started 2026-06-12 @ `eff634c` then **stalled at taxonomy refresh**
- Log: `data/live_resources/reprocess.log` — only 2 lines; no `[N/1512]` progress
- Prior partial run (2026-06-10): stopped at **76/1512**
- **No reprocess PID** running (verified 2026-06-13)
- Requires: `gcloud auth login` + `gcloud auth application-default login`, Doppler `DATABASE_PUBLIC_URL`

```bash
mkdir -p data/live_resources
doppler run --project dave-ai-stack --config prd -- \
  .venv/bin/python -m scripts.reset_and_reprocess_live --confirm-reset \
  --refresh-taxonomy --export data/live_resources/export.json \
  2>&1 | tee data/live_resources/reprocess.log
```

Monitor: `tail -f data/live_resources/reprocess.log` (grep `\[N/1512\]`; ~45s/resource ≈ 19h total).

### Sample batch 1 — **DONE**

- **98/100** processed, **2** failed (`list index out of range`)
- Outcomes: `auto_accept=52`, `review_needed=36`, `auto_exclude=10`
- Log: `data/live_resources/sample_100.log`; sample: `data/live_resources/sample_100_random.json`

### Sample batch 2 — **DONE**

- **100/100** processed, **0** failed
- Outcomes: `auto_accept=47`, `review_needed=51`, `auto_exclude=2`
- Log: `data/live_resources/sample_100_2.log`; sample: `data/live_resources/sample_100_random_2.json`

### QA audit — **COMPLETE**

- Full 3-layer pipeline on **210** `review_queue` docs
- Layer 1 `audit_records`: 204 records (dq ok=45/warn=118/fail=41; URL live=137/dead=64/unreachable=3)
- Layer 2 `source_accuracy_audit`: 205 records (pass=17/warn=74/fail=114)
- Layer 3 `write_qa_audit`: 210 docs updated
- Log: `data/live_resources/qa_audit.log`
- **Optional:** re-run layers 2–3 after sample batch 2 settles (new queue docs may exist)

---

## 5. Outstanding / incomplete / planned

| Item | Status |
|---|---|
| Full 1512 reprocess | Approved; stalled at taxonomy refresh — restart when authed |
| **WS-V2** HITL pickers | Full 78-specialty + 25-stage pickers; `book_chapter` removal — not done |
| Prompt lab live cycle | Code + console UI wired; GCP Job deploy + end-to-end cycle **not verified** |
| `SequentialAgent` → Workflow | ADK deprecation warning in prompt_lab — migration planned |
| Demo re-seed | Skipped during reprocess work |
| `eval_history` JSON artifacts | Untracked under `agents/pipeline/.adk/eval_history/` — **gitignored** |
| Duplicate `resource_code` in `review_queue` | From overlapping reprocess/sample runs — dedupe before full reprocess |
| Compendium sync | **Manual only** — Approve writes Firestore; curator clicks **Sync to Compendium** on Published page |
| Agent Cloud Run IAP | Deferred — judges use public console |
| `gcloud` user creds | May be expired — blocks `adk deploy` / `gcloud run deploy` (ADC alone insufficient) |

---

## 6. How to work (from `CLAUDE.md`)

1. **`docs/` are source of truth** — read `BUILD_PLAN.md` for ordered build, `AGENTS_SPEC.md` + `agents/prompts/` for behaviour.
2. **Never trust training data for ADK / Vertex / google-genai / Cloud Run** — use Context7 or official repos (`github.com/google/adk-python`, `google.github.io/adk-docs`). Pin `google-adk==2.1.x`.
3. **Region & models:** Gemini 3 on **global** endpoint (`GOOGLE_CLOUD_LOCATION=global`); infra in `us-central1`.
4. **`VertexAiSearchTool` is exclusive** — isolate in its own sub-agent or wrap via `AgentTool`.
5. **Secrets never enter the repo** — Secret Manager at deploy; placeholders in samples.
6. **No completion claims without fresh verification** — run commands and paste output.
7. **Test-first:** write eval/unit test, confirm fail, implement until green.
8. **Commit after verified tasks** — conventional messages; **pushes are human's job** unless explicitly requested.
9. **Human-gated (never without approval):** `gcloud billing`, IAM grants, `gcloud ... delete`, `--force`, `--allow-unauthenticated`.
10. **Emit platform methodology codes** (SYN-01, SYN-02, OBS-01, EVAL-01) — see `docs/TAXONOMY.md`.
11. **`quality_score` is 0–100**; six canonical dimensions; editorial badges from `docs/SCHEMA.md`.

On "continue": read `STATE.md` first (see `.claude/skills/resume/SKILL.md`).

---

## 7. Key commands

### Tests & eval

```bash
.venv/bin/pytest tests/ -q
.venv/bin/python -m scripts.run_benchmark                    # full gate
.venv/bin/python -m scripts.run_benchmark --check-regression
.venv/bin/python -m scripts.aggregate_gold_set
.venv/bin/python -m scripts.taxonomy_audit --score-gold
adk eval agents/pipeline eval/gold_set.json --config_file_path=eval/eval_config.json
```

### Deploy

```bash
# Agent (human-gated auth)
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/adk deploy cloud_run \
  --project=cothesis-curation-agent --region=us-central1 \
  --service_name=cothesis-agent --with_ui --trace_to_cloud --adk_version=2.1.0 agents/ -- \
  --no-allow-unauthenticated \
  --service-account=agent-runtime@cothesis-curation-agent.iam.gserviceaccount.com \
  --set-secrets=VERTEX_DATASTORE_ID=vertex-datastore-id:latest,MCP_SERVER_URL=mcp-server-url:latest,MCP_SERVER_KEY=mcp-server-key:latest

bash scripts/deploy_console.sh
bash scripts/deploy_batch_job.sh
bash scripts/deploy_benchmark_job.sh
bash scripts/deploy_prompt_lab_job.sh   # human-gated
```

### Ops / batch

```bash
# Reprocess (see §4)
doppler run --project dave-ai-stack --config prd -- \
  .venv/bin/python -m scripts.reset_and_reprocess_live --confirm-reset --refresh-taxonomy

# QA audit trio
.venv/bin/python -m scripts.audit_records
.venv/bin/python -m scripts.source_accuracy_audit
.venv/bin/python -m scripts.write_qa_audit

# Pipeline state reconcile after bulk rejects
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.reconcile_pipeline_state --apply

# Compendium sync
.venv/bin/python -m scripts.sync_to_compendium --dry-run

# Demo seed
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo
```

### Console dev

```bash
cd console && npm run dev          # http://localhost:3000
cd console && npm run lint && npm run build
bash scripts/e2e_console_smoke.sh
```

### Monitor logs

```bash
tail -f data/live_resources/reprocess.log
tail -f data/live_resources/sample_100_2.log
gcloud logging read 'resource.type=cloud_run_revision' --limit=50 --project=cothesis-curation-agent
```

---

## 8. Architecture snapshot

- **Interactive path:** `agents/pipeline/agent.py` — `LlmAgent` orchestrator via `AgentTool` (`adk web`)
- **Batch path:** `agents/pipeline/deterministic.py` — `run_pipeline()` code-sequenced; LLM for judgments only; pure-Python arbiter
- **Eight specialist agents:** discovery → appraisal → classification → editorial → reconciliation → QC panel → arbiter (+ isolated grounding)
- **Firestore collections:** `drafts`, `draft_records`, `review_queue`, `pipeline_state`, `resources`, `qa_audit`, `eval_failure_bucket`, `prompt_proposals`, `prompt_lab_runs`
- **Console:** Next.js 16 HITL — Dashboard, Review queue, Published, Pipeline, Prompt lab, Catalog editor

Full diagram-ready reference: `docs/ARCHITECTURE_BRIEF.md`, `docs/ARCHITECTURE.md`.

---

## 9. Key files modified recently

### Prompt loop / vocabulary (WS-V through WS-E)

- `agents/shared/tag_vocabulary.py`, `data/taxonomy/tag_vocabulary.json`
- `agents/taxonomy.py`, `agents/shared/compendium_bridge.py`, `agents/pipeline/deterministic.py`
- `agents/prompts/*.md` (version comments + taxonomy alignment)
- `agents/prompt_lab/` (new)
- `eval/cases/*.json`, `eval/gold_set.json`, `eval/taxonomy_gold.json`, `eval/baseline.json`
- `scripts/run_benchmark.py`, `scripts/aggregate_gold_set.py`, `scripts/prompt_eval_loop.py`
- `scripts/source_accuracy_audit.py`, `scripts/refine_classification.py`, `scripts/reconcile_pipeline_state.py` (new)
- `agents/shared/prompt_versions.py`, `agents/shared/firestore_schemas.py`
- `firestore.indexes.json`

### Console (WS-B + fixes)

- `console/lib/eval-export.ts`, `console/lib/failure-bucket.ts`, `console/lib/firestore.ts`
- `console/lib/qa-issues.ts`, `console/app/review/actions.ts`
- `console/components/ReviewActions.tsx`, `console/app/prompt-lab/`
- `console/app/dashboard/page.tsx`, `console/components/PipelineStatsCard.tsx`
- `console/app/resources/page.tsx` (`compendium_synced_at` fix)
- `console/data/eval-summary.json`

### Docs

- `docs/JUDGE_GUIDE.md`, `docs/OPERATIONS.md`, `docs/PROMPT_IMPROVEMENT_LOOP.md`
- `docs/INGESTION_AGENT_HANDOVER.md`, `docs/ARCHITECTURE_BRIEF.md`

### Tests

- `tests/test_tag_vocabulary.py`, `tests/test_eval_export.py`, `tests/test_prompt_lab_*.py`
- `tests/test_run_benchmark.py`, `tests/test_refine_classification.py`, `tests/test_firestore_schemas.py`

---

## 10. Blockers / human gates

1. **`gcloud auth login` + `gcloud auth application-default login`** — required for deploy and some ops
2. **Doppler `DATABASE_PUBLIC_URL`** — required for live export / full reprocess
3. **Compendium `compendium-import-url` secret** — update when Railway deploy changes
4. **Prompt changes** — human PR only; never auto-merge from prompt lab
5. **Billing / IAM / delete / `--allow-unauthenticated`** — explicit human approval

---

## 11. Suggested next tasks (priority order)

1. Verify `gcloud auth` → redeploy console @ `20881fa` if not already on `console-00026-5zh`
2. Dedupe duplicate `resource_code` rows in `review_queue` before full reprocess
3. Restart full 1512 reprocess (tmux/background; monitor `reprocess.log`)
4. Optional: re-run QA audit layers 2–3 on post-batch-2 queue
5. WS-V2: expand TaxonomyEditor to 78 specialties + 25 thesis stages
6. Verify prompt lab end-to-end: deploy Job → flag case in console → proposal → human PR
7. Migrate `agents/prompt_lab/` from `SequentialAgent` to ADK Workflow
8. Record demo video (`docs/DEMO_SCRIPT.md`); update `docs/SUBMISSION.md`

---

## 12. Judge / demo quick reference

- **Console:** https://console-791873451733.us-central1.run.app — passcode `cothesis-demo-2026`
- **Walkthrough:** `docs/JUDGE_GUIDE.md`, `docs/DEMO_SCRIPT.md`
- **Re-seed:** `GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.seed_demo`
- **Do not** run live pipeline on camera (~45s/resource)
