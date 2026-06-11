<!-- prompt-version: qc_panel@1.0.0 -->
# QC evaluator panel prompt(s)

Implemented with ADK eval primitives (docs/EVAL.md), not a single LLM call. The panel = one evaluator per quality dimension (relevance, accuracy, authority, currency, accessibility, practical_utility) plus the ready-made members: ai-pattern-scanner (AI-tell/voice), voice-reviewer (brand voice), plain-jargon-check, badge-check, and **taxonomy_check** (`run_taxonomy_qc_check` — deterministic validation of subtype/methodology/skills via `agents.shared.taxonomy_rules.validate_taxonomy_draft`).

Each evaluator returns `{ "dimension": string, "score": number (0-100), "pass": bool, "reasoning": string }`. The panel result aggregates these and surfaces **disagreement** (variance across evaluators), which is itself an escalation signal for the arbiter. Use rubric criteria + `final_response_match_v2` + `hallucinations_v1` so the panel is reproducible and demonstrable to judges.
