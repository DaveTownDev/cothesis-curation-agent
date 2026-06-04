# AIAssessment — Canonical Entity (Satellite Table)

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: entity_AIAssessment.md (restructured as satellite)
VERSION: unified-schema v1.0 (merge output)
PATTERN: Satellite table — 1:N to Resource, full audit history

## Purpose
AIAssessment stores LLM-generated quality assessments for Resources.
One Resource can have many AIAssessment records (one per assessment run).
The satellite table pattern (Conflict 9 Decision: option C) enables full audit history
and aligns with Patent B requirements for assessment traceability.
Resource.current_ai_assessment_id references the most-recent assessment.

The three-agent AI pipeline (Primary Assessor → Reviewer → Synthesis/Arbitrator, Z.AI GLM-4.6)
writes one AIAssessment record per run. Quality thresholds: auto-approve ≥80, human review 60-79,
auto-reject <60; ai_confidence <0.7 forces human review regardless of score.

## Composite Key
Primary key: `(resource_code, assessed_at)` — uniquely identifies each assessment event.
`resource_id` (UUID) is retained as an indexed column for cross-store joins but is NOT part of the PK.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `resource_code` | string | Yes | Resource.code | FK to parent resource (P4 code-based FK). Part of composite PK. |
| `resource_id` | string (uuid) | Yes | Resource.resource_id | UUID join key for cross-store queries (Convex, Neo4j, Qdrant). Indexed; not PK. |
| `assessed_at` | datetime | Yes | — | Timestamp of assessment run. Part of composite PK. Was: `assessed_at` on golden records (no home in canonical entity_schemas__Resource.md — gap now closed). |
| `model_version` | string | Yes | — | LLM model used e.g. `claude-sonnet-4-6`, `glm-4.6`. Was: `model_used` on golden records (renamed for clarity: version is more precise than used). |
| `assessment_prompt_version` | string | No | — | Version of the assessment prompt template used. Enables prompt-version-stratified analysis. |
| `ai_confidence` | number (0-100) | Yes | — | AI synthesis-agent overall confidence in this assessment. Was: `confidence` (matrix) / `ai_confidence` (canonical Resource schema) — canonical name wins. Scale: 0-100. Values <70 trigger human-review queue. |
| `quality_score` | number (0-100) | Yes | — | Overall AI quality score. Scale: 0-100. Was: 0-1 in matrix §6.2; 0-100 in canonical schema and directory §3.4 — canonical wins. Migration: multiply legacy 0-1 values × 100. |
| `quality_dimensions` | object | No | — | Per-dimension quality sub-scores feeding quality_score. Dimensions: `relevance`, `accuracy`, `authority`, `currency`, `accessibility`, `practical_utility`, `ebm_level` (article-only). Sub-dimensions vary by subtype. |
| `ai_subtype_signal` | string | No | — | AI-inferred subtype classification signal. Was: `subtype_classification` (renamed per Task I). Distinct from Resource.resource_subtype_code (the stored FK). |
| `proposed_badges` | string[] | No | — | AI-proposed recommendation badges. Was: `editorial_badges` on Resource (split per Task I / Conflict 9). Values: `editors_choice` \| `best_free` \| `best_beginners` \| `best_time_poor` \| `essential` \| `expert_pick`. Human ratification produces Resource.editorial.editorial_badges. |
| `relevance_to_methodology_codes` | string[] | No | Methodology.code[] | AI-assessed methodology relevance codes. Distinct from Resource.methodology_codes (human-ratified). |
| `relevance_to_discipline_codes` | string[] | No | ProfessionalDiscipline.code[] | AI-assessed discipline relevance. Distinct from Resource.discipline_codes (human-ratified). |
| `thesis_stage_signals` | string[] | No | — | AI-assessed THESIS stage relevance signals. Phase codes (two-letter, migration 08): `TH` \| `HI` \| `EV` \| `ST` \| `IN` \| `SH`. Was: `getting_started` \| `literature_background` \| `planning_ethics` \| `doing_research` \| `making_sense` \| `writing_sharing` (renamed per Task I). |
| `difficulty_level` | string (enum) | No | — | AI-assessed difficulty: `beginner` \| `intermediate` \| `advanced`. |
| `summary` | string | No | — | AI-generated summary of the resource (extended form). Was: `editorial_description_long` on golden records (renamed: summary is more neutral — this is AI-generated, not editorial). |
| `strengths` | string[] | No | — | AI-assessed strengths of the resource. |
| `limitations` | string[] | No | — | AI-assessed limitations of the resource. |
| `trainee_suitability_score` | number (0-100) | No | — | AI-assessed suitability for trainees specifically. |
| `language_detected` | string | No | — | ISO 639-1 language code as detected by the AI pipeline. |
| `requires_human_review` | boolean | Yes | — | True if ai_confidence < 70 OR quality_score in 60-79 range → routes to human-review queue. Was: implicit in entity_schemas__Resource.md (no explicit boolean) — gap now closed. |
| `pipeline_run_id` | string | No | — | Identifier for the assessment pipeline run (links Primary Assessor → Reviewer → Synthesis agent outputs). |

## Page Mixin Fields

NOT ATTACHED. AIAssessment is a backend satellite table, not surfaced on Compendium. No slug, no page_title, no has_page.

## Derived Fields

(none)

## Relationships

| Relation | Direction | Target | FK | Notes |
|---|---|---|---|---|
| resource_code | many→one | Resource | `resource_code` → Resource.code | Parent resource. Every AIAssessment belongs to exactly one Resource. |
| (resource_code, assessed_at) | one→one (back-ref) | Resource.current_ai_assessment_id | ← Resource.current_ai_assessment_id | Most-recent assessment is referenced from Resource. Updated when a new assessment is written. |
| Three-agent pipeline | producer (process) | — | `pipeline_run_id`, `model_version`, `assessed_at`, `ai_confidence`, `requires_human_review` | Pipeline is the write-path, not an entity. These fields capture the pipeline audit trail. |

## Notes

- **quality_score scale: 0-100.** Migration: multiply any legacy 0-1 values × 100. The matrix §6.2 documented 0-1; the canonical schema and directory §3.4 used 0-100. Canonical wins.
- **proposed_badges vs editorial_badges**: AI suggestions only → stored on AIAssessment.proposed_badges. Human editorial ratification → stored on Resource.editorial.editorial_badges. The matrix classified badges as LLM-authored; the canonical schema and directory §8 say badges are editorial-only. Resolution: both are true — AI proposes, human ratifies. The satellite table makes this split explicit and traceable.
- **Full assessment history is queryable**: `SELECT * FROM ai_assessment WHERE resource_code = 'X' ORDER BY assessed_at DESC`. The satellite table pattern (vs embedded mixin) is what enables this.
- **ai_confidence scale**: The canonical Resource schema used 0-1 for `ai_confidence`; this is normalised to 0-100 in the satellite table for consistency with quality_score. Threshold: <70 triggers human review (equivalent to the legacy <0.7 threshold).
- **summary vs editorial_description**: `summary` here is AI-generated (stored on AIAssessment). `editorial_description` on Resource is CoThesis-editorial-authored and "never copied from source" — these are distinct fields with distinct authorship and distinct purposes.
- **Fields with no prior canonical home**: `assessed_at`, `model_version`, `requires_human_review`, `ai_subtype_signal`, `summary` appeared in all 13 golden-record files but had no home in `entity_schemas__Resource.md`. The satellite table is their canonical home.
- **model_version naming**: renamed from `model_used` (golden records) for precision — version is a more specific and useful identifier than "used".
