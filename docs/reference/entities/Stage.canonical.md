# Stage — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: cothesis_main_collected/cothesis_thesis_stages.json (canonical), entity_Stage.md
VERSION: v1.1.0 — phase/stage codes renamed to two-letter prefixes (OQ-002 resolution, migration 08)

## Purpose
Stage represents one of the 25 steps in the THESIS research framework, grouped into 6 phases.
Canonical stage IDs follow the pattern STG-{PHASE}-{NN} (e.g. STG-TH-01, STG-HI-02, STG-ST-03).
Stages are the "universal constant" — they never change based on research type. Blueprints and
Research Models configure activation of stages but cannot create new ones.

## ERD Note
Stage is schema-defined in cothesis_thesis_stages.json as a first-class entity but is NOT
in the 32-entity application ERD (per entities__Blueprint.md: "Stages live in the THESIS framework
spec"). Stage is admitted to the unified schema as a THESIS Framework entity, above the application
layer. See entity_Stage.md §4 for full provenance.

## Source-of-Truth Fields
| Field | Type | Required | Notes |
|---|---|---|---|
| code | string | yes | PK in STG-{PHASE}-{NN} format (e.g. STG-TH-01). Note: JSON also carries a shorter `code` field (e.g. TH-01) — the full stage_id (STG-TH-01) is treated as PK here per P4. Immutable once in production. |
| phase_code | string | yes | FK → Phase.code (e.g. TH, HI, EV, ST, IN, SH) |
| name | string | yes | Stage name |
| description | string | null | What the trainee does at this stage |
| purpose | string | null | Why this stage exists |
| sequence | integer | yes | Position within the phase (1-based, alias: sequence_in_phase) |
| global_sequence | integer | yes | Position across all 25 stages (1-25) |
| stage_type | string | yes | Always "CORE" for canonical stages |
| is_universal | boolean | yes | Always true for the 25 core stages |
| typical_duration | object | null | { min, typical, max, unit } — unit is always "weeks" |
| primary_deliverables | string[] | yes | Main outputs of the stage |
| secondary_deliverables | string[] | null | Optional outputs |
| success_criteria | string[] | yes | How to know the stage is complete |
| common_blockers | string[] | yes | What typically delays this stage |
| default_activation | enum | yes | `required` \| `optional` \| `skip`. Default that new blueprints inherit for this stage unless explicitly overriding. See Activation Resolution Rule below. |
| is_active | boolean | yes | Runtime activation state |

## Page Mixin Fields
NOT ATTACHED — Stages are not surfaced as standalone Compendium pages.

## Derived Fields
| Field | Derived From | Derivation Rule |
|---|---|---|
| completion_percentage | global_sequence | global_sequence / 25 × 100 |

## Relationships
| Relation | Direction | Target | FK Field |
|---|---|---|---|
| phase_code | many→one | Phase | phase_code |
| code | one→many | Project | current_stage_code (via FK) |
| code | one→many | Blueprint | stage_activation[] (pathway_adjustments.stage_activation keys) |
| code | one→many | LoopConstruct | participating_stage_codes[] |

## Activation Resolution Rule

> Every Blueprint must declare an activation value (`required` / `optional` / `skip`) for every canonical Stage. If a Blueprint omits a Stage from its `stage_activation` block, the Stage's `default_activation` value applies. Blueprints SHOULD explicitly declare all 25 stages for clarity, but the default-inheritance mechanism prevents drift when new stages are added to the canon.

No `universal: true` flag — this was rejected per OQ-002 resolution. The `default_activation` field on Stage serves the same role without creating a special case in Blueprint validation logic.

## Integrity Notes
- P5 bidirectional: Stage→Phase FK (phase_code) is present. Phase adds reciprocal stage_codes[] per Phase.canonical.md.
- Blueprint FK re-pointing to canonical STG-XX-NN codes is complete as of migration 08. Blueprint canonical files are in `_merge/blueprints/`.

---

## Seed Data — All 25 Canonical Stages

| code | phase | name | global_sequence | default_activation |
|---|---|---|---|---|
| STG-TH-01 | TH | Topic Identification & Scoping | 1 | required |
| STG-TH-02 | TH | Question/Aim Formulation | 2 | required |
| STG-TH-03 | TH | Theoretical Framing | 3 | required |
| STG-TH-04 | TH | Feasibility Assessment | 4 | required |
| STG-HI-01 | HI | Search Strategy Development | 5 | required |
| STG-HI-02 | HI | Evidence Gathering | 6 | required |
| STG-HI-03 | HI | Quality Assessment | 7 | optional |
| STG-HI-04 | HI | Synthesis & Positioning | 8 | required |
| STG-EV-01 | EV | Study Design Specification | 9 | required |
| STG-EV-02 | EV | Construct Operationalization | 10 | required |
| STG-EV-03 | EV | Sample/Selection Strategy | 11 | required |
| STG-EV-04 | EV | Data Acquisition Planning | 12 | required |
| STG-EV-05 | EV | Governance & Registration | 13 | required |
| STG-ST-01 | ST | Pilot & Calibration | 14 | optional |
| STG-ST-02 | ST | Data Acquisition Execution | 15 | required |
| STG-ST-03 | ST | Quality Assurance | 16 | required |
| STG-ST-04 | ST | Data Management | 17 | required |
| STG-IN-01 | IN | Analysis Preparation | 18 | required |
| STG-IN-02 | IN | Primary Analysis | 19 | required |
| STG-IN-03 | IN | Results Interpretation | 20 | required |
| STG-IN-04 | IN | Supplementary Analyses | 21 | optional |
| STG-SH-01 | SH | Output Drafting | 22 | required |
| STG-SH-02 | SH | Refinement & Review | 23 | required |
| STG-SH-03 | SH | Dissemination Planning | 24 | required |
| STG-SH-04 | SH | Completion & Follow-up | 25 | required |
