STATUS: AUTHORED (draft) — needs Dave's review
Tier: 2 (App-only — Convex authors directly)
SOURCE: Inferred from entity_ChecklistCompletion.md
NOTE: ChecklistItem is referenced as a cross-cluster FK (ChecklistCompletion.checklist_id) but is never
defined in the addendum. Gap flagged in entity_ChecklistCompletion.md section 5.

## Purpose
ChecklistItem is a discrete checklist entry, child of a Task or Stage.
ChecklistCompletion records when a specific ChecklistItem is completed by a user.
ChecklistItems may be methodology-specific (e.g. a CONSORT checklist item) or
generic (user-created within a Task or Stage).

## Source-of-Truth Fields
| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| code | string | yes | — | PK |
| task_code | string | null | Task.code | parent task (if attached to a task) |
| stage_code | string | null | Stage.code | parent stage (if attached directly to a stage) |
| methodology_code | string | null | Methodology.code | methodology-specific checklist item |
| title | string | yes | — | checklist item text |
| description | string | null | — | optional detail |
| is_required | boolean | yes | — | default false |
| display_order | integer | null | — | |
| is_active | boolean | yes | — | soft-delete support |
| created_at | datetime | yes | — | |
| updated_at | datetime | yes | — | |

## Constraints
- At least one of task_code or stage_code must be non-null (checklist item must belong to something).
- task_code and stage_code are mutually exclusive (a ChecklistItem is attached to either a Task or a Stage, not both).

## Page Mixin Fields
NOT ATTACHED — ChecklistItems are private user/platform data.

## Relationships
| Field | Direction | Target | Notes |
|---|---|---|---|
| task_code | many-one | Task | nullable |
| stage_code | many-one | Stage | nullable |
| methodology_code | many-one | Methodology | nullable |
| code | one-many | ChecklistCompletion.checklist_item_code | completion records |

## Source Field Mapping (UUID to Code Migration)
| Source field | Source entity | Maps to canonical |
|---|---|---|
| checklist_id (UUID) | ChecklistCompletion.checklist_id | checklist_item_code |
