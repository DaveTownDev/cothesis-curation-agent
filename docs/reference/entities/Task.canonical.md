STATUS: AUTHORED (draft) — needs Dave's review
Tier: 2 (App-only — Convex authors directly)
SOURCE: Inferred from entity_ScheduledWork.md, entity_TaskCompletion.md, entity_ChecklistCompletion.md
NOTE: Task entity is referenced but not directly authored in source files. Both TaskCompletion.task_id
and ScheduledWork.task_id reference this entity as a cross-cluster FK. ChecklistItem (authored separately)
is a child of Task.

## Purpose
Task represents a discrete, actionable item within a Project — either system-generated
(from Blueprint/Stage activation) or user-created. ScheduledWork, TaskCompletion, and
ChecklistCompletion all reference Task as their parent.

## Source-of-Truth Fields
| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| code | string | yes | — | PK e.g. "TASK-2024-0123" UPPERCASE_SHORT |
| project_code | string | yes | Project.code | parent project |
| title | string | yes | — | task title |
| description | string | null | — | optional detail |
| task_type | enum | yes | — | system_generated | user_created | blueprint_step | checklist_item |
| status | enum | yes | — | pending | in_progress | complete | skipped | blocked |
| stage_code | string | null | Stage.code | which THESIS stage this task belongs to |
| phase_code | string | null | Phase.code | which phase this task belongs to |
| due_date | date | null | — | |
| completed_at | datetime | null | — | |
| completed_by_code | string | null | User.code | if different from project owner |
| parent_task_code | string | null | Task.code | self-ref for subtasks |
| source_blueprint_code | string | null | Blueprint.code | if system-generated |
| is_required | boolean | yes | — | default false |
| display_order | integer | null | — | |
| created_at | datetime | yes | — | |
| updated_at | datetime | yes | — | |

## Page Mixin Fields
NOT ATTACHED — Tasks are private user data.

## Derived Fields
| Field | Derivation | Type |
|---|---|---|
| is_overdue | due_date < today AND status NOT IN (complete, skipped) | boolean |

## Relationships
| Field | Direction | Target | Notes |
|---|---|---|---|
| project_code | many-one | Project | |
| stage_code | many-one | Stage | nullable |
| phase_code | many-one | Phase | nullable |
| source_blueprint_code | many-one | Blueprint | nullable |
| parent_task_code | many-one | Task (self) | subtask hierarchy |
| code | one-many | TaskCompletion.task_code | completion records |
| code | one-many | ChecklistCompletion.task_code | checklist completions under this task |
| code | one-many | ScheduledWork.task_code | scheduled work blocks |
| code | one-many | ChecklistItem.task_code | child checklist items |

## Source Field Mapping (UUID to Code Migration)
| Source field | Source entity | Maps to canonical |
|---|---|---|
| task_id (UUID) | TaskCompletion.task_id | task_code |
| task_id (UUID) | ScheduledWork.task_id | task_code |

## Open Questions
- OQ-TASK-01: Should Task have a many-many with Resource (resources useful for this task)?
- OQ-TASK-02: Blueprint step activation -- is Task created 1:1 with Blueprint node, or N per project?
- OQ-TASK-03: task_type=checklist_item -- is this the same as ChecklistItem entity, or a Task with child ChecklistItems? Confirm model.
