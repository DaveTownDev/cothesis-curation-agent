# CLAUDE.md — Project Constitution

CoThesis Curation Agent: a multi-agent system (ADK on Vertex AI / Cloud Run) that enriches and curates research resources for the CoThesis Compendium, with a QC evaluator panel, an arbiter routing gate, a human review console, and a progress dashboard. Built for the Google for Startups AI Agents Challenge, Track 1.

**Source of truth = the `docs/` specs.** Read `docs/BUILD_PLAN.md` for the ordered build, `docs/AGENTS_SPEC.md` + `agents/prompts/` for agent behaviour, `docs/SCHEMA.md` for the record shape, `docs/OPERATIONS.md` for GCP. This file is rules and pointers only.

## Hard rules (these hold 100% of the time)
- **Never trust training data for ADK, Vertex AI, google-genai, or Cloud Run.** Use Context7 (`use context7`) or the official repos (`github.com/google/adk-python`, `google.github.io/adk-docs`) before writing any of their APIs. ADK is GA and fast-moving — pin `google-adk==2.1.x` (never below 2.0.1).
- **Region & models:** Gemini 3 (Pro + Flash/Flash-Lite) on the **global** endpoint (`GOOGLE_CLOUD_LOCATION=global`); infra in `us-central1`. The Compendium's data is public, so no AU residency constraint.
- **`VertexAiSearchTool` is exclusive** — it cannot share an agent with other tools. Isolate grounding in its own sub-agent or wrap via `AgentTool`.
- **Secrets never enter the repo.** No keys, no `.env` with real values, no service-account JSON, no Tailscale IPs / VPS hostnames, no AWS code. Real values come from Secret Manager at deploy. Use placeholders in samples.
- **No completion claims without fresh verification evidence.** Before saying anything is done, run the command fresh and paste the output. "Tests pass" with no visible run is not done.
- **Gated to the human (never do these without explicit approval):** `git push`, `gcloud billing`, any IAM role grant, `gcloud ... delete`, anything `--force`, and any `--allow-unauthenticated` decision.
- **Emit platform methodology codes** (SYN-01, SYN-02, OBS-01, EVAL-01), never the legacy RS/OD display codes. See `docs/TAXONOMY.md` for the mapping.
- **quality_score is 0–100**; quality dimensions are the canonical six (relevance, accuracy, authority, currency, accessibility, practical_utility); editorial badges come from the canonical set in `docs/SCHEMA.md`.

## How to work
- Start every non-trivial phase in **plan mode**; get the plan approved; then implement exactly as written.
- Build the pipeline **sequentially in the main thread**, one agent per phase. Use subagents only for read-only research, diff review (`code-reviewer`), and running evals (`eval-runner`).
- Small verifiable steps: build one agent, run it in `adk web`, then move on. Don't build five before anything runs.
- Test-first: write the eval/unit test, confirm it fails, commit it, then implement until green without modifying the test.
- Commit after each verified task (small, logical commits). Conventional messages. **Pushes are the human's job.**
- Keep `STATE.md` current after every task. On "continue", read `STATE.md` and resume. When compacting, preserve the modified-file list and the test/deploy commands.

## Stack
Python 3.11+, ADK 2.x, Gemini 3 on Vertex AI, Cloud Run, Vertex AI Search (grounding), Firestore (draft store + pipeline state), Secret Manager, Next.js + shadcn/ui (console). Context7 + the project MCP server inside Claude Code.
