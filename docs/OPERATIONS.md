# OPERATIONS — GCP setup, deploy, secrets, cost

Full rationale in the setup playbook; this is the runbook. gcloud runs from Claude's shell under the human's ADC. **[DAVE]** marks human-only steps.

## Day 0 guardrails (do FIRST)
- **[DAVE]** Confirm paid billing (already set up). Create the budget + hard kill-switch — budgets only alert, they do not cap:
  - `gcloud billing budgets create --billing-account=BILLING_ID --display-name="Agents Challenge $500" --budget-amount=500USD --threshold-rule=percent=0.5 --threshold-rule=percent=0.75 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0 --filter-projects="projects/$GOOGLE_CLOUD_PROJECT"`
  - Wire the budget to a Pub/Sub topic + a Cloud Function that disables billing (Google's `disable-billing-with-notifications` pattern). This is the only real hard stop.
- **[DAVE]** `gcloud auth login` + `gcloud auth application-default login`.

## Enable services (Claude, once authed)
`gcloud services enable aiplatform.googleapis.com run.googleapis.com discoveryengine.googleapis.com firestore.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com iap.googleapis.com --project=$GOOGLE_CLOUD_PROJECT`

## Region & models
Infra in `us-central1`. Gemini 3.x is **global-endpoint only** -> `GOOGLE_CLOUD_LOCATION=global`. (Trade-off: global endpoint has no context caching / batch discount — relevant to cost below.) Vertex AI Search datastore lives in the global collection.

## IAM (least privilege) — **[DAVE]** approves grants
Runtime SA `agent-runtime@$PROJECT.iam.gserviceaccount.com` with only: `roles/aiplatform.user`, `roles/discoveryengine.viewer`, `roles/datastore.user`, `roles/secretmanager.secretAccessor` (on specific secrets), `roles/logging.logWriter`. Never the default compute SA. Claude's automation runs as the human's user, not this SA.

## Deploy (Cloud Run, not Agent Engine)
- Agent service: `adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=us-central1 --with_ui --trace_to_cloud agents/` — answer **N** to allow-unauthenticated; protect with **Cloud Run IAP** (`--iap`), add judges as IAP-secured Web App User. **[DAVE]** enables IAP + adds judge emails.
- Console: `bash scripts/deploy_console.sh` (or `gcloud run deploy console --source console/ …`) — public + passcode login. **Judge URL:** https://console-791873451733.us-central1.run.app (passcode in Secret Manager `console-login`; demo value `cothesis-demo-2026`). Walkthrough: `docs/JUDGE_GUIDE.md`.

## Secrets
`echo -n "VALUE" | gcloud secrets create NAME --data-file=- --replication-policy=automatic`, inject with `--set-secrets=ENV=NAME:latest`. Runtime SA needs `secretAccessor` before deploy. Next.js: keep secrets server-side (NEXT_PUBLIC_* bakes at build).

## Full pipeline reset + live reprocess

Wipe all in-flight pipeline Firestore state and re-run every live Compendium resource through `run_pipeline` with the current taxonomy (`data/taxonomy/live_*.json`).

```bash
# Preview (no writes):
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.reset_and_reprocess_live --dry-run

# Reset + export + reprocess (~45s/resource; run in tmux/background):
doppler run --project dave-ai-stack --config prd -- \
  .venv/bin/python -m scripts.reset_and_reprocess_live --confirm-reset \
  --refresh-taxonomy --export data/live_resources/export.json \
  2>&1 | tee data/live_resources/reprocess.log
```

Clears: `drafts`, `draft_records`, `review_queue`, `pipeline_state`, `resources`. Does **not** delete live Compendium rows. Requires `DATABASE_PUBLIC_URL` (Postgres export) and ADC for Firestore + Vertex.

`--reset-only` clears collections without running the pipeline. `--use-cached-export` skips Postgres fetch if `export.json` exists.

**Postgres enrichment queue** (Railway `compendium.enrichment_queue`, used by the Compendium enrichment worker):

```bash
doppler run --project dave-ai-stack --config prd -- \
  .venv/bin/python -m scripts.sync_live_to_enrichment_queue --dry-run

doppler run --project dave-ai-stack --config prd -- \
  .venv/bin/python -m scripts.sync_live_to_enrichment_queue --confirm \
  --export data/live_resources/export.json
```

Merges live catalog from Postgres `import_candidates` + Neo4j (public library graph), inserts missing queue rows, resets `complete`/`failed`/`processing` → `pending`, and sets `import_candidates.status = enrichment_queued`.

## Prompt improvement loop

Full architecture, HITL integration points, and phase roadmap: **[docs/PROMPT_IMPROVEMENT_LOOP.md](PROMPT_IMPROVEMENT_LOOP.md)**. Build task tracker: `docs/PROMPT_IMPROVEMENT_BUILD_PLAN.md`. Firestore shapes: `docs/SCHEMA.md` (`eval_failure_bucket`, `prompt_proposals`, `prompt_lab_runs`).

### Human merge workflow (prompt changes)

Prompt lab and console **never** auto-write `agents/prompts/`. Every production prompt change follows this gate:

1. **Propose offline** — `prompt-lab-run` Job (or local `adk web` prompt lab) writes a `prompt_proposals` doc with `unified_diff` + `eval_delta`. HITL flags land in `eval_failure_bucket` first.
2. **Review in console** — `/prompt-lab` lists `pending` proposals; approve = merge instructions only; reject = `status=rejected` (no file write).
3. **Human PR** — Curator applies the diff in git, bumps the prompt registry (`agents/shared/prompt_versions.py`), and adds a version comment at the top of the edited `agents/prompts/*.md` file.
4. **Regression gate** — `.venv/bin/pytest tests/ -q` then `python -m scripts.run_benchmark --check-regression` (see Benchmark runner below). Do **not** weaken `eval/eval_config.json` thresholds.
5. **Version stamp** — Ensure `assessment_prompt_version` / per-agent registry strings match the merged prompt files before deploy.
6. **Deploy** — Follow deploy sequence below; capture a fresh `eval/baseline.json` only after a green full benchmark on `main`.

**Gold cases from HITL** — "Add to gold set" writes `eval/cases/{resource_code}.json`; run `python -m scripts.aggregate_gold_set` before benchmark. Gold and prompt changes land via **PR only**.

### Source-accuracy QA layer

Deterministic comparison of `review_queue.draft_record` against live URLs/DOIs. Run after batch processing or before QA triage (weekly or ad hoc — not on every `run-batch`):

```bash
# Data-quality + URL liveness (layer 1):
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.audit_records

# Source-accuracy heuristics (layer 2) -> /tmp/cothesis_source_accuracy.json:
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.source_accuracy_audit

# Merge both into review_queue.qa_audit for console QA column:
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.write_qa_audit
```

Filter the review queue by `qa_audit.source_verdict == "fail"` for worst-first triage. **Classification replay** (one resource, no full pipeline): `python -m scripts.refine_classification {resource_code} [--dry-run]`.

### Benchmark runner

`scripts/run_benchmark.py` (WS-A) runs, in order:

1. `pytest -q`
2. `adk eval` against `eval/gold_set.json` + `eval/eval_config.json`
3. Writes `console/data/eval-summary.json` for the dashboard band

Flags:

- `--check-regression` — compare scores to `eval/baseline.json`; exit 1 on regression (CI + weekly Scheduler).
- `--subset N` — cap cases for prompt-lab replays (cost guard).

Local run (after WS-A lands):

```bash
GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.run_benchmark --check-regression
```

**CI** — `.github/workflows/benchmark.yml` (WS-A) triggers on `eval/**`, `agents/prompts/**`, `scripts/run_benchmark.py`. **Weekly Scheduler** — separate from daily `run-batch` @ 20:00 UTC; human deploy via `bash scripts/deploy_benchmark_job.sh` (see below).

### Prompt-improvement deploy sequence

**[DAVE]** — human-gated; run only after WS merges are green on `main`. Do not run `gcloud` deploy scripts from automation without approval.

1. **Firestore indexes** — `firebase deploy --only firestore:indexes` (requires Firebase CLI; includes `eval_failure_bucket` + `prompt_proposals` indexes in `firestore.indexes.json`).
2. **Agent** — `adk deploy cloud_run` from `agents/` (prompt version constants ship with image); record revision in `STATE.md`.
3. **Batch image** — `bash scripts/deploy_batch_job.sh` (deterministic orchestrator unchanged).
4. **Benchmark Job** — `bash scripts/deploy_benchmark_job.sh` + weekly Cloud Scheduler → `run-benchmark` Job.
5. **Prompt lab Job** — `bash scripts/deploy_prompt_lab_job.sh` (WS-D; separate image).
6. **Console** — `bash scripts/deploy_console.sh` (gold export + `/prompt-lab` when WS-B ships).
7. **Post-deploy** — bump `prompt_versions` registry if prompts changed; `python -m scripts.run_benchmark --check-regression`; refresh `eval/baseline.json` on intentional prompt bump.

**Cost guards (prompt lab):** `PROMPT_LAB_MAX_CASES=10` default; Flash-Lite for classification replays; Pro only for editorial rubric judge. Monthly: review `eval_failure_bucket` volume and tune max cases. Kill-switch per Day 0 guardrails above.

## Cost (target: well under $100)
Model tiering (Gemini 3.x: Flash-Lite for discovery/classification/reconciliation/QC; Flash for appraisal/editorial; Pro only for the arbiter routing decision) is the biggest lever. Scale Cloud Run to zero; keep prompts < 200K tokens (Pro doubles above); Vertex AI Search free tier is 10k queries/month. Note: on the global endpoint, context caching and batch discounts are unavailable, so lean harder on tiering and trimming. The kill-switch covers the runaway-loop tail risk. The /cost-check skill summarises spend.

## Claude Code billing note
From 15 Jun 2026, headless `claude -p` / Agent SDK draws on a separate Agent SDK credit; interactive terminal/IDE use is unaffected. Build interactively; treat scheduled/headless eval runs as separately metered. Never set `ANTHROPIC_API_KEY` in the shell unless you intend API billing.
