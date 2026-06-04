# Entity: LoopIteration

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (satellite table for LoopConstruct — tracks each actual iteration pass within a Project)
VERSION: v1.0.0

---

## Purpose

LoopIteration represents one execution pass of a LoopConstruct within a specific Project.
Where LoopConstruct is the *template* (e.g. "Delphi Round"), LoopIteration is the *instance*
(e.g. "Project XYZ — Delphi Round 2").

Each time a project repeats a loop, a new LoopIteration record is created. This gives:
- A timestamped history of all iterations within a project
- Per-iteration status tracking (in_progress, complete, abandoned)
- Storage for iteration-specific data (e.g. response rate for a Delphi round, PDSA change tested)
- A link from `Project.current_loop_iteration_id` to the active iteration

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | uuid | yes | Surrogate PK. |
| `project_id` | uuid | yes | FK → Project.id |
| `loop_construct_code` | string | yes | FK → LoopConstruct.code |
| `iteration_number` | integer | yes | 1-based sequence number within the project+loop pair. e.g. Round 1, Round 2. |
| `status` | enum | yes | `planned` \| `in_progress` \| `complete` \| `abandoned` |
| `started_at` | timestamp | null | When this iteration began |
| `completed_at` | timestamp | null | When this iteration was marked complete or abandoned |
| `summary` | string | null | Optional free-text notes on this iteration (e.g. response rate, key findings, change tested) |
| `outcome_data` | jsonb | null | Structured iteration-specific outcome fields. Shape varies by LoopConstruct type. e.g. `{ response_rate: 0.82, consensus_items_achieved: 14, total_items: 20 }` for Delphi; `{ change_tested: "...", outcome: "..." }` for PDSA. |

---

## Page Mixin Fields

NOT ATTACHED — LoopIteration records are operational data, not Compendium content.

---

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `is_current` | Project.current_loop_iteration_id | True if this record's id matches Project.current_loop_iteration_id |

---

## Relationships

| Relation | Direction | Target | FK Field |
|---|---|---|---|
| LoopIteration.project_id | many→one | Project | FK |
| LoopIteration.loop_construct_code | many→one | LoopConstruct | FK |
| LoopIteration.id | ←one | Project | Project.current_loop_iteration_id (nullable) |

---

## Integrity Notes

- Composite uniqueness: `(project_id, loop_construct_code, iteration_number)` must be unique.
- `iteration_number` is auto-incremented per `(project_id, loop_construct_code)` pair — not global.
- `completed_at` must be set when `status` transitions to `complete` or `abandoned`.
- `outcome_data` shape is LoopConstruct-specific; validated at application layer, not DB constraint.
