# SCHEMA RECONCILIATION

Authority order applied (per intake instructions):
1. `_merge/entities/*.canonical.md` (May 17) — field existence and shape on Resource, ResourceSubtype, AIAssessment
2. `compendium_enrichment_qc_spec.md` (Jun 4) — enrichment/QC behaviour, score scale, allowed values, badges, routing
3. `database_schema_v4.md` and `field_mapping_*_complete.md` — supporting detail beneath those

`editorial_description_plain` is an **intentional addition** not in v4 or canonical files. Preserved throughout.

Proposed edits to `docs/SCHEMA.md` are listed below. **Not applied — awaiting your confirmation.**

---

## 1. Fields present in SCHEMA.md that differ from or are absent in Resource.canonical.md

### 1.1 `editorial_description_long` — CONFLICT: field renamed / relocated

**SCHEMA.md says:** universal field `editorial_description_long` (3-5 sentences).

**Resource.canonical.md says:** this field does not exist on Resource. The note reads:
> "editorial_description_long is an alias for editorial_note — resolved: editorial_note is the canonical name."

Two distinct fields now fill this space:
- `AIAssessment.summary` — AI-generated extended description of what the resource is (stored on the assessment satellite, not Resource). Renamed from `editorial_description_long` per Task I.
- `Resource.editorial.editorial_note` — human-authored assessment ("why this matters"); required only for `featured` status.

**Proposed SCHEMA.md edit:**
- Remove `editorial_description_long` from Universal fields table.
- Add `summary` to the AIAssessment section (AI pipeline writes it; it is NOT the editorial long description).
- Add `editorial_note` to a `Resource.editorial` embedded-object section (human-authored, required for `featured`).
- Keep `editorial_description` (AI-authored 1–2 sentence factual summary, required for all published resources).
- Keep `editorial_description_plain` (intentional addition — no change).

**Flag:** The console rule (`.claude/rules/console.md`) says "Render three description fields per resource: short, long, and the jargon-free PLAIN version". The canonical split is `editorial_description` (short/1–2 sentences), `editorial_note` (editorial rationale, human-only, gated on `featured`) and `editorial_description_plain` (plain addition). If the console's "long" means `editorial_note`, it must only show when `editorial_note` is populated. Confirm which field maps to which display slot before building the console.

---

### 1.2 `editorial_badges` — CONFLICT: field split across two entities

**SCHEMA.md says:** `editorial_badges` is a universal field on Resource (max 3, canonical set).

**Resource.canonical.md says:** editorial badges are split:
- `AIAssessment.proposed_badges` — AI-suggested badges (stored on the assessment, AI-authored).
- `Resource.editorial.editorial_badges` — human-ratified badges (stored on Resource.editorial, human-authored).

Both are max 3; same canonical value set: `editors_choice | best_free | best_beginners | best_time_poor | essential | expert_pick`.

**Proposed SCHEMA.md edit:**
- Remove `editorial_badges` from Universal fields table.
- Add `proposed_badges` to AIAssessment section.
- Add `editorial_badges` to a `Resource.editorial` embedded-object section.
- Add note: "AI proposes → human ratifies. AI proposals live on AIAssessment.proposed_badges. Ratified set lives on Resource.editorial.editorial_badges."

---

### 1.3 `provenance` object — CONFLICT: replaced by distributed fields

**SCHEMA.md says:** `provenance: object { ai_drafted, model, reviewer, drafted_at, approved_at }`.

**Resource.canonical.md says:** no `provenance` object. These fields are distributed:
- `field_provenance` (JSON) on Resource — universal provenance JSON.
- `model_version`, `assessment_prompt_version`, `pipeline_run_id`, `assessed_at` on AIAssessment — assessment audit trail.
- `Resource.editorial.editorial_reviewed_by`, `editorial_reviewed_at` — human review provenance.

**Proposed SCHEMA.md edit:**
- Remove `provenance` object from Universal fields table.
- Add `field_provenance` to Resource fields.
- Split audit fields into AIAssessment section (`model_version`, `assessment_prompt_version`, `pipeline_run_id`, `assessed_at`) and Resource.editorial section (`editorial_reviewed_by`, `editorial_reviewed_at`).

---

### 1.4 `editorial_status` enum — CONFLICT: incomplete value list

**SCHEMA.md says:** `proposed -> in_review -> published`.

**Resource.canonical.md says:** `proposed | in_review | published | archived | deprecated`.

**Proposed SCHEMA.md edit:** Add `archived` and `deprecated` to the state machine enum. State machine diagram can remain simplified (the linear path is the happy path); note the two exit states.

---

### 1.5 `requires_human_review` — CONFLICT: field location

**SCHEMA.md says:** `requires_human_review: boolean` is a universal Resource field.

**AIAssessment.canonical.md says:** `requires_human_review` lives on AIAssessment (not Resource). Triggered when `ai_confidence < 70` OR `quality_score` 60–79.

**Proposed SCHEMA.md edit:** Move `requires_human_review` from Universal fields table to AIAssessment section. Note the routing logic: `ai_confidence < 70` forces review regardless of score.

---

### 1.6 `quality_dimensions` — MINOR DIFFERENCE: 7th dimension for articles

**SCHEMA.md says:** 6 canonical dimensions (relevance, accuracy, authority, currency, accessibility, practical_utility).

**AIAssessment.canonical.md says:** same 6 plus `ebm_level` (article-only).

No conflict for the universal schema. **Proposed SCHEMA.md edit:** Add footnote: "Articles also carry `ebm_level` as a 7th quality dimension in `type_fields`."

---

### 1.7 `alternative_titles` — ALIGNMENT NOTE

**SCHEMA.md says:** `alternative_titles: string[]` — "novice-vocabulary search surface (hidden, for recall)".

**Resource.canonical.md says:** `alternative_titles: string[]` — "Aliases and abbreviations for search recall. Not public."

These match. No edit needed. The SCHEMA.md parenthetical "(hidden, for recall — NOT the visible plain card)" is accurate and can stay.

---

## 2. Fields in Resource.canonical.md NOT in SCHEMA.md (proposed additions)

These are fields the agents will need to write or read:

| Field | On entity | Notes |
|---|---|---|
| `ai_confidence` | AIAssessment | 0-100; <70 forces human review |
| `ai_subtype_signal` | AIAssessment and Resource | AI classification signal; distinct from `resource_subtype_code` FK |
| `summary` | AIAssessment | AI-generated extended description (was `editorial_description_long`) |
| `proposed_badges` | AIAssessment | AI badge suggestions (pre-ratification) |
| `relevance_to_methodology_codes` | AIAssessment | AI-assessed methodology relevance |
| `relevance_to_discipline_codes` | AIAssessment | AI-assessed discipline relevance |
| `thesis_stage_signals` | AIAssessment | AI-assessed THESIS stage signals |
| `strengths` | AIAssessment | AI-assessed resource strengths |
| `limitations` | AIAssessment | AI-assessed resource limitations |
| `trainee_suitability_score` | AIAssessment | 0-100; AI-assessed trainee suitability |
| `pipeline_run_id` | AIAssessment | Links Primary Assessor → Reviewer → Synthesis agent outputs |
| `field_provenance` | Resource | Universal field-level provenance JSON |
| `resource_subtype_code` | Resource | FK to ResourceSubtype.code |
| `type_fields` | Resource | JSONB; subtype-specific extension fields (already referenced in SCHEMA.md) |

**Proposed SCHEMA.md edit:** Add an `AIAssessment fields` section listing the above, with a note that this is the satellite table the pipeline writes (one per assessment run, many per resource). Add `field_provenance` and `resource_subtype_code` to the Resource universal fields.

---

## 3. resource_database / research_database type question — RESOLVED

**Finding:** `ResourceSubtype.research_database.canonical.md` has `PARENT_TYPE: dataset`. It is **a subtype of `dataset`**, not a 15th ResourceType.

**Detail:** Added in taxonomy v2.2 (OQ-005 resolution). Subtype count bumped from 61 → 62. The `dataset` ResourceType now has 4 subtypes: `research_dataset`, `teaching_dataset`, `open_data_portal`, `research_database`.

**The 14-type `resource_type_code` enum is unchanged.** No action required on the classifier. `docs/TAXONOMY.md` correctly lists `dataset` as one of the 14 types.

**Proposed SCHEMA.md edit:** None for the type list. Optionally note that `dataset` includes the `research_database` subtype (PubMed, Embase, ClinicalTrials.gov, etc.).

---

## 4. methodology_codes code-space — CLARIFICATION

`Resource.canonical.md` says `methodology_codes → Methodology.code[]`. The taxonomy JSON uses internal IDs (REV-01, OBS-01, QI-01). `docs/TAXONOMY.md` and `CLAUDE.md` say agents emit platform codes (SYN-01, SYN-02, OBS-01, EVAL-01).

**Resolution:** The platform codes (SYN-01 etc.) are the canonical `Methodology.code` values for the MVP methodologies. The taxonomy JSON IDs (REV-01, QI-01) are source-taxonomy internal codes used only in the grounding source data. The classifier emits platform codes; those are what go into `Resource.methodology_codes`. No change to agent spec.

**Crosswalk for agents (taxonomy JSON ID → platform code):**

| Taxonomy JSON ID | Platform code | Name |
|---|---|---|
| REV-01 | SYN-01 | Narrative Systematic Review |
| REV-02 | SYN-02 | Scoping Review |
| OBS-01 | OBS-01 | Retrospective Chart Review |
| QI-01 | EVAL-01 | Standards-Based Clinical Audit |

---

## 5. `editorial_description_plain` — INTENTIONAL ADDITION

Not in `Resource.canonical.md`, `database_schema_v4.md`, or `compendium_enrichment_qc_spec.md`. Intentionally added as a CoThesis-agent-specific enrichment field. Preserved in `docs/SCHEMA.md` as specified.

---

## 6. Quality routing thresholds — compendium_enrichment_qc_spec.md is authoritative

`AIAssessment.canonical.md` says:
- `quality_score ≥ 80` → auto-approve
- `quality_score 60–79` → human review queue
- `quality_score < 60` → auto-reject
- `ai_confidence < 70` → human review regardless of score

`docs/SCHEMA.md` and `docs/ARCHITECTURE.md` use IMPORT_* threshold names. These thresholds are the canonical values; confirm against `compendium_enrichment_qc_spec.md §routing` before wiring the arbiter.

---

## Summary of proposed SCHEMA.md edits (not yet applied)

1. Remove `editorial_description_long` as a universal Resource field; replace with `summary` (AIAssessment) and `editorial_note` (Resource.editorial).
2. Move `editorial_badges` to a split: `proposed_badges` on AIAssessment + `editorial_badges` on Resource.editorial.
3. Replace `provenance` object with distributed fields across AIAssessment and Resource.editorial.
4. Extend `editorial_status` enum to include `archived` and `deprecated`.
5. Move `requires_human_review` from Resource to AIAssessment.
6. Add `ebm_level` footnote to quality_dimensions.
7. Add AIAssessment fields section (ai_confidence, summary, proposed_badges, thesis_stage_signals, strengths, limitations, trainee_suitability_score, pipeline_run_id).
8. Add `field_provenance` and `resource_subtype_code` to Resource universal fields.

**`editorial_description_plain` is preserved unchanged.**
