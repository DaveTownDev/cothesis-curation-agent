---
name: run-evals
description: Run deterministic tests and ADK eval sets and report scores.
---
1. `pytest -q` for tool/schema/routing tests.
2. `adk eval` against the gold set (trajectory + final_response_match_v2 + hallucinations_v1).
3. Paste raw scores; flag any criterion below threshold (docs/EVAL.md). Do not alter tests to pass.
