# BUILD_PLAN — ordered, phase-gated build (8 days)

Deadline: 12 Jun 2026, 08:00 AWST (= 11 Jun, 5:00pm PT). Builder: Claude Code. Owner: Dave (checkpoints only). Each phase has acceptance criteria that must be demonstrably true (run it, see it) before moving on. **[DAVE]** marks a human gate.

## Day 0 — Guardrails (mostly [DAVE], before any code)
- **[DAVE]** Confirm paid billing; create the $500 budget (alerts 50/75/90/100%) **and** the Pub/Sub + Cloud Function billing kill-switch. Run `gcloud auth login` + `gcloud auth application-default login`.
- Claude: install Context7 + gcloud MCP; the repo already ships `.gitignore`, `.pre-commit-config.yaml`, hooks, CLAUDE.md, and the specs — run `pre-commit install`; enable the GCP services (docs/OPERATIONS.md); create the least-privilege runtime SA (**[DAVE]** approves the IAM grants).
- **Acceptance:** budget alert email received (test it); `pre-commit` blocks a planted fake secret; services enabled; auth works (`gcloud auth list`).

## Day 1 — Scaffold
- Verify ADK + Agents CLI versions live (Context7). `uvx google-agents-cli setup`; scaffold the ADK project into `agents/`; pin `google-adk==2.1.x`. Create the Firestore DB (us-central1) and the Vertex AI Search datastore (global). 
- **Acceptance:** `adk web agents/` shows a skeleton agent responding locally; Firestore + datastore exist.
- **[DAVE]** Drop data exports into `data/` and the per-type field maps into `docs/field_maps/`.

## Day 2 — Grounding + first two agents
- Load the methodology definitions + seed resources into Vertex AI Search; confirm indexing. Build **Discovery** (MCP server tools) and **Appraisal** (deterministic-API-first → Flash) per docs/AGENTS_SPEC.md. Define Firestore collections (docs/SCHEMA.md).
- **Acceptance:** a grounded query returns cited results in the playground; an appraisal writes a draft AIAssessment to Firestore with quality_score (0-100) and the 6 dimensions.

## Day 3 — Classification, Editorial, Reconciliation
- Build **Classification** (platform codes, 14 types, THESIS, FS), **Editorial** (short + long + plain, badges, difficulty — per agents/prompts/editorial.md and data/editorial_examples/), **Reconciliation** (dedup, title similarity 0.9). Commit failing tests first for each.
- **Acceptance:** one sample resource flows end-to-end producing a complete draft record; `code-reviewer` subagent checks the diff against this section.

## Day 4 — QC panel + arbiter + HITL
- Build the **QC evaluator panel** (per-dimension evaluators + the ready-made QC members) and the **Arbiter** routing gate (composite + panel agreement → auto-publish | review queue | human author, using IMPORT_* thresholds). Build the gold eval set (20-40 items). Wire HITL pause/resume.
- **Acceptance:** `adk eval` runs against the gold set; the arbiter routes a low-confidence item to the review queue and a high-confidence one to auto-publish.

## Day 5 — Console + dashboard
- Next.js + shadcn/ui review console (approve/reject → writes human-ratified Resource fields + provenance) and the progress dashboard (pipeline state, eval scores, trace links). The plain description renders as a labelled breakout card.
- **Acceptance:** the console renders a real pipeline item locally and an approval writes back to Firestore.

## Day 6 — Deploy + secrets + judge access
- Secret Manager for all secrets; `adk deploy cloud_run` (agent, private, IAP) and `gcloud run deploy console` (public + login). Cloud Scheduler + n8n monitoring on the pipeline.
- **Acceptance:** both URLs reachable; the console is gated by login; **[DAVE]** logs in as a judge would.

## Day 7 — Eval, observe, harden, rehearse
- `--trace_to_cloud` on; verify Cloud Trace; run the full eval and fix the top failures (TDD); confirm scale-to-zero; `gitleaks` over full history; record the demo video; write the business case (docs/SUBMISSION.md).
- **Acceptance:** clean end-to-end demo captured; spend check well under budget; no secret in history.

## Day 8 — Final review + submit
- **[DAVE]** Clean-clone build to confirm reproducibility; final secret/AWS sweep; LICENSE visible; set `min-instances=1` for judging; submit per the official rules.
