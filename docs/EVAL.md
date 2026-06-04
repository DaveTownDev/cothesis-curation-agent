# EVAL — testing, evaluation & observability

This is the quality story for judges (30% technical) and the thing most entries skip. Two layers + observability.

## 1. Deterministic tests (pytest) — committed BEFORE implementation
Tools (parsing, schema validation, Firestore writes), the arbiter's routing given fixed inputs, code-mapping (RS->SYN etc.), and the publish checklist. Fast, free, no LLM. Never weaken a test to make it pass.

## 2. ADK eval sets — agent behaviour
Gold set of **20-40** hand-curated Compendium items spanning resource types and the 4 MVP methodologies. Eval cases as `.test.json`; thresholds in `eval_config.json`; run via `adk eval` / the /run-evals skill. Primitives:
- `tool_trajectory_avg_score` — did discovery->appraisal->...->arbiter fire in the right order, did the arbiter route correctly.
- `final_response_match_v2` — LLM-as-judge for editorial quality vs reference.
- `hallucinations_v1` — grounding of claims against the Vertex AI Search context.
- `safety_v1` + rubric criteria — per-dimension QC.
**The QC evaluator panel is implemented with these primitives** — trajectory + LLM-as-judge + grounding over the gold set is the panel made demonstrable.

## 3. Observability
ADK emits OpenTelemetry spans (agent, sub-agent, LLM call, tool). Deploy with `--trace_to_cloud` for Cloud Trace. Capture per-span latency, tool I/O, token counts, grounding confidence, and arbiter routing decisions.

## Demo (Demo & Presentation 20%)
Surface: a live Cloud Trace waterfall of one resource moving through all agents + QC + arbiter; the eval scoreboard (trajectory + LLM-as-judge pass rates); and the review console + progress dashboard. That evidences production-grade evaluation, guardrails, and observability.
