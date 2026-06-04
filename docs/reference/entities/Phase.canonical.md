# Phase — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: cothesis_main_collected/cothesis_thesis_stages.json, entity_Phase.md
VERSION: v1.2.0 — slug + display_name fields added (Compendium alignment, canonical v1.5.0)

## Purpose
Phase represents one of the 6 top-level phases of the THESIS research framework.
The six phase initials spell THESIS: Theory (TH), History (HI), Evaluate (EV), Study (ST),
Interpret (IN), Share (SH). Two-letter codes eliminate the S vs S2 namespace collision
present in v1.0.x — see stage_id_reconciliation.md and migration 08.

## ERD Note
Phase is schema-defined in cothesis_thesis_stages.json as a first-class entity but is NOT
in the 32-entity application ERD (per entities__Blueprint.md). Phase is admitted to the unified
schema as a THESIS Framework entity, above the application layer.

## Source-of-Truth Fields
| Field | Type | Required | Notes |
|---|---|---|---|
| code | string | yes | PK — two-letter token: TH, HI, EV, ST, IN, SH. Immutable identifier shared across Compendium and Convex. |
| phase_id | string | yes | Alternate PK form used in JSON: PHASE-TH, PHASE-HI, etc. |
| name | string | yes | Phase name (Theory, History, Evaluate, Study, Interpret, Share) |
| display_name | string | yes | Human-readable label for SEO/display (e.g. "Theory", "History"). Used in Compendium phase navigation and page headings. |
| slug | string | yes | URL-fragment-safe slug for Compendium phase pages (e.g. `theory`, `history`). Unique. Compendium renders at `/library/phases/{slug}`. |
| full_name | string | yes | Full descriptive name (e.g. "Theory: Research Question Development") |
| description | string | null | Phase purpose |
| sequence | integer | yes | Phase order (1-6) |
| typical_duration_percent | integer | yes | Percentage of total project time (TH:10, HI:15, EV:20, ST:25, IN:15, SH:15 — sums to 100) |
| stage_codes | string[] | yes | FK[] → Stage.code — all stages in this phase. Added per P5 as reciprocal of Stage.phase_code. Stored for phase progress queries. |
| colour | string | null | Hex color for UI |
| icon | string | null | Lucide icon name |
| is_active | boolean | yes | |

## Page Mixin Fields
NOT ATTACHED — Phases are not surfaced as standalone Compendium pages.

**Note on slug/display_name:** Although Phase has no standalone page, `slug` and `display_name` are SoT fields used as Compendium navigation identifiers. The Compendium phase pages render at `/library/phases/{slug}`. The two-letter `code` (TH, HI, EV, ST, IN, SH) is the immutable identifier; `slug` is the URL fragment for SEO; `display_name` is the human-readable label.

## Relationships
| Relation | Direction | Target | FK Field |
|---|---|---|---|
| code | one→many | Stage | Stage.phase_code (reciprocal stored as stage_codes[] per P5) |
| code | indirect→ | Blueprint | via Stage.phase_code (Blueprint references stages, not phases directly) |
| code | indirect→ | ResearchModel | via stage activation config |

---

## Seed Data — All 6 Phases

| sequence | code | phase_id | display_name | slug | name | full_name | typical_duration_percent | stage_codes |
|---|---|---|---|---|---|---|---|---|
| 1 | TH | PHASE-TH | Theory | theory | Theory | Theory: Research Question Development | 10 | [STG-TH-01, STG-TH-02, STG-TH-03, STG-TH-04] |
| 2 | HI | PHASE-HI | History | history | History | History: Literature Review & Context | 15 | [STG-HI-01, STG-HI-02, STG-HI-03, STG-HI-04] |
| 3 | EV | PHASE-EV | Evaluate | evaluate | Evaluate | Evaluate: Study Design & Ethics | 20 | [STG-EV-01, STG-EV-02, STG-EV-03, STG-EV-04, STG-EV-05] |
| 4 | ST | PHASE-ST | Study | study | Study | Study: Data Collection & Management | 25 | [STG-ST-01, STG-ST-02, STG-ST-03, STG-ST-04] |
| 5 | IN | PHASE-IN | Interpret | interpret | Interpret | Interpret: Analysis & Results | 15 | [STG-IN-01, STG-IN-02, STG-IN-03, STG-IN-04] |
| 6 | SH | PHASE-SH | Share | share | Share | Share: Writing & Dissemination | 15 | [STG-SH-01, STG-SH-02, STG-SH-03, STG-SH-04] |
