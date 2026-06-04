# LearningObjective — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Promoted from Program-embedded nested shape — OQ-008 deferred promotion, Task D session
NOTE: Private operational data — no Compendium page.
VERSION: 1.0.0

---

## Purpose

LearningObjective is a stated learning outcome that a trainee is expected to demonstrate by completing (or engaging with) a training Program or Module. Learning objectives are authored by program designers and used to align research activities with formal training outcomes.

Examples:
- "Demonstrate ability to formulate a structured, answerable clinical research question"
- "Apply an appropriate quantitative or qualitative methodology to address a research question"
- "Critically appraise published literature relevant to the research area"
- "Produce a written research output that meets the program's format and word count requirements"
- "Present research findings clearly to a non-specialist audience"

Programs reference learning objectives via `learning_objective_codes[]`. Modules may also reference objectives via `learning_objective_codes[]` when a Module contributes to specific objectives.

**Promotion rationale (OQ-008):** Promoted over KEEP_EMBEDDED because:
- Objectives are reused across Programs AND Modules (both reference the same FK array)
- Objectives carry their own versioning and alignment metadata (e.g. mapped to NHMRC competency frameworks)
- Independent FK resolution needed for competency tracking and outcome reporting

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT. e.g. LO-RQ-FORMULATE, LO-METHOD-APPLY, LO-APPRAISE-LIT, LO-WRITE-OUTPUT. Immutable once in production. |
| `name` | string | yes | — | Short name (e.g. "Formulate a Research Question") |
| `statement` | string | yes | — | Full objective statement beginning with an action verb (Bloom's taxonomy preferred). e.g. "Demonstrate ability to formulate a structured, answerable clinical research question using PICO or equivalent frameworks." |
| `bloom_level` | enum \| null | no | — | `remember \| understand \| apply \| analyse \| evaluate \| create`. Bloom's taxonomy cognitive level. Nullable. |
| `objective_category` | enum | yes | — | `research_design \| methodology \| critical_appraisal \| writing \| presentation \| ethics \| data_management \| professional_skills \| other` |
| `competency_framework_code` | string \| null | no | — | External competency framework code (e.g. NHMRC Research Training Competency, CanMEDS Scholar role). Free-text; not FK-normalised. |
| `program_codes` | string[] \| null | no | Program.code | Programs that include this objective. Reciprocal to Program.learning_objective_codes[]. P5 integrity enforced by learning_objective_integrity.py. |
| `module_codes` | string[] \| null | no | Module.code | Modules that address this objective. Reciprocal to Module.learning_objective_codes[]. P5 integrity enforced by learning_objective_integrity.py. |
| `domain_codes` | string[] \| null | no | Domain.code | Domains this objective applies to. Null = all domains. |
| `version` | string | yes | — | Semantic version (e.g. "1.0.0"). |
| `is_active` | boolean | yes | — | Default true. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private operational data.

---

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `program_count` | program_codes[] | Count of Programs referencing this objective. |
| `module_count` | module_codes[] | Count of Modules referencing this objective. |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| `program_codes[]` | many→many | Program | program_codes | Reciprocal to Program.learning_objective_codes[]; P5 enforced |
| `module_codes[]` | many→many | Module | module_codes | Reciprocal to Module.learning_objective_codes[]; P5 enforced |
| `domain_codes[]` | many→many | Domain | domain_codes | Nullable |

---

## Enum Reference

### `bloom_level`
| Value | Description |
|---|---|
| `remember` | Recall facts and basic concepts |
| `understand` | Explain ideas or concepts |
| `apply` | Use information in new situations |
| `analyse` | Draw connections among ideas |
| `evaluate` | Justify a decision or course of action |
| `create` | Produce new or original work |

### `objective_category`
| Value | Description |
|---|---|
| `research_design` | Designing research questions, objectives, hypotheses |
| `methodology` | Applying or selecting research methods |
| `critical_appraisal` | Appraising evidence quality and relevance |
| `writing` | Producing written research outputs |
| `presentation` | Communicating findings orally or visually |
| `ethics` | Understanding and applying ethical principles |
| `data_management` | Collecting, organising, and storing research data |
| `professional_skills` | Time management, collaboration, supervision engagement |
| `other` | Not categorised above |
