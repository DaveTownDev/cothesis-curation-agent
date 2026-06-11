#!/usr/bin/env bash
# Rebuild the benchmark image and point the Cloud Run Job `run-benchmark` at it.
#
# **[DAVE] human-gated** — do not run from CI or agent automation without approval.
# Prerequisites (WS-A): scripts/run_benchmark.py, Dockerfile.benchmark,
#   cloudbuild.benchmark.yaml, eval/baseline.json.
#
# Weekly Cloud Scheduler should invoke:
#   gcloud run jobs execute run-benchmark --region $REGION --project $PROJECT \
#     --args=--check-regression
#
# Not gated on IAM/allow-unauth changes (image + job update only).
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-cothesis-curation-agent}"
REGION="${REGION:-us-central1}"
JOB="run-benchmark"
IMG="us-central1-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/cothesis-benchmark:latest"

for f in cloudbuild.benchmark.yaml Dockerfile.benchmark; do
  if [[ ! -f $f ]]; then
    echo "ERROR: $f not found (WS-A deliverable)." >&2
    echo "Create Dockerfile.benchmark + cloudbuild.benchmark.yaml before deploying." >&2
    exit 1
  fi
done

echo "Building $IMG ..."
gcloud builds submit --config cloudbuild.benchmark.yaml --substitutions=_IMAGE="$IMG" --project="$PROJECT" .

SA="${RUNTIME_SA:-agent-runtime@cothesis-curation-agent.iam.gserviceaccount.com}"

if gcloud run jobs describe "$JOB" --region "$REGION" --project "$PROJECT" &>/dev/null; then
  echo "Updating job $JOB -> $IMG"
  gcloud run jobs update "$JOB" --image "$IMG" --region "$REGION" --project "$PROJECT"
else
  echo "Creating job $JOB -> $IMG"
  gcloud run jobs create "$JOB" \
    --image "$IMG" \
    --region "$REGION" \
    --project "$PROJECT" \
    --service-account "$SA" \
    --task-timeout 3600 \
    --max-retries 1 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=global"
fi

echo "Done. Smoke test with:"
echo "  gcloud run jobs execute $JOB --region $REGION --project $PROJECT --args=--check-regression"
echo ""
echo "Weekly Scheduler (human): create/update a job that executes run-benchmark with --check-regression."
echo "Keep separate from daily run-batch @ 20:00 UTC (see docs/OPERATIONS.md)."
