# Entity: LoopConstruct

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (inferred from Delphi blueprint iterative round pattern; PDSA re-audit cycle in Audit blueprint; action research and grounded theory methodologies)
VERSION: v1.0.0

---

## Purpose

LoopConstruct represents a named, repeating pattern that can occur within a research project —
either within a single stage (e.g. Delphi rounds all happen within STG-ST-02) or spanning
multiple stages (e.g. a PDSA cycle spans data collection through implementation and back).

LoopConstructs are **platform-defined templates** — they describe the shape of an iterative
pattern and which stages are involved. A Project activates a LoopConstruct when its Blueprint
includes one. Each actual iteration of the loop is tracked as a separate `LoopIteration` record.

LoopConstructs are NOT user-authored. They are canonical records defined per methodology type.
See `_merge/seeds/loop_constructs.seed.md` for the 5 seeded constructs.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPER_SNAKE PK. e.g. `DELPHI_ROUND_LOOP`, `PDSA_CYCLE`. Immutable once in production. |
| `name` | string | yes | Human-readable name. e.g. "Delphi Consensus Round" |
| `description` | string | yes | What this loop represents and when it is activated |
| `loop_scope` | enum | yes | `within_stage` \| `across_stages`. Whether the loop repeats within a single stage or spans multiple stages. |
| `anchor_stage_code` | string | null | FK → Stage.code. For `within_stage` loops: the stage this loop is anchored to. Null for `across_stages` loops. |
| `participating_stage_codes` | string[] | yes | FK[] → Stage.code. All stages that participate in one loop iteration. For within-stage loops, this is the anchor stage (array of one). |
| `termination_condition` | string | yes | Plain-language description of when the loop ends (e.g. "Consensus threshold reached (≥70% agreement) OR stability across rounds") |
| `typical_iterations` | object | null | `{ min: int, typical: int, max: int }` — expected number of iterations. |
| `methodology_codes` | string[] | null | FK[] → Methodology.code. Methodologies that typically activate this loop. Informational. |
| `is_active` | boolean | yes | Whether this loop construct is available on the platform. |

---

## Page Mixin Fields

NOT ATTACHED — LoopConstructs are not surfaced as Compendium pages.

---

## Derived Fields

None.

---

## Relationships

| Relation | Direction | Target | FK Field |
|---|---|---|---|
| LoopConstruct.anchor_stage_code | many→one | Stage | nullable FK |
| LoopConstruct.participating_stage_codes[] | many→many | Stage | one-sided array (no reciprocal on Stage per P5 decision; Stage.canonical.md relationship table documents this) |
| LoopConstruct.code | one→many | LoopIteration | LoopIteration.loop_construct_code |
| LoopConstruct.code | one→many | Blueprint | Blueprint.loop_construct_codes[] |

---

## Integrity Notes

- P4: Code-based PK. `code` is immutable once a LoopIteration references it.
- P5: `participating_stage_codes[]` is one-sided. Stage.canonical.md documents the reverse relationship in its Relationships table (LoopConstruct.participating_stage_codes[]).
- `loop_scope` determines nullability of `anchor_stage_code`: if `within_stage`, anchor_stage_code MUST be set; if `across_stages`, anchor_stage_code MUST be null.

---

## Open Questions

None.
