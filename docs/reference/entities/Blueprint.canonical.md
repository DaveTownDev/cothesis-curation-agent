# Blueprint — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
VERSION: unified-schema v1.0 (OQ-BP-01 resolution)
SOURCE: Authored from referencing context (Stage.canonical.md, LoopConstruct.canonical.md, Methodology.canonical.md, _merge/blueprints/*.canonical.md seed files)
COMPENDIUM_URL: /library/blueprints/{slug}

---

## Purpose

A Blueprint is an executable authoring pattern for a specific Methodology — it defines which canonical THESIS stages activate (and how), which Modules attach at each stage, and any LoopConstructs that govern iteration.

The 3 seed blueprints in `_merge/blueprints/` are Blueprint records:
- `audit.canonical.md` → Blueprint code `EVAL-01-FULL-CYCLE`
- `systematic_review.canonical.md` → Blueprint code `SYN-01-STANDARD`
- `delphi.canonical.md` → Blueprint code `MEAS-03-CLASSICAL`

**Methodology** is the methodology *concept* (clinical audit as a research approach). **Blueprint** is the *operational pattern* for executing that concept in CoThesis (which stages, which modules, which loops, in what sequence).

Multiple Blueprints may exist for one Methodology (e.g. a "lite" blueprint for novice trainees and a "full" blueprint for advanced). When `variant_label` is null, that blueprint is the only one for its methodology.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT pattern: `{TYPE}-{NN}-{VARIANT}` (e.g. EVAL-01-FULL-CYCLE, SYN-01-STANDARD, MEAS-03-CLASSICAL). Immutable once in production. |
| `name` | string | yes | — | Display name (e.g. "Clinical Audit — Full Cycle") |
| `description` | string | null | — | 2–4 sentences describing what this blueprint provides |
| `methodology_code` | string | yes | Methodology.code | Which methodology this blueprint operationalises |
| `version` | string | yes | — | Blueprint version (e.g. "1.0.0") |
| `variant_label` | string | null | — | If multiple blueprints exist for one methodology (e.g. "lite", "full", "rapid"). Null when only one blueprint exists for the methodology. |
| `loop_construct_codes` | string[] | null | LoopConstruct.code | Loops governing this blueprint (Delphi rounds, PDSA cycles, theoretical sampling). Empty / null for single-pass blueprints. |
| `module_codes` | string[] | null | Module.code | Modules that attach at activation points across stages. See Module.canonical.md (OQ-MODULE-01 resolved). |
| `target_horizon` | enum | yes | — | `MVP \| PH1 \| PH2 \| PH3` — when this blueprint becomes available in the platform |
| `difficulty_tier` | integer | null | — | 1–5 scale. 1 = most trainee-accessible; 5 = highest expertise/resource requirement. |
| `typical_duration_months` | integer | null | — | Median execution time in months for a trainee project |
| `ethics_complexity` | enum | null | — | `low \| moderate \| high \| variable` — high-level signal for trainee selection |
| `recommended_supervisor_expertise` | string | null | — | Free-text — what kind of supervisor expertise suits this blueprint |
| `reporting_guideline_codes` | string[] | null | ReportingGuideline.code | Reporting guidelines relevant to this blueprint (e.g. PRISMA-2020 for systematic_review) |
| `is_active` | boolean | yes | — | Default true. Soft-deactivate without retiring. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

ATTACHED — Blueprint surfaces on Compendium at `/library/blueprints/{slug}`

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name |
| `has_page` | boolean | Whether Compendium page is generated |
| `is_active` | boolean | Whether blueprint appears in user-facing surfaces |
| `phase` | integer | Rollout phase (1 = launch) |

---

## Derived Fields

| Field | Derived From | Rule |
|---|---|---|
| `stage_count_required` | BlueprintStageActivation records | Count of activations where `activation = required` |
| `stage_count_optional` | BlueprintStageActivation records | Count of activations where `activation = optional` |
| `stage_count_skipped` | BlueprintStageActivation records | Count of activations where `activation = skip` |
| `has_iteration` | loop_construct_codes[] | True when array is non-empty |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| methodology_code | many→one | Methodology | methodology_code | Required |
| loop_construct_codes[] | one→many | LoopConstruct | loop_construct_codes | Loops within this blueprint |
| module_codes[] | many→many | Module | module_codes | Modules attached at stage activation points. See Module.canonical.md (OQ-MODULE-01 resolved). |
| reporting_guideline_codes[] | many→many | ReportingGuideline | reporting_guideline_codes | Guidelines relevant to this blueprint |
| code | one→many | BlueprintStageActivation | blueprint_code | 25 activation records per blueprint (one per canonical stage) |
| code | one→many | Project | blueprint_code | Projects using this blueprint |

---

## Notes

- The 3 seed blueprints (EVAL-01, SYN-01, MEAS-03) currently live as standalone markdown files in `_merge/blueprints/`. These represent Blueprint records — the markdown files are seed data, this canonical file is the schema definition.
- Stage activation records (required/optional/skip per stage) are currently embedded in the seed blueprint markdown files. Per OQ-008 (nested shape promotion), these should be promoted to a `BlueprintStageActivation` entity. See OQ-008 resolution.
- `module_codes[]` — Module entity authored in OQ-MODULE-01 session. See Module.canonical.md for full field set. Modules are stage-specific content units (instruments, tasks, templates, checklists, analysis walkthroughs, runners, reference guides).
