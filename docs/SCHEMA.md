# SCHEMA — canonical record shape & state

**Authoritative field existence and shape:** `docs/reference/entities/*.canonical.md` (May 17 merge output).  
**Authoritative enrichment/QC behaviour** (score scale, allowed values, badges, routing): `docs/reference/compendium_enrichment_qc_spec.md` (Jun 4).  
`database_schema_v4.md` and `field_mapping_*_complete.md` are supporting detail beneath those.

`editorial_description_plain` is an **intentional addition** not in the canonical entities — preserve on all agents and in the console.

## AI-proposes / human-ratifies
- Agents write a draft **AIAssessment** (`editorial_status: proposed`).
- The arbiter routes it; the human console writes the ratified **Resource** fields + provenance and moves `in_review -> published`.

---

## Resource — universal fields (every resource)

| Field | Type | Notes |
|---|---|---|
| `resource_type_code` | string (enum 14) | One of the 14 types in docs/TAXONOMY.md |
| `resource_subtype_code` | string \| null | FK → ResourceSubtype.code; null for `book_chapter` |
| `editorial_description` | string | **SHORT** — CoThesis-authored 1–2 sentences; the canonical "short" display field |
| `editorial_description_plain` | string | **PLAIN breakout card** — jargon-free; no research terms (see AGENTS_SPEC Editorial) |
| `editorial_note` | string \| null | **Optional "Editor's note"** — human-authored rationale ("why this matters"); required for `featured` status only; never AI-written |
| `quality_score` | number | **0-100** (denormalised snapshot from current AIAssessment) |
| `methodology_codes` | string[] | **platform** codes (SYN/OBS/EVAL…); max 5 |
| `discipline_codes` | string[] | Vocabulary **specialty codes** (e.g. `CARDIO`, `PSYCH`); max 3 (was: `specialty_tags`) |
| `domain_codes` | string[] | Optional cross-specialty domain codes (e.g. `DIGHEALTH`, `EBM`); max 3 |
| `stage_codes` | string[] | THESIS: TH/HI/EV/ST/IN/SH (was: `thesis_stages`) |
| `skill_codes` | string[] | Foundation Skills FS-01..FS-16 |
| `difficulty_level` | string | beginner / intermediate / advanced |
| `time_to_consume` | string | estimate, calibrated to ~100 wpm for dense material |
| `access_type` | string | free / freemium / paid / subscription / institutional / open_access |
| `content_format` | string | text / video / audio / interactive / pdf / spreadsheet / infographic / flowchart / slide_deck / mixed |
| `alternative_titles` | string[] | **novice-vocabulary search surface** (hidden, for recall — NOT the visible plain card) |
| `type_fields` | object (JSONB) | per-type golden-record fields, discriminated by `resource_type_code` (see docs/field_maps/) |
| `field_provenance` | object (JSON) | universal per-field provenance record |
| `editorial_status` | enum | `proposed \| in_review \| published \| archived \| deprecated` |
| `current_ai_assessment_id` | string \| null | FK → AIAssessment.(resource_code, assessed_at); points to most-recent assessment |
| `last_verified` | date | when CoThesis last confirmed URL + info is current |

### Resource.editorial embedded object (human-ratified)

| Field | Type | Notes |
|---|---|---|
| `editorial_badges` | string[] | **Human-ratified** badges (max 3, canonical set below). AI proposals live on AIAssessment.proposed_badges. |
| `editorial_note` | string \| null | Human "Editor's note" block; required for `featured` |
| `editorial_status` | enum | `proposed \| in_review \| published \| archived \| deprecated` |
| `editorial_reviewed_by` | string | user_code of last reviewer |
| `editorial_reviewed_at` | datetime | timestamp of last editorial review |

---

## AIAssessment — satellite table (AI pipeline writes; 1 Resource → many AIAssessments)

One AIAssessment record per pipeline run. `Resource.current_ai_assessment_id` points to the most-recent one.

| Field | Type | Notes |
|---|---|---|
| `resource_code` | string | FK → Resource.code (part of composite PK) |
| `assessed_at` | datetime | timestamp of this assessment run (part of composite PK) |
| `model_version` | string | LLM used e.g. `gemini-pro-latest` |
| `assessment_prompt_version` | string | prompt template version |
| `pipeline_run_id` | string | links Primary Assessor → Reviewer → Synthesis agent outputs |
| `ai_confidence` | number (0-100) | synthesis-agent overall confidence; **<70 forces human review regardless of quality_score** |
| `quality_score` | number (0-100) | overall AI quality score; **≥80 auto-approve, 60-79 human review, <60 auto-reject** |
| `quality_dimensions` | object | per-dimension sub-scores (see below) |
| `summary` | string | **LONG display slot** — AI-generated 3-5 sentence description; distinct from `editorial_description` (which is CoThesis-editorial-authored) |
| `proposed_badges` | string[] | **AI-suggested** badges (max 3, canonical set); human ratification produces Resource.editorial.editorial_badges |
| `ai_subtype_signal` | string | AI-inferred subtype signal (distinct from Resource.resource_subtype_code FK) |
| `relevance_to_methodology_codes` | string[] | AI-assessed methodology relevance (platform codes) |
| `relevance_to_discipline_codes` | string[] | AI-assessed discipline relevance |
| `thesis_stage_signals` | string[] | AI-assessed THESIS stage signals: TH/HI/EV/ST/IN/SH (was: `thesis_stages`) |
| `difficulty_level` | string | beginner / intermediate / advanced |
| `strengths` | string[] | AI-assessed resource strengths |
| `limitations` | string[] | AI-assessed resource limitations |
| `trainee_suitability_score` | number (0-100) | AI-assessed suitability specifically for trainees |
| `language_detected` | string | ISO 639-1 |
| `requires_human_review` | boolean | true when ai_confidence <70 OR quality_score 60-79; routes to review queue |

### quality_dimensions shape

**Universal (all 6 present on every resource):**
```
"relevance":        { "score": 0-100, "weight": number, "reasoning": string }
"accuracy":         { ... }
"authority":        { ... }
"currency":         { ... }
"accessibility":    { ... }
"practical_utility": { ... }
```

**Conditional (articles only — 7th dimension in quality_dimensions):**
```
"ebm_level": { "score": 0-100, "weight": number, "reasoning": string }
```
`ebm_level` maps the article's position in the evidence hierarchy (systematic review > RCT > cohort > case series, etc.). Omit entirely for non-article resource types.

---

## Console display contract

Resource detail page renders **four slots**:

| Slot | Field | Source | Visibility |
|---|---|---|---|
| Short | `editorial_description` | CoThesis-editorial-authored (AI-drafted, human-ratified) | Always |
| Long | `AIAssessment.summary` | AI-generated 3-5 sentences | Always (present on every ratified resource) |
| Plain card | `editorial_description_plain` | AI-generated, jargon-free | Always (breakout card beneath long) |
| Editor's note | `editorial_note` | Human-authored only | Featured/curated resources only; clearly labelled as editor's voice |

---

## Canonical badge set (max 3)
`editors_choice`, `best_free`, `best_beginners`, `best_time_poor`, `essential`, `expert_pick`.

AI proposes → `AIAssessment.proposed_badges`. Human ratifies → `Resource.editorial.editorial_badges`.

## Two-layer score model

**Routing (0-1 scale) — arbiter gate, matches IMPORT_* thresholds in `.env`:**
- `relevance_score` — from Classification agent; how relevant the resource is to the target methodology/audience.
- `classification_confidence` — from Classification agent; confidence in the type/methodology assignment.

**Quality/display (0-100 scale) — AIAssessment, shown on cards:**
- `quality_score` — overall editorial quality; drives card bar and publish checklist.
- `ai_confidence` — synthesis-agent confidence in the assessment; <70 forces human review.

Do not conflate the two layers. The arbiter routes on `relevance_score` and `classification_confidence` (0-1). `ai_confidence` is a quality signal, not a routing threshold.

## Quality routing (from compendium_enrichment_qc_spec.md)
- `quality_score ≥ 80` → auto-approve
- `quality_score 60-79` → human review queue
- `quality_score < 60` → auto-reject
- `ai_confidence < 70` → human review regardless of score
- **Display:** hide `quality_score` on the card below 60.

## Firestore collections
- `drafts` — AIAssessment proposals (pre-ratification).
- `resources` — published/ratified Resource records.
- `pipeline_state` — per-resource state machine + agent decisions + provenance.
- `review_queue` — items routed to humans, with the arbiter's reason and panel result.
- `eval_failure_bucket` — structured HITL / QA failures for the offline prompt lab (see below).
- `eval_gold_cases` — HITL-captured ADK gold eval cases (`eval_id` doc key); export via `scripts/export_gold_from_firestore.py`.
- `prompt_proposals` — proposed prompt diffs awaiting human PR merge (see below).
- `prompt_lab_runs` — audit trail for `prompt-lab-run` Cloud Run Job executions (see below).

### `eval_failure_bucket`

HITL-captured taxonomy / classification failures. **Append-only** from the console; consumed by the offline prompt lab Job. Typed model: `agents/shared/firestore_schemas.py` → `EvalFailureBucketDoc`.

| Field | Type | Notes |
|---|---|---|
| `resource_code` | string | FK → Resource / review_queue item |
| `agent` | string | Pipeline stage: `classification`, `editorial`, `appraisal`, … |
| `field` | string | Disputed draft field, e.g. `methodology_codes`, `discipline_codes` |
| `human_label` | string | Reviewer description of the error |
| `prompt_version` | string | Registry version at failure time, e.g. `classification@1.0.0` |
| `created_at` | datetime | ISO-8601 UTC; indexed DESC for recent-first listing |
| `origin` | enum | `hitl_flag` \| `qa_requeue` \| `send_to_lab` \| `benchmark` |
| `pipeline_run_id` | string \| null | Optional link to `pipeline_state` run |
| `review_queue_id` | string \| null | Optional Firestore doc id on `review_queue` |
| `consumed_by_lab_run_id` | string \| null | Set when a prompt-lab Job picks up this record |

**Indexes:** composite `consumed_by_lab_run_id` ASC + `created_at` DESC for pending-failure queries (`firestore.indexes.json`).

### `prompt_proposals`

Offline prompt lab output — one unified diff per target file. **Never** auto-written to `agents/prompts/`; human merges via PR after console approve. Typed model: `PromptProposalDoc`.

| Field | Type | Notes |
|---|---|---|
| `status` | enum | `pending` \| `approved` \| `rejected` \| `merged` — indexed |
| `target_prompt_file` | string | Repo-relative path, e.g. `agents/prompts/classification.md` |
| `unified_diff` | string | Unified diff text |
| `rationale` | string | Analyst summary tied to failure bucket ids |
| `failure_bucket_ids` | string[] | Source `eval_failure_bucket` doc ids |
| `eval_delta` | object \| null | Subset benchmark vs `eval/baseline.json` (see `EvalDelta`) |
| `lab_run_id` | string \| null | FK → `prompt_lab_runs` doc id |
| `created_at` | datetime | Proposal creation time |
| `reviewed_at` | datetime \| null | Human decision timestamp |
| `reviewed_by` | string \| null | Console user identifier |
| `review_notes` | string \| null | Optional dismiss / merge notes |

**Indexes:** `status` ASC; composite `status` + `created_at` DESC for console listing.

### `prompt_lab_runs`

Audit record for one `prompt-lab-run` Cloud Run Job execution. Typed model: `PromptLabRunDoc`.

| Field | Type | Notes |
|---|---|---|
| `status` | enum | `running` \| `succeeded` \| `failed` \| `cancelled` |
| `started_at` | datetime | Job start (UTC) |
| `completed_at` | datetime \| null | Job end |
| `failure_bucket_ids` | string[] | Input failure doc ids (capped by `PROMPT_LAB_MAX_CASES`) |
| `max_cases` | number | Cost cap mirror of env default `10` |
| `proposal_ids` | string[] | Output `prompt_proposals` doc ids |
| `model_version` | string \| null | LLM used for analyst/editor replay |
| `error` | string \| null | Failure message when `status=failed` |

### Compendium sync fields (`resources`, post-publish)

Written when the HITL console or `scripts/sync.py` POSTs to Compendium `/api/import/json`.

| Field | Type | Notes |
|---|---|---|
| `compendium_synced_at` | datetime \| null | Set on successful import POST |
| `compendium_batch_id` | string \| null | `import_batch_id` from Compendium response |
| `compendium_sync_error` | string \| null | Last sync failure message; cleared on success |
| `compendium_id` | string \| null | Compendium `resource_id` when returned by import API |
| `compendium_url` | string \| null | Public library URL — from API or constructed from id/slug |

If the import API returns only `import_batch_id` (no per-resource array), sync still succeeds but `compendium_id` / `compendium_url` may be null until Compendium exposes them.

## State machine
`discovered -> appraised -> classified -> edited -> reconciled -> qc_panel -> arbiter ->` then routing: `auto_accept -> in_review (publish checklist) -> published` | `review_needed -> (human) -> published|excluded` | `auto_exclude`.

`editorial_status` full enum: `proposed | in_review | published | archived | deprecated`.

## Publish checklist (required for `published`)
editorial_description present · ≥1 methodology_code (platform) when required for `resource_type_code` (optional for software/community/funding/dataset/template/visual_reference) · quality_score present · link verified · human-ratified (editorial_reviewed_by + editorial_reviewed_at set on Resource.editorial).

## Per-type fields
The full golden-record field set per resource type lives in `docs/field_maps/field_mapping_<type>_complete.md`. `type_fields` is discriminated by `resource_type_code` (the 14 types in docs/TAXONOMY.md). MVP is all 14 types; the four MVP methodologies are article-dominant but every type's path is built.

The `dataset` type includes the `research_database` subtype (PubMed, Embase, ClinicalTrials.gov, etc. — queryable systems, not downloadable data files).
