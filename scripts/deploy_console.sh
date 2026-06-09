#!/usr/bin/env bash
# Redeploy HITL console to Cloud Run from main.
# Prereq: gcloud auth login && gcloud auth application-default login
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-cothesis-curation-agent}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE="console"
CONSOLE_URL="https://console-791873451733.us-central1.run.app"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Deploying $SERVICE to $PROJECT ($REGION)..."
gcloud run deploy "$SERVICE" \
  --source "$ROOT/console" \
  --project="$PROJECT" \
  --region="$REGION" \
  --min-instances=1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT,CONSOLE_PUBLIC_URL=$CONSOLE_URL" \
  --update-secrets="CONSOLE_LOGIN_SECRET=console-login:latest" \
  --quiet

echo "Done. Console URL: $CONSOLE_URL"
echo "Optional: firebase deploy --only firestore:rules --project $PROJECT"
