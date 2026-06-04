# Module — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored OQ-MODULE-01 session — new entity; referenced by Blueprint.module_codes[]
COMPENDIUM_URL: /library/modules/{slug}
VERSION: 1.0.0

---

## Purpose

Module is a stage-specific content unit attached at activation points within a Blueprint. A Module provides structured guidance, tools, templates, assessments, or reference materials that a Trainee should engage with when they reach a particular stage in their research project.

Examples:
- "Literature Search Fundamentals" — instrument module attached to HI (History & Identification) stage
- "CONSORT Checklist Walkthrough" — checklist module for reporting guideline compliance at write-up stages
- "Systematic Review Protocol Template" — template module for blueprints using SR methodology
- "Data Analysis Walkthrough (Qualitative)" — task module for analysis stages in qualitative blueprints

A Blueprint references Modules via `module_codes[]`. Each Module can appear in multiple Blueprints. Modules are distinct from Resources in that they are platform-authored interactive units, not external content references. Modules may *link* to Resources but are not themselves Resources.

**Relationship to Blueprint:** Blueprint.module_codes[] is a flat reference list. The activation point (which stage a Module fires at) is determined by the Module's own `target_stage_codes[]` and the Blueprint's `BlueprintStageActivation` records. When a Module is attached to a Blueprint, the presentation layer surfaces it to the Trainee when they reach any of the Module's target_stage_codes that are activated in that Blueprint.

**Compendium pages:** Modules surface at `/library/modules/{slug}` for discovery. Most Modules will have `has_page: true` — they are authored platform content with editorial value. `has_page: false` is reserved for internal workflow modules not intended for public browsing.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT pattern. e.g. LIT-SEARCH-FUND, CONSORT-CL, SR-PROTOCOL-TMPL, QDA-WALKTHROUGH. Immutable once in production. |
| `name` | string | yes | — | Full module name |
| `short_name` | string \| null | no | — | Abbreviated display name for stage sidebars |
| `module_type` | enum | yes | — | `instrument \| task \| template \| checklist \| analysis \| runner \| reference \| other`. See Enum Reference below. |
| `description` | string | yes | — | What this module does; what a Trainee will accomplish by engaging with it. 1–3 sentences. |
| `target_stage_codes` | string[] | yes | Stage.code | Stages at which this module is surfaced. Must contain at least one code. |
| `methodology_codes` | string[] \| null | no | Methodology.code | Methodologies for which this module is relevant. Null = methodology-agnostic. |
| `blueprint_codes` | string[] \| null | no | Blueprint.code | Blueprints that include this module. Reciprocal to Blueprint.module_codes[]. One-sided storage here per P5; P5 validation script enforces bidirectional integrity. |
| `estimated_duration_minutes` | integer \| null | no | — | Estimated time to complete the module. Null if open-ended. |
| `ai_assistance_level` | enum | yes | — | `none \| suggestions \| guided \| full_draft`. Describes how much AI assistance is integrated. See Enum Reference below. |
| `requires_supervisor_review` | boolean | yes | — | Whether completing this module requires supervisor sign-off. Default false. |
| `prerequisite_module_codes` | string[] \| null | no | Module.code | Modules that should be completed before this one. Self-referential; nullable. |
| `learning_objective_codes` | string[] \| null | no | LearningObjective.code | Learning objectives addressed by this module. Nullable; resolved when Task D complete. |
| `resource_codes` | string[] \| null | no | Resource.code | Resources embedded or linked within this module. Nullable. |
| `reporting_guideline_codes` | string[] \| null | no | ReportingGuideline.code | Reporting guidelines this module supports compliance with. Nullable. |
| `domain_codes` | string[] \| null | no | Domain.code | Domains this module is relevant for. Null = all domains. |
| `professional_discipline_codes` | string[] \| null | no | ProfessionalDiscipline.code | Disciplines for which this module has specialty-specific content. Null = discipline-agnostic. |
| `version` | string | yes | — | Semantic version (e.g. "1.0.0"). Incremented on content changes. |
| `is_active` | boolean | yes | — | Default true. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

ATTACHED — Module pages surface at /library/modules/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually derived from `code` lowercased + hyphens. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. Default true for authored modules. |
| `is_active` | boolean | Whether the module page is currently live. |
| `phase` | integer | Rollout phase. |

---

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `blueprint_count` | Blueprint.module_codes[] | Count of Blueprints that include this module. |
| `stage_count` | target_stage_codes[] | Length of target_stage_codes[]. |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| `target_stage_codes[]` | many→many | Stage | target_stage_codes | Required; at least one stage |
| `methodology_codes[]` | many→many | Methodology | methodology_codes | Nullable |
| `blueprint_codes[]` | many→many | Blueprint | blueprint_codes | Reciprocal to Blueprint.module_codes[]; P5 integrity enforced by module_integrity.py |
| `prerequisite_module_codes[]` | many→many | Module | prerequisite_module_codes | Self-referential; nullable |
| `learning_objective_codes[]` | many→many | LearningObjective | learning_objective_codes | Nullable; resolved when Task D complete |
| `resource_codes[]` | many→many | Resource | resource_codes | Nullable |
| `reporting_guideline_codes[]` | many→many | ReportingGuideline | reporting_guideline_codes | Nullable |
| `domain_codes[]` | many→many | Domain | domain_codes | Nullable; null = all domains |
| `professional_discipline_codes[]` | many→many | ProfessionalDiscipline | professional_discipline_codes | Nullable |

---

## Enum Reference

### `module_type`
| Value | Description |
|---|---|
| `instrument` | A structured research instrument (survey, tool, scoring guide) |
| `task` | A discrete, actionable task with defined steps (e.g. "Conduct your database search") |
| `template` | A document or output template to be filled in |
| `checklist` | A compliance or completion checklist |
| `analysis` | A guided analysis walkthrough (statistical, qualitative, etc.) |
| `runner` | An interactive runner / wizard that guides through a multi-step process |
| `reference` | A reference guide or quick-access resource bundle |
| `other` | Not categorised above |

### `ai_assistance_level`
| Value | Description |
|---|---|
| `none` | No AI features — pure human-authored content |
| `suggestions` | AI offers optional suggestions or hints |
| `guided` | AI actively guides the user through steps, checking progress |
| `full_draft` | AI can produce a full draft output for human review |

---

## Notes

- **Distinct from Resource:** Resources are external content (journals, courses, tools, videos). Modules are platform-authored interactive units. Modules *link to* Resources; they are not Resources themselves.
- **Distinct from Blueprint:** Blueprints define the research pathway (stage activation, methodology binding). Modules are the content units that sit at those stages.
- **blueprint_codes[] reciprocal storage:** Stored one-sided on Module per P5. Blueprint.module_codes[] is the canonical FK direction (Blueprint references its Modules). Module.blueprint_codes[] is a convenience reciprocal populated from Blueprint records. module_integrity.py enforces that every Blueprint.module_codes[] entry has a corresponding Module.blueprint_codes[] reverse entry.
- **version field:** Content versioning ensures that Blueprint activation records can reference a specific module version for reproducibility. Increment on any substantive content change.
