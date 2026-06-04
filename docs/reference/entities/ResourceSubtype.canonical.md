STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: cothesis_macmini_collected/entity_schemas__ResourceType.md + cothesis_macmini_collected/cothesis_resource_type_taxonomy_v2.md
PRODUCED_BY: Task B (schema merge)
DATE: 2026-05-15

---

# Entity: ResourceSubtype

## Purpose

ResourceSubtype is a child of ResourceType providing finer-grained classification. 61 subtypes across 14 types at v2.1 (note: `book_chapter` has 0 subtypes — it is the structural exception).

ResourceSubtype entries appear as secondary filters or facets once a top-level ResourceType is selected. They drive agent-level discovery specificity and allow users to narrow from "Software & Tools" to "Statistical Software" or from "Journal Articles" to "Seminal Methodology Paper."

`code` is a stable, immutable, globally-unique lowercase_snake_case primary key across all subtypes — not just within a parent type. This enables single-step `Resource.resource_subtype_code` lookup without needing to know the parent type first.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string | yes | PK. Stable, immutable, globally unique across all subtypes. Lowercase snake_case. e.g. `statistical_software`, `seminal_paper`, `primary_guideline`. FK target for Resource.resource_subtype_code. Pattern: `^[a-z][a-z0-9_]{1,49}$`. |
| `type_code` | string | yes | FK → ResourceType.code. Parent type. Required, non-null. DB FK constraint: must exist in ResourceType.code. |
| `name` | string | yes | Display label (Title Case) for filter chips, tiles, breadcrumbs. e.g. "Statistical Software", "Seminal Methodology Paper". |
| `name_singular` | string \| null | no | Singular form for detail pages and breadcrumbs. maxLength: 40. |
| `description` | string \| null | no | Editorial 1–3 sentence description. Lead paragraph on the subtype page / tooltip when the subtype is referenced. |
| `long_description` | string \| null | no | Optional extended description for the subtype page body. |
| `agent_discovery_codes` | string[] | no | Agent-discovery type codes (from the 46-type list) mapping to this subtype. Most 1:1; some merge multiple agent codes into one subtype. |
| `common_resource_examples` | string[] | no | Editorial list of well-known example resources of this subtype. 4–10 entries. |
| `default_thesis_stage_relevance` | enum[] | no | Default THESIS-stage relevance. Values: `theory`, `history`, `evaluate`, `study`, `interpret`, `share`. Editorial baseline; individual Resources can override. |
| `primary_methodology_associations` | string[] | no | → Methodology.code[]. Methodologies most associated with this subtype. Soft tagging; not strict membership. Proposed promotion to a SubtypeMethodologyAffinity junction. |
| `is_methodology_specific` | boolean | no | Whether this subtype is tightly bound to 1–2 methodologies (e.g. `seminal_paper`) vs methodology-agnostic (e.g. `reference_manager`). Drives page layout: methodology-specific subtypes get methodology-grouped result lists; agnostic subtypes get flat lists with methodology as a side-filter. |
| `display_order` | integer | yes | Sort order within the parent type (per-parent-type ordering, not global). minimum: 0, maximum: 9999. |
| `is_active` | boolean | yes | Whether the subtype appears in user-facing filters/tiles. Default: true. |
| `phase` | integer | yes | Rollout phase 1–5. 1 = launch (all 61 ship). minimum: 1, maximum: 5. Default: 1. |
| `estimated_resource_count_target` | integer \| null | no | Editorial-planning target resource count by end of Phase 2. Drives content roadmap visibility. |
| `notes` | string \| null | no | Internal-only editorial notes. Never user-facing. |

---

## Page Mixin Fields

ResourceSubtype does NOT get its own Compendium page (pages belong to ResourceType). No Page Mixin attached.

Note: Subtype-level browse is handled as a filtered view within the parent ResourceType page (e.g. `/library/resources/software?subtype=statistical_software`), not as a standalone page at its own slug. If a future phase introduces subtype-level pages, attach the standard Page Mixin (slug, page_title, meta_description, short_description, seo_keywords[], icon, has_page, is_active, phase) at that time.

---

## Derived Fields

(none)

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|----------|-----------|--------|----------|-------|
| type_code | many→one | ResourceType | type_code | Required. Every subtype belongs to exactly one ResourceType. DB FK constraint. Seed order: ResourceType (14) first, then ResourceSubtype (61). |
| code | one→many | Resource | resource_subtype_code | Resources classified into subtypes. Two-step validation required: (a) resource_subtype_code must exist in ResourceSubtype.code; (b) the subtype's type_code must match Resource.resource_type_code. |
| primary_methodology_associations[] | many→many (soft) | Methodology | Methodology.code | Soft tagging via denormalised array. Proposed promotion to SubtypeMethodologyAffinity junction for per-mapping notes. |

---

## Subtype Roster (v2.1 — 61 total)

| type_code | code | name |
|-----------|------|------|
| `software` | `statistical_software` | Statistical Software |
| `software` | `qualitative_software` | Qualitative Analysis Software |
| `software` | `reference_manager` | Reference Manager |
| `software` | `systematic_review_tool` | Systematic Review Tool |
| `software` | `data_collection` | Data Collection Platform |
| `software` | `literature_discovery` | Literature Discovery Tool |
| `software` | `writing_tool` | Writing & Collaboration Tool |
| `software` | `project_management` | Project Management Tool |
| `software` | `figure_tool` | Data Visualisation / Figure Tool |
| `software` | `calculator` | Sample Size / Power Calculator |
| `software` | `coding_resource` | Clinical Coding Tool |
| `software` | `ai_research_tool` | AI Research Assistant |
| `software` | `registration_platform` | Protocol Registration Platform |
| `software` | `mobile_app` | Mobile App |
| `book` | `textbook` | Textbook |
| `book` | `handbook` | Handbook / Manual |
| `book` | `edited_collection` | Edited Collection |
| `book` | `open_textbook` | Open Access Textbook / Free eBook |
| `book` | `style_guide` | Style & Writing Guide |
| `book` | `monograph` | Research Monograph |
| `article` | `seminal_paper` | Seminal Methodology Paper |
| `article` | `methodology_review` | Methodology Review Paper |
| `article` | `exemplar_study` | Published Exemplar Study |
| `article` | `methodology_paper` | Methodology Paper |
| `article` | `methodology_comparison` | Methodology Comparison Paper |
| `article` | `research_article` | Research Article |
| `article` | `review_article` | Review Article |
| `article` | `preprint` | Preprint |
| `article` | `editorial` | Editorial / Commentary |
| `article` | `guideline_article` | Clinical / Practice Guideline Article |
| `reporting_guideline` | `primary_guideline` | Primary Reporting Guideline |
| `reporting_guideline` | `guideline_extension` | Reporting Guideline Extension |
| `reporting_guideline` | `appraisal_tool` | Critical Appraisal Tool |
| `course` | `free_course` | Free Online Course |
| `course` | `paid_course` | Paid Course or Workshop |
| `course` | `open_courseware` | Open Courseware |
| `course` | `workshop_materials` | Workshop / Training Materials |
| `course` | `flashcard_set` | Flashcard / Study Set |
| `video` | `video_tutorial` | Tutorial / How-To Video |
| `video` | `video_lecture` | Lecture / Presentation Recording |
| `video` | `video_explainer` | Explainer / Concept Video |
| `video` | `video_software_demo` | Software Walkthrough |
| `video` | `video_channel` | Video Channel / Series |
| `video` | `video_interview` | Interview / Discussion |
| `podcast` | `podcast_show` | Podcast Show |
| `podcast` | `podcast_episode` | Podcast Episode |
| `web_guide` | `methodology_guide` | Institutional Methodology Guide |
| `web_guide` | `web_article` | Blog Post / Web Article |
| `web_guide` | `blog_site` | Blog / Website (ongoing) |
| `web_guide` | `programme_requirements` | College Research Requirements |
| `web_guide` | `tweetorial` | Tweetorial / Social Thread |
| `web_guide` | `worked_example` | Worked Example / Case Study |
| `template` | `protocol_template` | Research Protocol Template |
| `template` | `ethics_template` | Ethics Application Template |
| `template` | `data_form_template` | Data Extraction / Collection Form |
| `template` | `analysis_plan_template` | Statistical Analysis Plan Template |
| `template` | `checklist_template` | Methodology Checklist / Decision Aid |
| `visual_reference` | `infographic` | Infographic |
| `visual_reference` | `flowchart` | Flowchart / Decision Tree |
| `visual_reference` | `cheat_sheet` | Cheat Sheet / Quick Reference |
| `visual_reference` | `presentation` | Presentation / Slide Deck |
| `visual_reference` | `poster` | Academic Poster |
| `dataset` | `research_dataset` | Research Dataset / Database |
| `dataset` | `teaching_dataset` | Teaching / Practice Dataset |
| `dataset` | `open_data_portal` | Open Data Portal |
| `community` | `online_community` | Online Community / Forum |
| `community` | `professional_network` | Professional Network / Society |
| `community` | `institutional_service` | Institutional Research Support |
| `community` | `mailing_list` | Mailing List / Newsletter |
| `funding` | `government_grant` | Government / National Grant |
| `funding` | `college_grant` | College / Professional Body Grant |
| `funding` | `institutional_grant` | University / Hospital Internal Grant |
| `funding` | `fellowship` | Research Fellowship / Scholarship |

Note: `book_chapter` has zero subtypes. Resources of type `book_chapter` carry null `resource_subtype_code`; they inherit subtype context from their parent book record. Do not create placeholder subtype rows for `book_chapter`.

---

## Builder Notes

- **`code` is globally unique**, not just unique within a parent type. This is a deliberate design choice enabling single-step lookup in `Resource.resource_subtype_code`.
- **Two-step Resource validation required:** a Resource's subtype must (a) exist in ResourceSubtype and (b) have its `type_code` match the Resource's `resource_type_code`.
- **`display_order` is per-parent-type**, not global. Reset to 10, 20, 30... within each parent type.
- **`is_methodology_specific` drives page layout.** Methodology-specific subtypes (`seminal_paper`, `primary_guideline`) get methodology-grouped result lists. Methodology-agnostic subtypes (`reference_manager`, `statistical_software`) get flat lists with methodology as a side-filter.
- **Subtype count reconciliation note.** The v2.0 source document header reported "48 subtypes" but the detailed type sections enumerate 73 distinct subtype codes. The authoritative count from `cothesis_shared_entity_schema.md §4.5` is 61. The roster above reflects 61 subtypes across 13 parent types (excluding `book_chapter`). Any discrepancy with the 73-count in the source detailed sections should be treated as a data-quality issue to resolve during seed data preparation.
