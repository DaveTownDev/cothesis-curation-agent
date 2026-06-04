---
description: Rules when working under tests/ and eval sets
---
- Two layers: deterministic pytest (tools, Firestore writes, arbiter routing) committed BEFORE implementation, and ADK eval sets for agent behaviour.
- ADK primitives: tool_trajectory_avg_score, final_response_match_v2 (LLM-as-judge), hallucinations_v1, safety_v1, rubric criteria.
- Gold set: 20-40 hand-curated items spanning resource types and the 4 MVP methodologies.
- Never weaken or rewrite a test to make it pass; fix the code. See docs/EVAL.md.
