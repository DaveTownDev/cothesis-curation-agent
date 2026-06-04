# FoundationSkill — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
VERSION: unified-schema v1.5.0 (Compendium alignment — FS-NN code format formalised; OQ-VALIDATION-01 resolution)
SOURCE: Merged from Compendium project (compendium_complete.json, 15 production-ready skills) + Core project (Schema 2 chat Batch 10, 3 May 2026)
COMPENDIUM_URL: /library/foundation-skills/{slug}

## Purpose

A FoundationSkill is a cross-cutting research competency that applies across multiple methodologies. Foundation Skills are prerequisite skills trainees need to execute methodology-specific work — finding literature, synthesising findings, critically appraising evidence, navigating ethics, statistical literacy, academic writing, etc. They are NOT methodologies themselves (you don't "do a literature searching project"); they are reusable competencies that methodologies depend on.

Each Foundation Skill drives a Compendium page, can be assessed in-platform, and routes the user to relevant Teaching & Learning modules. 16 canonical Foundation Skills at v1.0; the list may grow in Phase 1 expansion.

Cross-profession generalisable — Foundation Skills apply to medical, legal, engineering, education, and any other professional research context.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. Format: `^FS-[0-9]{2}$` (e.g. `FS-09`). Zero-padded. Immutable once published. The Compendium site uses these codes as PRIMARY KEY identifiers in PostgreSQL and Neo4j; the Convex clone inherits them. |
| `name` | string | yes | — | Display name. Title Case (e.g. "Literature Searching", "Statistical Literacy"). Used as Compendium page title. |
| `short_name` | string \| null | no | — | Compact display name. Often 1-2 words (e.g. "Stats", "Lit Search"). For chip/tile/horizontal-scroll displays. |
| `description` | string | yes | — | Rich 100-250 word description of what the skill encompasses, why it matters for trainees, at what stages it applies. Drives Compendium content. |
| `category_code` | string | yes | MethodCategory.code | Always `FS`. Synthetic MethodCategory for Compendium navigation. See OQ-METHCAT-01. |
| `prerequisite_skill_codes` | string[] \| null | no | FoundationSkill.code | Self-referential DAG. Skills that must be developed before this one (e.g. FS-03 prerequisites FS-02). Uses FS-NN codes. |
| `related_skill_codes` | string[] \| null | no | FoundationSkill.code | Self-referential. Skills commonly co-occurring or complementary, but not prerequisite. |
| `thesis_stage_codes` | string[] \| null | no | Stage.code | Which canonical THESIS stages activate this skill. Some skills (project_management, supervision) span all stages. |
| `methodology_codes` | string[] \| null | no | Methodology.code | M:N reciprocal with Methodology.related_foundation_skill_codes[]. Per P5, validation enforced by fs_methodology_bidirectional.py — Methodology side (related_foundation_skill_codes[]) is the source of truth. **Note:** Prompt spec Section 3 named this field `related_methodology_codes`; aligned to `methodology_codes` to match Methodology.canonical.md cross-reference and fs_methodology_bidirectional.py R1 check. |
| `software_commonly_used` | string[] \| null | no | — | Free-text list of tools/software relevant to this skill (e.g. for statistics: ["SPSS", "R", "JASP", "Stata", "jamovi"]). |
| `difficulty_rating` | integer \| null | no | — | 1-5 scale; trainee-perceived difficulty. Higher = harder for novices. |
| `average_acquisition_time_hours` | integer \| null | no | — | Empirical estimate of hours to reach "developing" competency. Drives onboarding planning. |
| `reform_in_progress` | boolean | yes | — | Default false. True when the underlying framework is evolving (e.g. PRISMA 2020 supersedes PRISMA 2009; Reflexive TA framework updating). Signals that content may need revision. |
| `competency_framework_mappings` | jsonb \| null | no | CompetencyFramework.code (via junction) | Maps this skill to external competency frameworks (CanMEDS, ACGME, GMC GPC, etc.). Structure: `[{framework_code: "CANMEDS", criterion_code: "SCHOLAR-3.0"}, ...]`. |
| `featured_in_carousel` | boolean | yes | — | Default false. True for skills surfaced on Compendium homepage carousel. |
| `is_active` | boolean | yes | — | Default true. Soft-deactivate without removal. |
| `phase` | integer | yes | — | Rollout phase (1, 2, 3). |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

Attached — FoundationSkill surfaces on Compendium at `/library/foundation-skills/{slug}`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `slug` | string | yes | URL slug (e.g. "literature-searching") |
| `page_title` | string | yes | SEO page title |
| `meta_description` | string \| null | no | SEO meta |
| `short_description` | string \| null | no | Card/snippet description (40-80 chars) |
| `seo_keywords` | string[] \| null | no | Primary and secondary SEO terms |
| `icon` | string \| null | no | Icon identifier (Lucide or equivalent) |
| `has_page` | boolean | yes | Default true. Whether to publish a Compendium page. |
| `is_active` | boolean | yes | Page-level activity (separate from entity-level is_active) |
| `phase` | integer | yes | Page rollout phase |

---

## Derived Fields

| Field | Derived From | Rule |
|---|---|---|
| `is_currently_active` | is_active, deleted_at | True when is_active AND deleted_at IS NULL |
| `difficulty_label` | difficulty_rating | 1→"easy", 2→"approachable", 3→"moderate", 4→"challenging", 5→"hard" |
| `usage_count` | methodology_codes (via query) | Number of Methodologies referencing this skill (read at query time from Methodology.related_foundation_skill_codes[]) |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| category_code | many→one | MethodCategory | category_code | Synthetic — always 'FS'. See OQ-METHCAT-01. |
| prerequisite_skill_codes[] | many→many (self-ref) | FoundationSkill | prerequisite_skill_codes | DAG — skill dependency order |
| related_skill_codes[] | many→many (self-ref) | FoundationSkill | related_skill_codes | Non-DAG — complementary skills |
| thesis_stage_codes[] | many→many | Stage | thesis_stage_codes | THESIS stages where this skill is activated |
| methodology_codes[] | many→many | Methodology | (reciprocal: Methodology.related_foundation_skill_codes[]) | Source of truth on Methodology side per P5. Bidirectional integrity validated by fs_methodology_bidirectional.py. |
| code | many→many | Resource | (reciprocal: Resource.skill_codes[]) | Source of truth on Resource side |
| competency_framework_mappings | many→many (junction) | CompetencyFramework | competency_framework_mappings | Via jsonb junction structure |

---

## Bidirectional Integrity

| Relationship | Rule | Validator |
|---|---|---|
| FoundationSkill ↔ Methodology | Methodology.related_foundation_skill_codes[] → FoundationSkill.code; FoundationSkill.methodology_codes[] → Methodology.code | `_merge/validation/fs_methodology_bidirectional.py` |

---

## Notes

- FoundationSkill is **cross-profession generalisable** by design. Names use universal terminology, not psychiatry/medicine-specific.
- The 16 canonical skills are the v1.0 baseline. Phase 1 expansion may add: Research Question Formulation, Reference Management, Research Integrity and Authorship, Reflexivity and Positionality (4 candidates from Core project).
- `literature_review` from the original Compendium taxonomy has been split into FS-02 (Literature Searching) and FS-03 (Literature Synthesis). The two-step framing reflects the real research workflow.
- FS-05 (Research Ethics) is the **cross-cutting skill** (how to navigate ethics across jurisdictions). Jurisdictional ethics review bodies (HREC, IRB, REC, etc.) live on a separate `EthicsReviewType` entity — Tier 2 (app-only). OQ-ETHICS-01 resolved: EthicsReviewType is CoThesis app-only, not Compendium scope.
- Codes are immutable. Once published in Compendium, FS-NN codes never reorder.
- **Field name note:** The `methodology_codes` field name aligns with Methodology.canonical.md's documented cross-reference (`FoundationSkill.methodology_codes[]`) and the fs_methodology_bidirectional.py R1 check. The authoring prompt's Section 3 spec used `related_methodology_codes`; this was corrected to `methodology_codes` during entity authoring to maintain internal schema consistency.
- **MethodCategory:** The `category_code: 'FS'` references a synthetic MethodCategory entry. No MethodCategory.canonical.md exists in `_merge/entities/` — see OQ-METHCAT-01.
