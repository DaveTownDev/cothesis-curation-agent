# Entity: DecisionPoint

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — inferred from Part 19 graph edge TRIGGERS: RiskFlag → DecisionPoint)
NOTE: DecisionPoint was referenced by a Part 19 graph edge (TRIGGERS) with no backing FK field on
RiskFlag and no entity definition in the addendum. This file resolves that gap. RiskFlag gains
decision_point_code (see Relationships below).

## Purpose
DecisionPoint is a node in the research workflow where a binary or multi-option decision must be made.
Examples: "Is your sample size sufficient?", "Did ethics approve your protocol?", "Have you completed
your literature review?".

RiskFlags TRIGGER when a DecisionPoint is not resolved favourably. DecisionPoints may be stage-specific
and methodology-specific, forming the adaptive decision layer of the platform.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. e.g. `SAMPLE_SIZE_SUFFICIENT`, `ETHICS_APPROVED`. Immutable once in production. |
| `title` | string | yes | Decision question text, phrased as a question. e.g. "Is your sample size sufficient?" |
| `description` | string | null | Additional context for the decision. 1–3 sentences. |
| `decision_type` | enum | yes | `binary` \| `multi_option` \| `confirmation`. Locked. |
| `options` | array | null | `[{value: string, label: string, triggers_risk: boolean}]`. Present when decision_type = multi_option. |
| `stage_code` | string | null | FK → Stage.code. Which professional stage this decision point occurs at. Null = applies to all stages. |
| `methodology_codes` | string[] | null | FK[] → Methodology.code. Methodologies this decision applies to. Empty = applies to all. |
| `is_required` | boolean | yes | Whether this decision point must be resolved before stage progression. Default false. |
| `is_active` | boolean | yes | Whether this decision point is live in the platform. |

---

## Page Mixin Fields

NOT ATTACHED — DecisionPoints are platform configuration data, not Compendium-facing entities.

---

## Derived Fields

None.

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| DecisionPoint.stage_code | many→one | Stage | nullable FK | |
| DecisionPoint.methodology_codes[] | many→many | Methodology | one-sided array | no reciprocal on Methodology |
| DecisionPoint.code | one→many | RiskFlag | RiskFlag.decision_point_code | risks triggered by this decision point |

### Gap Resolution
Part 19 edge TRIGGERS (RiskFlag → DecisionPoint) had no backing field on RiskFlag.
Resolution: RiskFlag gains `decision_point_code` (string, null, FK → DecisionPoint.code).
This field represents "which decision point (if any) triggered this risk flag".

---

## Open Questions

- OQ-DP-01: Are DecisionPoints authored by the platform team only, or can supervisors/institutions add custom ones? Affects governance model.
- OQ-DP-02: Should options[] be a separate entity (DecisionPointOption) for larger option sets, or is an embedded array sufficient? Confirm with Dave.
