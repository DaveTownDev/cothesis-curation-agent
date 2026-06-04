---
name: deploy-agent
description: Deploy the agent service and console to Cloud Run (human approves).
disable-model-invocation: true
allowed-tools: Bash
---
1. Confirm secrets exist in Secret Manager and the runtime SA has secretAccessor.
2. Agent: `adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=us-central1 --with_ui --trace_to_cloud agents/`; answer N to allow-unauthenticated; protect with IAP.
3. Console: `gcloud run deploy console --source console/ --region=us-central1 --update-secrets=CONSOLE_LOGIN_SECRET=console-login:latest`.
4. Report both URLs; the human approves and verifies login. See docs/OPERATIONS.md.
