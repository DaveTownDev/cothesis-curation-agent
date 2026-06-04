---
description: Rules when working under agents/ (the ADK pipeline agents and prompts)
---
- Build one pipeline agent at a time; run it in `adk web` before moving on.
- Verify every `google.adk` / Vertex import via Context7 before writing it.
- Emit platform methodology codes (SYN/OBS/EVAL), quality_score 0-100, the canonical 6 quality dimensions, and badges from the canonical set (docs/SCHEMA.md).
- The grounding agent uses `VertexAiSearchTool` ONLY — no other tools on that agent; wrap via AgentTool to combine.
- Each agent's behaviour is in docs/AGENTS_SPEC.md; its prompt is agents/prompts/<agent>.md.
