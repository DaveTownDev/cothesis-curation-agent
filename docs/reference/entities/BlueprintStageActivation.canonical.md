# BlueprintStageActivation — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
VERSION: unified-schema v1.0 (OQ-008 nested shape promotion)
SOURCE: Promoted from embedded stage activation tables in _merge/blueprints/*.canonical.md seed files
NOTE: Private operational data — no Compendium page.

---

## Purpose

BlueprintStageActivation is the junction record between a Blueprint and a Stage. It declares how that Blueprint activates (or skips) each of the 25 canonical THESIS stages, and carries a human-readable rationale note for why that activation decision was made.

Each Blueprint has exactly 25 BlueprintStageActivation records — one per canonical stage. The `activation` field governs whether a stage is required, optional, or skipped when a trainee executes that blueprint.

When a blueprint does not declare an activation for a stage, the platform falls back to `Stage.default_activation`. All 3 seed blueprints currently declare all 25 stages explicitly.

**Seed data:** 75 records (25 per blueprint × 3 seed blueprints: EVAL-01-FULL-CYCLE, SYN-01-STANDARD, MEAS-03-CLASSICAL). These were previously embedded as tables in the blueprint seed markdown files.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `id` | uuid | yes | — | Surrogate PK. BlueprintStageActivation records are not referenced by human-readable codes; UUID is sufficient. |
| `blueprint_code` | string | yes | Blueprint.code | The blueprint this activation record belongs to |
| `stage_code` | string | yes | Stage.code | The stage being activated. STG-XX-NN format. |
| `activation` | enum | yes | — | `required \| optional \| skip`. Controls whether the stage is mandatory, optional, or excluded for this blueprint. |
| `blueprint_note` | string | null | — | Free-text rationale for the activation decision. Surfaced in the trainee UI as contextual guidance ("Why is this stage optional for this methodology?"). |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private operational data, never surfaced on Compendium.

---

## Derived Fields

None. The Blueprint entity derives `stage_count_required`, `stage_count_optional`, and `stage_count_skipped` by aggregating over this entity's records.

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| blueprint_code | many→one | Blueprint | blueprint_code | Required |
| stage_code | many→one | Stage | stage_code | Required |

---

## Integrity Notes

- Uniqueness constraint: `(blueprint_code, stage_code)` must be unique — one activation record per stage per blueprint.
- `activation = required` means the stage MUST be completed by the trainee; the platform blocks progression past this stage until the trainee marks it complete.
- `activation = optional` means the stage appears in the trainee's project plan but can be skipped.
- `activation = skip` means the stage is hidden from the trainee's project plan for this blueprint.
- Validated by `_merge/validation/blueprint_reference_integrity.py` (rule group 3).

---

## Open Questions

None.
