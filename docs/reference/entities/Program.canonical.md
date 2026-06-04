# Program — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Stub authored from referencing entities (OQ-012 session); full field set authored OQ-PROG-01 session
NOTE: Private operational data — no Compendium page.
VERSION: 1.0.0

---

## Purpose

Program represents a formal training program within which a Trainee undertakes research. A Program is offered by a Training Organisation (Organisation with types[] including `training_provider`) and defines the research framework that trainees within it must follow.

Examples: RANZCP Advanced Training Program; RACP Basic Physician Training Research Project; ANZCA Fellowship Training Program; University of Melbourne MD Research Component.

A `Project.program_code` (nullable FK) links a project to the program under which it is being completed. This affects:
- Which research requirements apply (has_research_requirement, research_requirement_type, word_count_target, etc.)
- Which methodology constraints apply (approved_methodology_codes[])
- Which ethics requirements apply (ethics_requirement_codes[])
- Which assessment criteria apply (assessment_criterion_codes[])
- Which format requirements apply (format_requirement_codes[])
- Which learning objectives apply (learning_objective_codes[])

**OQ-012 resolution:** `stage_axis` is a required field with no default value. Programs must explicitly declare whether their stage axis is `professional`, `academic`, or `both`. All programs must declare this explicitly during Program record creation. `both` covers combined clinical-academic programs (e.g. MD/PhD, clinician-researcher tracks).

**Dual-branch pattern (principles_and_decisions.md, Conflict 10 / P1):** Program carries `stage_axis` so the presentation layer knows whether to surface professional stage labels, academic stage labels, or both. This is the canonical mechanism for the dual-branch career stage model.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT pattern. e.g. RANZCP-ATP, RACP-BPT, ANZCA-FTP, UOM-MD-RESEARCH. Immutable once in production. |
| `name` | string | yes | — | Full program name |
| `short_name` | string \| null | no | — | Abbreviated display name |
| `program_type` | enum | yes | — | `fellowship \| certificate \| diploma \| degree \| coursework_component \| other`. Categorises the formal credential type. |
| `domain_code` | string | yes | Domain.code | The domain this program operates in (e.g. HEALTH, LAW). Denormalised from organisation for query efficiency. |
| `organisation_code` | string | yes | Organisation.code | The training provider offering this program. Organisation must have types[] including `training_provider`. |
| `stage_axis` | enum | yes | — | `professional \| academic \| both`. **Required — no default.** Determines which stage enum applies: ProfessionalStage, AcademicStage, or both. All programs must declare this explicitly. (OQ-012 resolved.) |
| `professional_discipline_codes` | string[] \| null | no | ProfessionalDiscipline.code | Which professional disciplines this program targets. Null for purely academic programs. |
| `academic_field_codes` | string[] \| null | no | AcademicField.code | Which academic research fields this program targets. Null for purely professional programs. |
| `description` | string \| null | no | — | Program description |
| `has_research_requirement` | boolean | yes | — | Whether this program requires a formal research component. Default false. |
| `research_requirement_type` | enum \| null | no | — | `thesis \| project \| dissertation \| case_series \| audit \| portfolio \| other`. Null when has_research_requirement is false. |
| `minimum_duration_months` | integer \| null | no | — | Minimum months the research component must span. Null = not prescribed. |
| `word_count_target` | integer \| null | no | — | Target word count for written research output. Null = not applicable. |
| `deliverable_types` | string[] \| null | no | — | Expected output types (e.g. ["written_report", "oral_presentation", "poster"]). Editorial; not FK-normalised. |
| `approved_methodology_codes` | string[] \| null | no | Methodology.code | Methodologies explicitly approved for use in this program. Null = unrestricted. |
| `research_requirement_notes` | string \| null | no | — | Free-text notes on research requirements, e.g. college-specific guidance. |
| `has_formal_examination` | boolean | yes | — | Whether the program has a formal examination component. Default false. |
| `examination_format_notes` | string \| null | no | — | Free-text notes on examination structure (e.g. "written MCQ + clinical viva"). |
| `ethics_review_required` | boolean | yes | — | Whether research conducted under this program requires formal ethics review. Default true for clinical programs. |
| `assessment_criterion_codes` | string[] \| null | no | AssessmentCriterion.code | Assessment criteria that apply to research projects in this program. Null = no program-level criteria. Authored per OQ-008-deferred promotions (Task D). |
| `format_requirement_codes` | string[] \| null | no | FormatRequirement.code | Format requirements for research outputs in this program. Null = no program-level format requirements. Authored per OQ-008-deferred promotions (Task D). |
| `ethics_requirement_codes` | string[] \| null | no | EthicsRequirement.code | Ethics requirements applicable to this program. Null = no program-level ethics requirements. Authored per OQ-008-deferred promotions (Task D). |
| `learning_objective_codes` | string[] \| null | no | LearningObjective.code | Learning objectives associated with this program. Null = no program-level objectives. Authored per OQ-008-deferred promotions (Task D). |
| `stage_progression` | jsonb \| null | no | — | KEEP_EMBEDDED. Program-specific stage activation overrides as a map `{ stage_code: activation }` where activation ∈ { required \| optional \| skip }. When null, the standard Blueprint activation applies. Example: `{"STG-TH-01": "required", "STG-SH-04": "skip"}`. |
| `is_active` | boolean | yes | — | Default true. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private operational data.

---

## Derived Fields

None.

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| `organisation_code` | many→one | Organisation | organisation_code | Required; Organisation must be training_provider |
| `domain_code` | many→one | Domain | domain_code | Required |
| `professional_discipline_codes[]` | many→many | ProfessionalDiscipline | professional_discipline_codes | Nullable |
| `academic_field_codes[]` | many→many | AcademicField | academic_field_codes | Nullable |
| `approved_methodology_codes[]` | many→many | Methodology | approved_methodology_codes | Nullable; unrestricted when null |
| `assessment_criterion_codes[]` | many→many | AssessmentCriterion | assessment_criterion_codes | Nullable; resolved when Task D complete |
| `format_requirement_codes[]` | many→many | FormatRequirement | format_requirement_codes | Nullable; resolved when Task D complete |
| `ethics_requirement_codes[]` | many→many | EthicsRequirement | ethics_requirement_codes | Nullable; resolved when Task D complete |
| `learning_objective_codes[]` | many→many | LearningObjective | learning_objective_codes | Nullable; resolved when Task D complete |
| `code` | one→many | Project | project_code | Projects running under this program |
| `code` | one→many | SupervisionRelationship | program_code | Supervision relationships scoped to this program |

---

## Enum Reference

### `program_type`
| Value | Description |
|---|---|
| `fellowship` | Postgraduate fellowship (e.g. FRANZCP, FRACP, FANZCA) |
| `certificate` | Certificate-level training program |
| `diploma` | Diploma-level program |
| `degree` | University degree with research component (e.g. MD, PhD, Masters) |
| `coursework_component` | Research requirement embedded in broader coursework program |
| `other` | Not categorised above |

### `stage_axis`
| Value | Description |
|---|---|
| `professional` | Stage axis uses ProfessionalStage enum (specialty training programs) |
| `academic` | Stage axis uses AcademicStage enum (research degree programs) |
| `both` | Stage axis uses both ProfessionalStage and AcademicStage (combined clinical-academic programs, e.g. MD/PhD, clinician-researcher tracks) |

### `research_requirement_type`
| Value | Description |
|---|---|
| `thesis` | Full thesis (book-length, original research) |
| `project` | Research project (shorter, supervisor-guided) |
| `dissertation` | Dissertation (intermediate form) |
| `case_series` | Clinical case series |
| `audit` | Clinical audit |
| `portfolio` | Portfolio of evidence |
| `other` | Not categorised above |

---

## Notes

- **stage_progression jsonb:** KEEP_EMBEDDED per OQ-008 — stage overrides are private to this program, never cross-referenced independently, and the shape is bounded to { stage_code: activation_enum }. Not a candidate for promotion.
- **assessment_criterion_codes[], format_requirement_codes[], ethics_requirement_codes[], learning_objective_codes[]:** These FKs point to entities that are authored in the Task D deferred promotion pass. The FK array pattern is correct; FK resolution will be enforced once the target entities exist.
- **Distinction from SupervisionRelationship:** Program defines the *framework*; SupervisionRelationship defines the *personnel assignment* within that framework.
- **Distinction from Blueprint:** Blueprint defines *how* a project is executed (methodology, stages, modules); Program defines *what requirements* the project must meet (word count, ethics, deliverables). A project has one Blueprint and optionally one Program.
