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

## Cost (target: well under $100)
Model tiering (Gemini 3.x: Flash-Lite for discovery/classification/reconciliation/QC; Flash for appraisal/editorial; Pro only for the arbiter routing decision) is the biggest lever. Scale Cloud Run to zero; keep prompts < 200K tokens (Pro doubles above); Vertex AI Search free tier is 10k queries/month. Note: on the global endpoint, context caching and batch discounts are unavailable, so lean harder on tiering and trimming. The kill-switch covers the runaway-loop tail risk. The /cost-check skill summarises spend.

## Claude Code billing note
From 15 Jun 2026, headless `claude -p` / Agent SDK draws on a separate Agent SDK credit; interactive terminal/IDE use is unaffected. Build interactively; treat scheduled/headless eval runs as separately metered. Never set `ANTHROPIC_API_KEY` in the shell unless you intend API billing.
