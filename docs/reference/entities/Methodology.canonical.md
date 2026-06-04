# Methodology — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: cothesis_macmini_collected/05_methodology__methodology.md (explicit merge artifact, v1.0)
SUPERSEDES: entity_schemas__Methodology.md, entities__Methodology.md
VERSION: unified-schema v1.1 (merge output)
COMPENDIUM_URL: /library/methodologies/{slug}

---

## Purpose

A Methodology represents a single named research method in the CoThesis registry. The registry contains 166 methodologies at launch: 147 core (across 10 categories: OBS/EXP/QUAL/MIX/SYN/EVAL/IMP/MEAS/MOD/CASE) and 19 extension (PRE/ENG/ENV/IND). Methodology is the central entity of the Compendium — every Requirement references permitted/recommended methodologies, every Blueprint is built on a single Methodology, and FoundationSkills are linked from here.

---

## Code Convention

| Context | Format | Example |
|---|---|---|
| Primary (CoThesis internal) | `{COTHESIS_CATEGORY_CODE}-{NN}` | `OBS-01`, `SYN-04`, `QUAL-11` |
| Legacy (Compendium) | `{COMPENDIUM_CODE}-{NN}` | `RS-01`, `OD-01`, `QM-03` |

The unified schema uses the CoThesis internal code format as canonical. Legacy Compendium codes are preserved in `legacy_compendium_code` for backward-compatibility and stale cross-reference resolution.

Category code mapping (Compendium → CoThesis):

| Compendium Code | CoThesis Code |
|---|---|
| RS | SYN |
| OD | OBS |
| EI | EXP |
| QM | QUAL |
| MV | MIX |
| CS | CASE |
| IM | EVAL |
| PM | IMP |
| MD | MEAS |
| CA | MOD |

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | YES | — | PK. Format: `{COTHESIS_CATEGORY_CODE}-{NN}` (e.g. OBS-01, QUAL-11, SYN-04). CoThesis internal format is canonical. |
| `legacy_compendium_code` | string \| null | no | — | Compendium-era code (e.g. OD-01, RS-04, QM-11). Formerly the primary PK in Compendium. Retained for backward-compat and stale cross-reference resolution. |
| `title` | string | YES | — | Primary human-readable name. Unified adopts Compendium's `title`; Core's `name` field is subsumed. |
| `alternative_names` | string[] | no | — | Other names by which this methodology is known. Source: compendium. |
| `regional_name_variations` | object | no | — | Names used in specific regions or health systems. Contains sub-keys: `au_nz[]`, `uk[]`, `us[]`, `international[]` (Core structured form) and `by_country{}` (Compendium keyed object by Country.code). Both representations retained. |
| `type` | string | YES | — | Constant value: `"methodology"`. |
| `category_code` | string | YES | MethodCategory.cothesis_code | FK → MethodCategory using CoThesis codes (OBS, SYN, QUAL, etc.), not Compendium codes (OD, RS, QM). |
| `category_slug` | string | no | — | Compendium URL slug of the parent category. Compendium-only; retained for page generation. |
| `horizon` | enum | YES | — | Rollout horizon. Values: `MVP` \| `PH1` \| `PH2` \| `PH3`. Primary rollout model; replaces the `phase` integer. |
| `tier` | integer | YES | — | 1 (most common/important) to 3 (specialist). Indicates trainee relevance and CoThesis feature priority. |
| `rollout_stage` | enum | no | — | Values: `live` \| `in_development` \| `planned` \| `deprecated`. |
| `architecture_dependency` | string \| null | no | Methodology.code | Code of another Methodology this entry depends on in the system architecture. |
| `rollout_rationale` | string | no | — | Explanation of horizon/tier placement for editorial and engineering reference. |
| `is_extension` | boolean | no | — | `true` for methodologies in PRE/ENG/ENV/IND extension categories. |
| `description` | string | YES | — | Comprehensive description of the methodology. |
| `unique_characteristics` | string | no | — | What sets this methodology apart from closely related designs. Source: compendium. |
| `primary_distinguisher` | string | YES | — | One-sentence primary distinguishing feature. Also appears nested in `differentiating_characteristics`. |
| `paradigm` | enum | YES | — | Epistemological paradigm. LOCKED values: `post-positivist` \| `interpretivist` \| `constructivist` \| `pragmatist` \| `critical` \| `mixed`. |
| `data_type` | enum | YES | — | Primary data type produced. LOCKED values: `quantitative` \| `qualitative` \| `mixed` \| `secondary` \| `not_applicable`. |
| `evidence_level` | string | no | — | NHMRC or OCEBM evidence level (e.g. I, II, III-1, III-2, IV). |
| `differentiating_characteristics` | object | no | — | Structured contrast with similar methodologies. Contains: `primary_distinguisher` (string), `key_features[]` (string[]), `vs_similar_methods[]` (array of `{compared_to: Methodology.code, difference: string}`). `compared_to` uses CoThesis codes. |
| `included_subtypes` | array | no | — | Array of `{name: string, description: string, when_to_use: string}`. Structured subtype descriptions. Source: core. |
| `variants` | array | no | — | Array of `{name: string, relationship_to_base: string, distinguishing_characteristics: string}`. Structured variant objects. Source: compendium. |
| `when_to_use` | string | no | — | Prose guidance on appropriate use. Source: compendium. |
| `example_research_questions` | string[] | no | — | Realistic example research questions for this methodology. Source: compendium. |
| `start_here` | string[] \| null | no | Resource.code | FK[] → Resource.code. Resources recommended as starting points for trainees before attempting this methodology (e.g. primer articles, introductory courses). OQ-009 resolved: FK target is Resource, not Methodology — "start here" content is editorial resource links, not prerequisite methodologies (those use parent_methodology_code). |
| `trainee_feasibility` | integer | YES | — | 1 (most trainee-accessible) to 5 (highest expertise/resource requirement). |
| `typical_duration_months` | integer | no | — | Typical months from initiation to completion for a trainee project. |
| `key_success_factors` | string[] | no | — | Factors that predict successful completion. Source: core. |
| `common_failure_reasons` | string[] | no | — | Reasons trainees fail or struggle with this methodology. Source: core. |
| `ethics_typical` | string | no | — | Compendium ethics indicator. Retained alongside `default_ethics_requirement` for different granularity. Source: compendium. |
| `default_ethics_requirement` | enum | no | — | LOCKED values: `always` \| `if_human_subjects` \| `usually_exempt` \| `never` \| `varies_by_pathway`. Source: core. |
| `ethics_summary` | string | no | — | Prose ethics guidance for trainees. Source: core. |
| `primary_reporting_standard_codes` | string[] | no | ReportingStandard.code | FK[] → ReportingStandard. Primary standard codes (e.g. `["STROBE"]`, `["PRISMA-2020"]`). |
| `reporting_standards` | array | no | — | Array of `{name: string, url: string}`. Structured reporting standard objects with URLs. Source: compendium. |
| `search_guidance` | object | no | — | Guidance for literature searching using this methodology. Contains: `primary_search_terms[]`, `secondary_search_terms[]`, `exclusion_terms[]`, `recommended_sources[]`, `quality_indicators[]`. Source: core. |
| `regulatory_phase` | string[] | no | — | Phases of regulatory process where this method applies. Values: `preclinical` \| `clinical` \| `post_marketing` \| `health_technology_assessment`. |
| `analytical_options` | string[] | no | — | Analytical approaches applicable to this methodology. Source: core. |
| `configurable_by` | string[] | no | — | Parameters that can be configured in Blueprint definitions. Source: core. |
| `compatible_output_types` | string[] | no | — | Output types compatible with this methodology (e.g. `research_report`, `journal_article`, `thesis`). |
| `ranzcp_pass_rate` | number \| null | no | — | Proportion of RANZCP submissions using this methodology that pass on first attempt. RANZCP-specific; very high data value. Source: core. |
| `ranzcp_pass_rate_history` | array \| null | no | — | Array of `{year: integer, pass_rate: number}`. Year-by-year pass rate history. Source: core. |
| `ranzcp_proposal_share_pct` | number \| null | no | — | Percentage of RANZCP research proposals using this methodology. Source: core. |
| `ranzcp_specific_rules` | string \| null | no | — | RANZCP-specific rules or requirements. Source: core. |
| `related_methodology_codes` | string[] | no | Methodology.code | FK[] → Methodology (self-referential). Related methods. Uses CoThesis codes. Formerly used Compendium codes in source; migrated. |
| `parent_methodology_code` | string \| null | no | Methodology.code | FK → Methodology. Set when this methodology is a specialisation of another. Nullable. |
| `related_foundation_skill_codes` | string[] | no | FoundationSkill.code | FK[] → FoundationSkill. **Renamed from `related_foundation_skills` per P4 code-based FK convention.** Bidirectional: FoundationSkill.methodology_codes[] references back. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK[] → ProfessionalDiscipline. **Migrated from `applicable_disciplines` (free-text) and `specialty_relevance[].specialty_code` per P4 + Conflict 7.** Flat FK array; free-text values converted to ProfessionalDiscipline.code references. See Notes. |
| `key_references` | array | no | — | Array of `{citation: string, url: string \| null, type: string}`. Key references for this methodology. Source: compendium. |
| `software_commonly_used` | string[] | no | — | Software tool codes or names. **TODO: migrate to FK[] → ResearchTool.code when ResearchTool entity is authored.** Uses uppercase codes from Core (e.g. `["SPSS", "STATA", "R"]`). |
| `stage_resources` | object | no | — | Links to CoThesis resources for each THESIS framework stage. Keyed by stage group (`theory`, `history`, `evaluate`, `study`, `interpret`, `share`). Each block contains: `stage_codes[]` (Core THESIS stage codes), `resource_codes[]` (FK[] → TLModule.code or Resource.code), `description` (string). |
| `seo_primary_terms` | string[] | no | — | Primary SEO terms. Source-of-truth editorial field; not derived. Source: compendium. |
| `seo_secondary_terms` | string[] | no | — | Secondary SEO terms. Source-of-truth editorial field; not derived. Source: compendium. |
| `editorial_intro` | string | no | — | Editorial/conversational intro for the Compendium page. Source: compendium. |
| `cothesis_model_id` | string | no | — | CoThesis system model identifier. May differ from `code` in edge cases. Compendium-only; retained for system cross-reference resolution. |
| `implementation_notes` | string | no | — | System implementation notes for CoThesis developers. Source: core. |
| `display_order` | integer | no | — | Ordering within the category page. Source: compendium. |
| `notes` | string | no | — | General audit/editorial notes. |
| `created_at` | datetime | YES | — | Auto-managed. ISO 8601 UTC. |
| `updated_at` | datetime | YES | — | Auto-managed. ISO 8601 UTC. |

### Decisions Applied to Source-of-Truth Fields

- **DROP `phase` (integer)** — `horizon` enum (MVP/PH1/PH2/PH3) + `tier` integer are the rollout model per Task A decision. The `phase` integer (Compendium 1–5) is not stored; mapping: phase 1 → MVP, 2 → PH1, 3 → PH2, 4+ → PH3.
- **KEEP `horizon` enum** — LOCKED values: `MVP` | `PH1` | `PH2` | `PH3`.
- **KEEP `tier` integer** — 1–3 scale.
- **LOCK `paradigm` enum** — `post-positivist` | `interpretivist` | `constructivist` | `pragmatist` | `critical` | `mixed`.
- **LOCK `data_type` enum** — `quantitative` | `qualitative` | `mixed` | `secondary` | `not_applicable`.
- **LOCK `default_ethics_requirement` enum** — `always` | `if_human_subjects` | `usually_exempt` | `never` | `varies_by_pathway`.
- **`start_here` field** — type `string[] | null`. FK_TARGET_TBD — annotated "FK → Resources or Methodologies — Dave to confirm per OQ-009".
- **`related_foundation_skills` → `related_foundation_skill_codes`** — renamed per P4 code-based FK convention. FK[] → FoundationSkill.code.
- **`applicable_disciplines` → `discipline_codes`** — was free-text in source; migrated to code-based FK array per P4 + Conflict 7. FK[] → ProfessionalDiscipline.code.
- **`specialty_relevance[]` array** — source: compendium sub-object. Subsumed into `discipline_codes[]` flat FK array. `specialty_code` values migrated to ProfessionalDiscipline.code; `relevance_note` values archived in migration notes.
- **All UUID FKs → code-based FKs** per P4.

---

## Page Mixin Fields

Attached per P3 — Methodology surfaces on `/library/methodologies/{slug}`.

Refer to `_merge/mixins/PageMixin.md` — all 9 fields apply.

**Source mapping** (from the `compendium` sub-object in source file):

| PageMixin Field | Source Field | Notes |
|---|---|---|
| `slug` | `compendium.slug` | URL slug, stable once published, kebab-case |
| `page_title` | `compendium.page_title` | SEO `<title>` tag |
| `meta_description` | `compendium.meta_description` | ≤160 chars; note: a `meta_description` field also exists at top-level (source: compendium); the `compendium` sub-object value takes precedence for page generation |
| `short_description` | `compendium.short_description` | Card/tile text, 1–2 sentences |
| `seo_keywords` | `compendium.seo_keywords` | Primary search terms for page; distinct from `seo_primary_terms` (editorial, broader) |
| `icon` | `compendium.icon` | Lucide icon name, nullable |
| `has_page` | `compendium.has_page` | Whether Compendium page is generated |
| `is_active` | `is_active` | Already top-level in source; controls user-facing visibility |
| `phase` | `horizon` (mapped) | Rollout phase for page generation purposes (1 = MVP launch) |

---

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| (none currently) | | |

**Note:** `seo_primary_terms` and `seo_secondary_terms` are source-of-truth editorial fields, not derived. They are authored by CoThesis editorial and stored directly on the entity.

---

## Relationships

| Relation | Direction | Target Entity | FK Field | Notes |
|---|---|---|---|---|
| Category | many→one | MethodCategory | `category_code` → MethodCategory.cothesis_code | Every Methodology belongs to exactly one MethodCategory. |
| Related Methodologies | many→many | Methodology (self) | `related_methodology_codes[]` → Methodology.code | Symmetric relationship; not automatically reciprocated — both sides authored. |
| Parent Methodology | many→one | Methodology (self) | `parent_methodology_code` → Methodology.code | Nullable. Set when this is a specialisation or elevated sub-type. |
| Foundation Skills | many→many | FoundationSkill | `related_foundation_skill_codes[]` → FoundationSkill.code | **RECIPROCAL**: FoundationSkill.methodology_codes[] references back. Bidirectional integrity validated. |
| Professional Disciplines | many→many | ProfessionalDiscipline | `discipline_codes[]` → ProfessionalDiscipline.code | Migrated from free-text `applicable_disciplines` + `specialty_relevance[]`. |
| Reporting Standards | many→many | ReportingStandard | `primary_reporting_standard_codes[]` → ReportingStandard.code | Primary standards only; full structured list in `reporting_standards[]` with URLs. |
| Differentiating Comparisons | many→many | Methodology (self) | `differentiating_characteristics.vs_similar_methods[].compared_to` → Methodology.code | Directional contrast pairs; editorial, not auto-reciprocated. |
| Architecture Dependency | many→one | Methodology (self) | `architecture_dependency` → Methodology.code | Nullable. System-level dependency, not a methodological relationship. |
| Start Here | many→many | Resource | `start_here[]` → Resource.code | FK[] → Resource. Editorial primer links. OQ-009 resolved. |

---

## Reciprocals Authored

- **`Methodology.related_foundation_skill_codes[]`** (FK → FoundationSkill.code)
  Bidirectional integrity validated by: `_merge/validation/fs_methodology_bidirectional.py`

- **`Methodology.legacy_compendium_code`** (nullable) — Compendium-side ID for stale-mapping resolution. Used by data pipeline to patch `cothesis_model_id` references in `compendium_complete.json`.

---

## Notes

- **`applicable_disciplines`** was free-text in source (values like `"medicine"`, `"nursing"`, `"allied_health"`, `"public_health"`, `"pharmacy"`); migrated to `discipline_codes[]` (FK → ProfessionalDiscipline.code) per P4 + Conflict 7. Free-text values archived in migration notes for conversion reference.
- **`specialty_relevance[]`** array (source: compendium sub-object with `specialty_code` + `relevance_note`) is subsumed into `discipline_codes[]`. The structured `{specialty_code, relevance_note}` form is not retained as a top-level field; if relevance notes need to be surfaced, they should be added to the ProfessionalDiscipline entity or a join record.
- **RANZCP-specific fields** (`ranzcp_pass_rate`, `ranzcp_pass_rate_history`, `ranzcp_proposal_share_pct`, `ranzcp_specific_rules`) retained in full — high data value. Source: core.
- **`software_commonly_used`** TODO: migrate to FK[] → ResearchTool.code when ResearchTool entity is authored. Currently stores uppercase codes from Core (e.g. `SPSS`, `STATA`, `R`, `SAS`, `PYTHON`).
- **Presentation label**: "Methodology" stays universal across professions. Legal/engineering contexts may prefer "Method" — handle in presentation layers when those professions are onboarded; do not alter the entity name.
- **`phase` field** (Compendium integer 1–5) DROPPED per Task A decision; `horizon` enum is the rollout model. The `phase` integer from the Compendium source is not stored; the integer-to-enum mapping is: 1 → MVP, 2 → PH1, 3 → PH2, 4+ → PH3.
- **`differentiating_characteristics.vs_similar_methods[].compared_to`** uses CoThesis codes in the unified schema. Compendium codes in source data must be migrated via the code mapping table in the Code Convention section.
- **`category_slug`** is retained as a Compendium-only convenience field for page generation; it does not replace or duplicate `category_code`.
- **`cothesis_model_id`** retained for system cross-reference resolution where it differs from `code` in edge cases (known: MV-07 → MEAS-11, MV-08 → MEAS-01-CROSSCULTURAL; see migration 01).
- **`stage_resources` block** uses both Compendium stage names (keys) and Core stage codes (values in `stage_codes[]`). The two representations are complementary; Core stage codes are authoritative for system integration.
