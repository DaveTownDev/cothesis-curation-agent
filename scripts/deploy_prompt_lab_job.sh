#!/usr/bin/env bash
# Rebuild the prompt-lab image and point the Cloud Run Job `prompt-lab-run` at it.
#
# **[DAVE] human-gated** — do not run from CI or agent automation without approval.
# Prerequisites (WS-D): scripts/prompt_eval_loop.py, Dockerfile.prompt-lab,
#   cloudbuild.prompt-lab.yaml, agents/prompt_lab/.
#
# Env: PROMPT_LAB_MAX_CASES=10 (cost cap; set on job update).
# Not gated on IAM/allow-unauth changes (image + job update only).
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-cothesis-curation-agent}"
REGION="${REGION:-us-central1}"
JOB="prompt-lab-run"
IMG="us-central1-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/cothesis-prompt-lab:latest"
MAX_CASES="${PROMPT_LAB_MAX_CASES:-10}"

if [[ ! -f cloudbuild.prompt-lab.yaml ]]; then
  echo "ERROR: cloudbuild.prompt-lab.yaml not found (WS-D deliverable)." >&2
  exit 1
fi

echo "Building $IMG ..."
gcloud builds submit --config cloudbuild.prompt-lab.yaml --substitutions=_IMAGE="$IMG" --project="$PROJECT" .

echo "Updating job $JOB -> $IMG (PROMPT_LAB_MAX_CASES=$MAX_CASES)"
gcloud run jobs update "$JOB" \
  --image "$IMG" \
  --region "$REGION" \
  --project "$PROJECT" \
  --set-env-vars "PROMPT_LAB_MAX_CASES=$MAX_CASES"

echo "Done. Smoke test with:"
echo "  gcloud run jobs execute $JOB --region $REGION --project $PROJECT"
echo ""
echo "Prompt lab never auto-writes agents/prompts/ — merge proposals via human PR."
