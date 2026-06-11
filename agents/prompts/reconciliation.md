<!-- prompt-version: reconciliation@1.0.0 -->
# Reconciliation agent prompt

Rebuild on Gemini (Flash). Dedupe each appraised+classified candidate against existing resources using title similarity (threshold `IMPORT_TITLE_SIMILARITY_THRESHOLD=0.9`). For MVP, on a probable duplicate: STOP (do not merge) and flag it. Otherwise assemble the final draft record (universal Resource fields + AIAssessment fields + `type_fields` per docs/SCHEMA.md) and set `editorial_status: proposed`. Canonical field names: `stage_codes` (not `thesis_stages`), `discipline_codes` (not `specialty_tags`), `resource_type_code` (not `resource_type`), `resource_subtype_code` (not `subtype`), `summary` (not `editorial_description_long`), `proposed_badges` (not `editorial_badges`), `ai_confidence` 0-100 (not `confidence` 0-1), `thesis_stage_signals` on AIAssessment (not `thesis_stages`), `relevance_to_discipline_codes` on AIAssessment (not `specialty_tags`).

Output: the assembled draft record, or `{ "duplicate_of": <id>, "action": "stop" }`.
