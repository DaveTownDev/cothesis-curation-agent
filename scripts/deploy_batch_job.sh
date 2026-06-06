#!/usr/bin/env bash
# Rebuild the batch image from current source and point the Cloud Run Jobs at it.
# The jobs run the DETERMINISTIC in-process pipeline; each job keeps its own
# command/args (run-batch -> scripts.run_batch, sync-to-compendium -> scripts.sync_to_compendium),
# so updating only --image is enough. Not gated (no IAM/allow-unauth changes).
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-cothesis-curation-agent}"
REGION="${REGION:-us-central1}"
IMG="us-central1-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/cothesis-batch:latest"

echo "Building $IMG ..."
gcloud builds submit --config cloudbuild.batch.yaml --substitutions=_IMAGE="$IMG" --project="$PROJECT" .

for JOB in run-batch sync-to-compendium; do
  echo "Updating job $JOB -> $IMG"
  gcloud run jobs update "$JOB" --image "$IMG" --region "$REGION" --project "$PROJECT"
done

echo "Done. Smoke test with:"
echo "  gcloud run jobs execute run-batch --region $REGION --project $PROJECT --args=--dry-run,--batch-size,5"
