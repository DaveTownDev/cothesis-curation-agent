STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: cothesis_macmini_collected/entity_schemas__ResourceType.md
SUPERSEDES: entities__ResourceType.md (uppercase-code narrative stub)
COMPENDIUM_URL: /library/resources/{slug}
PRODUCED_BY: Task B (schema merge)
DATE: 2026-05-15

---

# Entity: ResourceType

## Purpose

A top-level resource type in the CoThesis Compendium taxonomy. There are 14 types describing the FORMAT of resources (software, book, video, podcast, etc.), distinct from the methodologies/skills that describe their CONTENT. Types appear as primary filter facets in the directory and generate dedicated browse landing pages (`/library/resources/{slug}`). Each type has 0–14 ResourceSubtype children for finer-grained filtering. Cross-profession generalisable — the format-based taxonomy applies to research resources in any domain.

ResourceType is the primary filter facet across the directory and the platform's research-mentor recommendations. The platform also surfaces type-aware recommendations ('You'll need a protocol template for this stage') routed through ResourceType. 14 total — production-ready in the launch dataset.

---

## Source-of-Truth Fields

Note: Page Mixin fields (slug, page_title, meta_description, short_description, seo_primary_terms, seo_secondary_terms, icon, has_page, is_active, phase) are listed below in the Page Mixin section.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string (enum, 14) | yes | Stable, immutable PK. Lowercase snake_case. FK target for ResourceSubtype.type_code and Resource.resource_type_code. Pattern: `^[a-z][a-z0-9_]{1,29}$`. Enum: `software`, `book`, `book_chapter`, `article`, `reporting_guideline`, `course`, `video`, `podcast`, `web_guide`, `template`, `visual_reference`, `dataset`, `community`, `funding`. Once published, never changes even if display name is revised. |
| `name` | string | yes | Display label as shown in the directory filter panel, browse tiles, and breadcrumbs. Plural form; user-friendly. Editorial control. maxLength: 50. Examples: "Software & Tools", "Books & Textbooks", "Journal Articles & Papers". |
| `name_singular` | string \| null | no | Singular form for use in resource detail pages and breadcrumbs. maxLength: 40. Examples: "Software", "Book", "Journal Article". |
| `description` | string \| null | no | Editorial 2–4 sentence description of what this resource type encompasses, what kinds of resources fall under it, and what makes it distinct. Surfaces as the lead paragraph on the type's Compendium page and as a tooltip. maxLength: 1500. |
| `long_description` | string \| null | no | Optional extended description for the ResourceType page body. Multiple paragraphs allowed. maxLength: 5000. |
| `agent_discovery_types` | string[] | no | List of agent-discovery type codes (from the 46-type list) that map to this UX ResourceType. Used by the import pipeline to consolidate granular agent results into UX-facing types. Editorial mapping. |
| `type_specific_fields` | string[] | no | List of field names that are specific to this resource type and appear on Resource records of this type. Editorial reference only — not a dynamic field selector. Each type has 5–15 type-specific fields beyond the universal Resource fields. |
| `common_resource_examples` | string[] | no | Editorial list of well-known example resources of this type. Surfaces on the type page as 'You might be looking for...' suggestions. 4–10 entries. |
| `default_thesis_stage_relevance` | enum[] | no | Default THESIS-stage relevance for resources of this type. Values: `theory`, `history`, `evaluate`, `study`, `interpret`, `share`. Editorial baseline — individual Resources can override. |
| `display_order` | integer | yes | Sort order in filter panel and homepage browse tiles. 10-spaced steps (10, 20, …, 140). Lower value = higher demand / shown first. minimum: 0, maximum: 9999. |
| `subtype_count` | integer \| null | no | Denormalised count of ResourceSubtype rows where `type_code = this.code`. Set at write time or recomputed via scheduled job. `book_chapter` = 0. minimum: 0. |
| `color_accent` | string \| null | no | Optional hex color (#RRGGBB) for type-specific accenting (filter chip outline, page header tint). Used sparingly; cream/forest-green base palette dominates. |
| `notes` | string \| null | no | Internal-only editorial notes. Never user-facing. maxLength: 2000. |

---

## Page Mixin Fields

Attached per P3 — ResourceType surfaces on /library/resources/{slug}

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `slug` | string | yes | URL slug for the Compendium type landing page. Lowercase kebab-case derived from code (underscores → hyphens). Stable once published. Pattern: `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Examples: "software", "book-chapter", "reporting-guideline". |
| `page_title` | string \| null | no | SEO `<title>` tag for the type landing page. Format: `{name} for Medical Research \| CoThesis`. maxLength: 80. |
| `meta_description` | string \| null | no | SEO meta description ≤160 chars. Drives organic CTR for type-level searches. maxLength: 160. |
| `short_description` | string \| null | no | Card/listing text for the type tile on the homepage and category browse pages. 1–2 sentences. maxLength: 280. |
| `seo_primary_terms` | string[] | no | Highest-priority search keywords for this type's landing page. Note: canonical schema splits the CompendiumPageMixin `seo_keywords[]` into primary/secondary for ResourceType. |
| `seo_secondary_terms` | string[] | no | Supporting keywords. 5–15 entries. |
| `icon` | string | yes | Lucide icon name displayed in filter sidebar, browse tiles, and breadcrumbs. Each ResourceType has a distinct icon for visual scanability. Examples: "wrench", "book", "file-text", "list-checks". |
| `has_page` | boolean | no | Whether the Compendium landing page is generated. Default: true. All 14 types ship with pages at launch. |
| `is_active` | boolean | yes | Whether this ResourceType appears in user-facing filters, dropdowns, and homepage browse tiles. Default: true. |
| `phase` | integer | yes | Rollout phase. 1 = launch (all 14 ship). 2/3 reserved for future additions. minimum: 1, maximum: 5. Default: 1. |

---

## Derived Fields

(none)

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|----------|-----------|--------|----------|-------|
| type_code | one→many | ResourceSubtype | ResourceSubtype.type_code | Every subtype belongs to exactly one ResourceType. DB FK constraint required. `book_chapter` has subtype_count = 0. |
| code | one→many | Resource | Resource.resource_type_code | Every Resource has exactly one type. Validate at import. |
| (proposed) | M:N | ListicleArticle | applicable_resource_types[] on ListicleArticle | Implementation TBD; surfaces related listicles on the type page. |

---

## Builder Notes

- **Codes are immutable and enum-constrained.** The 14 types are editorially closed for launch. Adding a 15th requires a substantive editorial decision and display_order renumbering.
- **Code uses snake_case; slug uses kebab-case.** `book_chapter` (code) → `book-chapter` (slug). Conversion is mechanical.
- **`book_chapter` has `subtype_count = 0`.** No subtypes — chapters inherit subtype context from their parent book.
- **`agent_discovery_types[]` is the import-pipeline bridge** from the 46-type discovery taxonomy to the 14-type UX taxonomy. Every agent type code must map to exactly one UX type.
- **`type_specific_fields[]` is documentation, not a dynamic field selector.** The actual field-selection logic is hard-coded in the Resource schema's variant blocks.
- **Display order convention:** 10-spaced steps. Current order reflects user demand — `software` at 10 (most-searched).
- **Compendium pages are SEO-critical.** Each ResourceType page is a directory landing page for high-volume category search. Populate `seo_primary_terms` and `seo_secondary_terms` before shipping.
- **`subtype_count` is denormalised.** Set at write time when subtypes are added/removed, or recompute via scheduled job.
