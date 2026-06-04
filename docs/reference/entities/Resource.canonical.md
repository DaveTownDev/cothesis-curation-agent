# Resource — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Resource.md + _task6_field_mapping_matrix.md (field consolidation)
VERSION: unified-schema v1.0 (merge output)
COMPENDIUM_URL: /library/{subtype_slug}/{slug}

## Purpose
A Resource is a single curated item in the CoThesis research directory. Resources are the primary content objects — articles, books, software, videos, podcasts, templates, etc. — linked to methodologies, disciplines, and training stages to power contextual recommendations.

## Source-of-Truth Fields (Universal Base)

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `resource_id` | string (uuid) | Yes | — | System-generated UUID. Universal join key across PostgreSQL, Convex, Neo4j, Qdrant, Payload CMS. Never changes after assignment. |
| `code` | string | Yes | — | Stable human-readable PK (kebab-case, globally unique). Used in all cross-entity FKs. |
| `resource_type_code` | string | Yes | ResourceType.code | Was: `type_code` enum. FK to ResourceType using code pattern (P4). |
| `resource_subtype_code` | string | No | ResourceSubtype.code | Was: `subtype_code`/`subtype`. Globally unique across 48 subtypes. Null for types with no active subtype. Two-step integrity: must exist in ResourceSubtype AND its parent type must match `resource_type_code`. |
| `title` | string | Yes | — | Primary display title. Cluster A canonical name. Aliases seen across subtypes: `name`, `programme_name`, `template_name`, `guideline_name`, `blog_name`, `channel_name`, `show_name`. |
| `url` | string (uri) | No | — | Canonical external URL. Verified per freshness_interval_days. |
| `doi` | string | No | — | DOI identifier. Present on 9/13 subtypes (absent on community, web_guide, podcast, funding in most cases). |
| `description` | string | No | — | Publisher/source-supplied description (abstract, tagline, etc.). Cluster B. DISTINCT from editorial_description. Never editorial-authored. |
| `editorial_description` | string | No | — | CoThesis-authored 1–2 sentence summary. Never copied from source (editorial-independence rule). Required for reviewed/featured tiers. |
| `editorial_note` | string | No | — | CoThesis editorial assessment ("why this matters"). Required for `featured` status. DISTINCT from editorial_description (shorter, purpose-different). Both are kept — see Notes. |
| `editorial_status` | string (enum) | Yes | — | `proposed` \| `in_review` \| `published` \| `archived` \| `deprecated`. Workflow status for editorial pipeline. |
| `methodology_codes` | string[] | No | Methodology.code[] | Was: `methodology_tags` (matrix/directory). Renamed per Task I field naming locks. 162-methodology taxonomy. |
| `discipline_codes` | string[] | No | ProfessionalDiscipline.code[] | Was: `specialty_tags` (matrix/directory). Renamed per Task I. Empty = universal. |
| `stage_codes` | string[] | No | Stage.code[] | Relevant THESIS stages. Was: `thesis_stages`. Phase codes (two-letter, migration 08): `TH` \| `HI` \| `EV` \| `ST` \| `IN` \| `SH`. Was: `getting_started` \| `literature_background` \| `planning_ethics` \| `doing_research` \| `making_sense` \| `writing_sharing` (renamed per Task I). |
| `skill_codes` | string[] | No | FoundationSkill.code[] | Was: `skill_tags`. FS-NN code pattern. |
| `area_codes` | string[] | No | CrossCuttingArea.code[] | Cross-cutting area relevance. |
| `topic_tags` | string[] | No | — | Free-form topic tags. Cluster I canonical name. Aliases: `keywords`, `tags`, `topics`, `subjects`, `categories`, `concepts`, `mesh_terms`. |
| `country_codes` | string[] | No | Country.code[] | Geographic relevance. Empty = universal. |
| `year_published` | integer | No | — | Original publication year. Derived from `publication_date`. Was: `publication_year`. |
| `publication_date` | string (date) | No | — | Original publication/release date. Cluster D canonical name. Aliases: `published_date`, `release_date`, `published_at`, `air_date`, `pub_date`, `version_date`, `date_published`. |
| `authors` | string[] | No | — | Author/creator names (free-text). Cluster C canonical (free-text form). No Author entity yet. Structured sub-entity forms live in type_fields. |
| `author_or_provider` | string | No | — | Free-text creator/author/provider (single string fallback for simple cases). |
| `publisher_code` | string | No | Organisation.code | FK to Organisation (type includes `publisher`). Was: `publisher_or_platform` free-text. |
| `journal_code` | string | No | Journal.code | Article/preprint only. Auto-resolved via DOI lookup. |
| `language_code` | string | No | — | ISO 639-1 primary language. Default `en`. Present in 12/13 subtypes (absent on funding). |
| `additional_languages` | string[] | No | — | Other ISO 639-1 codes the resource is available in. |
| `content_format` | string (enum) | No | — | Physical/sensory format: `text` \| `video` \| `audio` \| `interactive` \| `pdf` \| `spreadsheet` \| `infographic` \| `flowchart` \| `slide_deck` \| `mixed`. Distinct from resource_type_code. |
| `access_type` | string (enum) | Yes | — | `free` \| `freemium` \| `paid` \| `subscription` \| `institutional` \| `open_access`. |
| `is_open_access` | boolean | No | — | Open-access flag. Was: `is_oa`, `is_free`. Present 11/13 subtypes. |
| `licence_type` | string | No | — | Licence identifier e.g. `CC-BY-4.0`, `All Rights Reserved`. Was: `license`. |
| `price_description` | string | No | — | Human-readable price/pricing description. Cluster M canonical (free-text form). Structured pricing fields live in type_fields. |
| `student_pricing` | boolean | No | — | Whether student/academic pricing available. |
| `institutional_access` | boolean | No | — | Whether available via university/hospital subscription. |
| `thumbnail_url` | string (uri) | No | — | Card/detail image. Cluster F canonical name. Aliases: `cover_image_url`, `image_url`, `logo_url`, `artwork_url`, `course_image_url`, `banner_url`, `channel_avatar_url`, `icon_url`. |
| `source_authority` | string (enum) | No | — | Editorial authority tier: `tier_a` \| `tier_b` \| `tier_c`. |
| `difficulty_level` | string (enum) | No | — | `beginner` \| `intermediate` \| `advanced`. |
| `ai_subtype_signal` | string | No | — | AI-inferred subtype classification signal. Was: `subtype_classification` (renamed per Task I). This is an LLM signal — NOT the `resource_subtype_code` FK. Easily confused: subtype_signal is ephemeral/probabilistic; subtype_code is the stored FK. |
| `current_ai_assessment_id` | string | No | AIAssessment.(resource_code, assessed_at) | Reference to most-recent AIAssessment record for this resource. Allows quick lookup of current scores without joining full history. |
| `quality_score` | number | No | — | Current quality score snapshot (0-100). Denormalised from current AIAssessment for fast querying. Canonical scale: 0-100. |
| `source_urls` | string[] | No | — | Alternative/mirror URLs for the resource. |
| `alternative_titles` | string[] | No | — | Aliases and abbreviations for search recall. Not public. |
| `related_resource_codes` | string[] | No | Resource.code[] | Curated related resources (alternatives, companions, prerequisites). Editorial only; not necessarily symmetric. |
| `import_source` | string | No | — | Import pipeline origin e.g. `manual`, `pubmed`, `crossref`, `openalex`. Was: `source` on golden records. |
| `import_id` | string | No | — | ID in source system (used with import_source for deduplication). |
| `last_verified` | string (date) | Yes | — | When CoThesis last confirmed URL works / info current. |
| `freshness_flag` | string (enum) | Auto | — | `fresh` \| `stale` \| `expired`. Auto-derived from `last_verified` vs type-specific threshold. |
| `field_provenance` | object (JSON) | No | — | Universal provenance JSON per golden record. Present in all 13 golden-record files; absent from canonical entity_schemas__Resource.md (gap now closed). |
| `golden_record_version` | string | No | — | Version identifier for the golden record. |
| `golden_record_hash` | string | No | — | Hash of the golden record at last import (for change detection). |
| `suggested_by` | string | No | UserProfile.user_id | User ID if submitted via "suggest a resource" flow. |
| `notes_internal` | string | No | — | Internal editorial notes. Not public. |
| `convex_id` | string | No | — | Convex document ID for synced subset. Platform field. |
| `neo4j_node_id` | string | No | — | Neo4j internal node ID. Platform field. |
| `qdrant_point_id` | string (uuid) | No | — | Qdrant point ID for embedding vector. Platform field. |
| `embedding_model` | string | No | — | Embedding model used e.g. `gemini-embedding-001`. Platform field. |
| `i_use_this_count` | integer | Auto | — | Count of users who flagged "I use this". Derived; not shown until threshold. |
| `save_count` | integer | Auto | — | Count of users who saved to a Collection. Derived; internal metric. |
| `type_fields` | object (JSON) | Yes (may be {}) | — | Subtype-specific extension JSON (JSONB). Shape discriminated by `resource_type_code`. Carries the 9-18 subtype-specific fields per ResourceSubtype. |
| `created_at` | datetime | Yes | — | Record creation timestamp. Auto-set. |
| `updated_at` | datetime | Yes | — | Last modification timestamp. Auto-set. |

## Resource.editorial Embedded Object

Embedded object on Resource carrying human-ratified editorial metadata. Distinct from AIAssessment fields (which are AI-generated).

| Field | Type | Notes |
|---|---|---|
| `editorial_badges` | string[] | Human-ratified recommendation badges (max 3). Values: `editors_choice` \| `best_free` \| `best_beginners` \| `best_time_poor` \| `essential` \| `expert_pick`. Was: `badges` (directory §3.4). AI-proposed badges live on AIAssessment.proposed_badges — see Notes. |
| `editorial_note` | string | Human editorial assessment ("why this matters"). Required for `featured` status. |
| `editorial_status` | string (enum) | `proposed` \| `in_review` \| `published` \| `archived` \| `deprecated`. |
| `editorial_reviewed_by` | string | user_code of the reviewer who last updated editorial status. |
| `editorial_reviewed_at` | datetime | Timestamp of last editorial review. |

## Page Mixin Fields

Attached per P3. Resources surface on Compendium at `/library/{subtype_slug}/{slug}`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `slug` | string (kebab-case) | Yes | URL slug. Used in: `/library/{subtype_slug}/{slug}`. |
| `page_title` | string | No | SEO `<title>` tag. Default: `{title} \| CoThesis`. |
| `meta_description` | string | No | SEO meta description ≤160 chars. Derived from editorial_description. |
| `short_description` | string | No | Brief description for card/list contexts (≤80 chars). |
| `seo_keywords` | string[] | No | SEO keyword list. |
| `icon` | string | No | Icon identifier or URL for UI display. |
| `has_page` | boolean | Yes | Whether this resource has a published Compendium detail page. |
| `is_active` | boolean | Yes | User-facing visibility. Default true. Distinct from editorial_status workflow field. |
| `phase` | integer | Yes | Rollout phase 1-5. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `oa_status` | `is_open_access` + `licence_type` | enum: `open` \| `restricted` \| `unknown`. `open` if is_open_access=true OR licence_type starts with "CC-"; `restricted` if paid/institutional; `unknown` otherwise. |
| `display_type_label` | `resource_type_code` | Look up ResourceType.name via active presentation layer. |
| `freshness_flag` | `last_verified` | Auto-derived from last_verified date vs type-specific freshness threshold. |
| `year_published` | `publication_date` | Extract year component from publication_date. |
| `quality_score` (snapshot) | `current_ai_assessment_id` → AIAssessment.quality_score | Denormalised from most-recent AIAssessment for fast querying. Updated when new assessment is created. |
| `i_use_this_count` | Bookmark/Endorsement records | Aggregate count from user interaction records. |
| `save_count` | Collection records | Aggregate count of saves across user collections. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| resource_type_code | many→one | ResourceType | `resource_type_code` → ResourceType.code | Every resource has exactly one type. Integrity: value must exist in ResourceType.code enum. |
| resource_subtype_code | many→one | ResourceSubtype | `resource_subtype_code` → ResourceSubtype.code | At most one subtype. Two-step integrity check required. |
| methodology_codes | many→many | Methodology | `methodology_codes[]` → Methodology.code[] | Denormalised array FK. Methodology.start_here[] and stage_resources{} provide reciprocal back-references (editorially curated, not auto-synced). |
| discipline_codes | many→many | ProfessionalDiscipline | `discipline_codes[]` → ProfessionalDiscipline.code[] | No reciprocal field on ProfessionalDiscipline. |
| stage_codes | many→many | Stage | `stage_codes[]` → Stage.code[] | No reciprocal field. |
| skill_codes | many→many | FoundationSkill | `skill_codes[]` → FoundationSkill.code[] | No reciprocal field. |
| area_codes | many→many | CrossCuttingArea | `area_codes[]` → CrossCuttingArea.code[] | No reciprocal field. |
| country_codes | many→many | Country | `country_codes[]` → Country.code[] | No reciprocal field. |
| publisher_code | many→one | Organisation | `publisher_code` → Organisation.code | Organisation.types[] must include `publisher`. |
| journal_code | many→one | Journal | `journal_code` → Journal.code | Article/preprint subtypes only. Auto-resolved via DOI. |
| current_ai_assessment_id | many→one | AIAssessment | `current_ai_assessment_id` → AIAssessment.(resource_code, assessed_at) | Points to the most-recent assessment. |
| code (as FK target) | one→many | AIAssessment | AIAssessment.resource_code → Resource.code | Full assessment history queryable. |
| related_resource_codes | many→many (self) | Resource | `related_resource_codes[]` → Resource.code[] | Editorial; not necessarily symmetric. |
| ListicleArticle | many→many | ListicleArticle | `listicle_appearances[]` ← computed from ListicleArticle.entries | Reciprocal field exists on ListicleArticle.entries; listicle_appearances is a cached derivation requiring refresh. |
| Bookmark / Endorsement / ResearchProject | one→many (FK target) | UserProfile interactions | Resource.resource_id referenced by interaction tables | Counts denormalised back via i_use_this_count, save_count. |

## Notes

- **editorial_description vs editorial_note**: BOTH KEPT with distinct purposes. `editorial_description` = AI-authored factual summary of what the resource is (required for all published resources). `editorial_note` = human-authored editorial rationale for why it matters (required only for `featured` status). The matrix flagged `editorial_description_long` as an alias for `editorial_note` — resolved: editorial_note is the canonical name.
- **methodology_tags renamed to methodology_codes** per Task I field naming locks (FK pattern consistency with P4).
- **specialty_tags renamed to discipline_codes** per Task I (consistency with entity name ProfessionalDiscipline).
- **subtype_classification renamed to ai_subtype_signal** per Task I (disambiguation from the resource_subtype_code FK — these are entirely different concepts: one is the stored FK, the other is an ephemeral AI classification signal).
- **editorial_badges split**: `proposed_badges` (AI-suggested, on AIAssessment) + `editorial_badges` (human-ratified, on Resource.editorial). The matrix classified badges as LLM-authored; the canonical schema and directory §8 say badges are editorial-only. Resolution: AI proposes → human ratifies. AI proposals stored on AIAssessment.proposed_badges. Ratified set stored on Resource.editorial.editorial_badges.
- **quality_score scale**: 0-100. The matrix §6.2 showed 0-1; the canonical schema and directory §3.4 both say 0-100. Canonical wins. Migration: multiply legacy 0-1 values × 100.
- **Type-specific fields** (per subtype) documented in ResourceSubtype.<name>.canonical.md files. They are stored in `type_fields` JSONB.
- **methodology_tags / specialty_tags in AIAssessment**: The AI assessment pipeline also produces methodology and discipline tags; these are stored on AIAssessment as `relevance_to_methodology_codes` and `relevance_to_discipline_codes` (AI signal). The human-ratified values are on Resource.methodology_codes / Resource.discipline_codes.
- **ERD placement**: Resource is confirmed as Entity in the unified schema (Layer 5: Resource Records). The conflicting documents have been reconciled in favour of explicit inclusion.
