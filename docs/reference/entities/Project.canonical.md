# Project — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: entity_Project.md (primary) merged with entity_ResearchProject.md (retired)
SUPERSEDES: entity_ResearchProject.md (RETIRED — see migrations/04_research_project_retirement.md)
VERSION: unified-schema v1.0 (merge output)
NOTE: No Compendium page — Projects are private user data

## Purpose
A Project represents a single research project owned by a trainee/user within CoThesis.
Projects are private, never surfaced on the Compendium. The Project entity is the central
node for the user's research journey — tracking methodology, stage, status, supervisors,
and outputs across the 25-stage THESIS framework.

## Source-of-Truth Fields
| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| id | uuid | yes | — | Internal PK (not used in FKs; code-based FKs used externally) |
| code | string | yes | — | Stable human-readable code e.g. "PROJ-2024-0042" |
| title | string | yes | — | Project title |
| user_code | string | yes | User.code | Owner |
| methodology_code | string | yes | Methodology.code | Was: methodology_id (UUID) |
| blueprint_code | string | yes | Blueprint.code | The Blueprint this project executes. Required — every project is created from a blueprint. |
| professional_discipline_code | string | null | ProfessionalDiscipline.code | Was: specialty_id (UUID FK) |
| reporting_standard_code | string | null | ReportingStandard.code | Was: reporting_standard_id |
| program_code | string | null | Program.code | Was: program_id |
| institution_code | string | null | Organisation.code | Was: institution_id |
| status | enum | yes | — | DRAFT \| IN_PROGRESS \| SUBMITTED \| UNDER_REVIEW \| REVISIONS_REQUIRED \| APPROVED \| WITHDRAWN |
| current_phase_code | string | null | Phase.code | Current THESIS phase |
| current_stage_code | string | null | Stage.code | Current THESIS stage (STG-XX-NN format) |
| current_loop_iteration_id | uuid | null | LoopIteration.id | FK to the currently active LoopIteration for this project. Null when no loop is in progress. |
| target_completion_date | date | null | — | User-set target |
| submitted_at | datetime | null | — | Date of formal submission |
| approved_at | datetime | null | — | Date of approval |
| word_count_target | integer | null | — | Target word count |
| word_count_current | integer | null | — | Current word count (computed from ProjectDocuments) |
| ethics_status | enum | null | — | NOT_REQUIRED \| PENDING \| APPROVED \| EXEMPT |
| ethics_reference | string | null | — | Ethics approval reference number |
| visibility | enum | yes | — | PRIVATE \| SHARED_WITH_SUPERVISOR \| SHARED_WITH_PROGRAM |
| tags | string[] | null | — | Free-text tags |
| notes | string | null | — | Internal notes |
| created_at | datetime | yes | — | |
| updated_at | datetime | yes | — | |
| deleted_at | datetime | null | — | Soft delete |

## Page Mixin Fields
NOT ATTACHED — Projects are private user data, never surfaced on Compendium.

## Derived Fields
| Field | Derived From | Derivation Rule |
|---|---|---|
| completion_percentage | current_stage_code + Stage entity | Stage.sequence / 25 × 100 |
| days_to_target | target_completion_date | target_completion_date - today |

## Relationships
| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| user_code | many→one | User | user_code | Owner |
| methodology_code | many→one | Methodology | methodology_code | Required |
| blueprint_code | many→one | Blueprint | blueprint_code | Required |
| professional_discipline_code | many→one | ProfessionalDiscipline | professional_discipline_code | |
| reporting_standard_code | many→one | ReportingStandard | reporting_standard_code | |
| program_code | many→one | Program | program_code | |
| institution_code | many→one | Organisation | institution_code | |
| current_phase_code | many→one | Phase | current_phase_code | |
| current_stage_code | many→one | Stage | current_stage_code | |
| current_loop_iteration_id | many→one | LoopIteration | current_loop_iteration_id | Nullable; set when a loop is active |
| project_code | one→many | SupervisionRelationship | project_code | Supervisors via relationship entity |
| project_code | one→many | ProjectDocument | project_code | |
| project_code | one→many | Milestone | project_code | |
| project_code | one→many | RiskFlag | project_code | |

## Notes
- ResearchProject RETIRED: all ResearchProject data migrated to Project. See migrations/04.
- supervisor_name / supervisor_email REMOVED: supervision handled by SupervisionRelationship entity.
- Code Stability Contract: Requirement.project_code → Project (was Requirement.code → ResearchProject).
- status enum: 7 values locked. Presentation layer may relabel for profession-specific UX.
- Presentation: Project entity NAME stays "Project" across professions. Field label overrides in medical.layer.md (none needed at MVP — flagged for Phase 2).
