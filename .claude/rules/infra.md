---
description: Rules for GCP / gcloud / deploy work
---
- gcloud runs from this shell under the human's ADC. Billing, IAM grants, deletes, --force, and --allow-unauthenticated decisions are gated to the human.
- Region: us-central1 for infra; GOOGLE_CLOUD_LOCATION=global for Gemini 3.x.
- Deploy to Cloud Run (not Agent Engine). Agent service: --no-allow-unauthenticated + IAP. Console: public + app login.
- Secrets via Secret Manager `--set-secrets`; runtime SA needs secretAccessor before deploy. See docs/OPERATIONS.md.
