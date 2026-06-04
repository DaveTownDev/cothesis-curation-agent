# CoThesis Compendium — Resource Enrichment, Quality Control & Quality Rating Specification

**Grounded in:** `project_upload/schema_entity_Resource.canonical.md`, `schema_entity_AIAssessment.canonical.md`, all 18 `schema_entity_ResourceSubtype.*.canonical.md` files, `schema_taxonomy_resource_type_taxonomy.canonical.md`, `schema_layer_compendium.layer.md`, `schema_meta_open_questions.md`, `cothesis_macmini_collected/cothesis_compendium_build_spec.md`, `cothesis_macmini_collected/compendium_content_types_reference.md`, `cothesis_macmini_collected/compendium_schema_reference.md`, `current_directory/cothesis_resource_directory_schema.md`, `current_directory/data_sources_by_resource_type.md`, `current_directory/cothesis_resource_type_definitions_for_agents.md`

**[AUTO]** = fully automatable. **[REVIEW]** = agent can draft, human must approve. **[HUMAN]** = human judgement required. **[INFERRED]** = not explicitly stated in any file.

---

## 1. ENRICHMENT — Complete Field Inventory

### 1.1 Universal Resource Fields

Every field on the canonical `Resource` entity, with provenance, rules, and publish requirements.

Source: `schema_entity_Resource.canonical.md`

| Field | Type | Required for Publish | Provenance | Rules / Constraints |
|---|---|---|---|---|
| `resource_id` | string (uuid) | Yes | System-generated | Never changes after assignment. Universal join key across PostgreSQL, Convex, Neo4j, Qdrant, Payload |
| `code` | string | Yes | System-generated | Kebab-case, globally unique. Used in all cross-entity FKs. Never changes |
| `resource_type_code` | string | Yes | [REVIEW] classifier sets, human confirms | FK to ResourceType.code (14 types). Pattern P4 |
| `resource_subtype_code` | string | No | [REVIEW] classifier sets, human confirms | Two-step integrity: (a) must exist in ResourceSubtype; (b) parent type must match `resource_type_code`. Null for types with no active subtype |
| `title` | string | Yes | [AUTO] source-ingested | Primary display title. Aliases: `name`, `programme_name`, `template_name`, `guideline_name`, `blog_name`, `channel_name`, `show_name` |
| `url` | string (uri) | No | [AUTO] source-ingested | Canonical external URL. Verified per type-specific `freshness_interval_days` |
| `doi` | string | No | [AUTO] source-ingested | Present on 9/13 subtypes. Absent on: community, web_guide, podcast, funding in most cases |
| `description` | string | No | [AUTO] source-ingested | Publisher/source-supplied description (abstract, tagline). **Never** editorial-authored. Distinct from `editorial_description` |
| `editorial_description` | string | **Yes (reviewed/featured tier)** | [REVIEW] AI drafts, human finalises | See §5 for full specification. **⚠️ Authorship contradiction — see §7.1** |
| `editorial_note` | string | **Yes (featured status only)** | [HUMAN] human-authored | "Why this matters" rationale. Distinct from editorial_description |
| `editorial_status` | string (enum) | Yes | [AUTO] system-managed | `proposed` \| `in_review` \| `published` \| `archived` \| `deprecated` |
| `methodology_codes` | string[] | No | [REVIEW] AI proposes (on AIAssessment), human ratifies on Resource | FK to Methodology.code[]. Formerly `methodology_tags`. 162-methodology taxonomy |
| `discipline_codes` | string[] | No | [REVIEW] AI proposes (on AIAssessment), human ratifies on Resource | FK to ProfessionalDiscipline.code[]. Formerly `specialty_tags`. Empty = universal |
| `stage_codes` | string[] | No | [REVIEW] AI proposes (as `thesis_stage_signals` on AIAssessment), human ratifies | FK to Stage.code[]. Values: `TH` \| `HI` \| `EV` \| `ST` \| `IN` \| `SH` |
| `skill_codes` | string[] | No | [REVIEW] AI proposes, human ratifies | FK to FoundationSkill.code[]. Formerly `skill_tags` |
| `area_codes` | string[] | No | [REVIEW] AI proposes, human ratifies | FK to CrossCuttingArea.code[] |
| `topic_tags` | string[] | No | [AUTO] source-ingested (e.g. MeSH terms) + [REVIEW] AI supplements | Free-form. Aliases: `keywords`, `tags`, `topics`, `subjects`, `categories`, `concepts`, `mesh_terms` |
| `country_codes` | string[] | No | [AUTO] source-ingested | FK to Country.code[]. Empty = universal |
| `year_published` | integer | No | [AUTO] derived | Extracted from `publication_date` |
| `publication_date` | string (date) | No | [AUTO] source-ingested | Aliases: `published_date`, `release_date`, `published_at`, `air_date`, `pub_date`, `version_date`, `date_published` |
| `authors` | string[] | No | [AUTO] source-ingested | Author/creator names (free-text) |
| `author_or_provider` | string | No | [AUTO] source-ingested | Single-string fallback for creator/author/provider |
| `publisher_code` | string | No | [AUTO] resolved via DOI/ROR lookup | FK to Organisation.code. Formerly free-text `publisher_or_platform` |
| `journal_code` | string | No | [AUTO] resolved via DOI lookup | FK to Journal.code. Article/preprint only |
| `language_code` | string | No | [AUTO] source-ingested or AI-detected | ISO 639-1. Default `en` |
| `additional_languages` | string[] | No | [AUTO] source-ingested | Other ISO 639-1 codes |
| `content_format` | string (enum) | No | [REVIEW] AI classifies | `text` \| `video` \| `audio` \| `interactive` \| `pdf` \| `spreadsheet` \| `infographic` \| `flowchart` \| `slide_deck` \| `mixed` |
| `access_type` | string (enum) | **Yes** | [REVIEW] AI classifies, human confirms | `free` \| `freemium` \| `paid` \| `subscription` \| `institutional` \| `open_access` |
| `is_open_access` | boolean | No | [AUTO] ingested + derived from `oa_status` | Present on 11/13 subtypes |
| `licence_type` | string | No | [AUTO] source-ingested | e.g. `CC-BY-4.0`, `All Rights Reserved` |
| `price_description` | string | No | [AUTO] source-ingested | Human-readable pricing |
| `student_pricing` | boolean | No | [AUTO] source-ingested | Whether student/academic pricing exists |
| `institutional_access` | boolean | No | [AUTO] source-ingested | Whether available via subscription |
| `thumbnail_url` | string (uri) | No | [AUTO] source-ingested | Card/detail image. Aliases by subtype: `cover_image_url`, `logo_url`, `artwork_url`, etc. |
| `source_authority` | string (enum) | No | [HUMAN] editorially assigned | `tier_a` \| `tier_b` \| `tier_c`. **Criteria not defined in any file — see §7.6** |
| `difficulty_level` | string (enum) | No | [REVIEW] AI assesses (on AIAssessment), human ratifies | `beginner` \| `intermediate` \| `advanced`. See §3.4 |
| `ai_subtype_signal` | string | No | [AUTO] AI-generated | Ephemeral classification signal. Distinct from `resource_subtype_code` FK |
| `current_ai_assessment_id` | string | No | [AUTO] updated by pipeline | Reference to most-recent AIAssessment record |
| `quality_score` | number (0-100) | No | [AUTO] denormalised from AIAssessment | Updated when new AIAssessment is created. Hidden on card if < 60 |
| `source_urls` | string[] | No | [AUTO] source-ingested | Alternative/mirror URLs |
| `alternative_titles` | string[] | No | [REVIEW] AI + editorial | Aliases and abbreviations for search recall. Not public |
| `related_resource_codes` | string[] | No | [HUMAN] editorial only | FK to Resource.code[]. Curated related resources. Not necessarily symmetric |
| `import_source` | string | No | [AUTO] pipeline-set | e.g. `manual`, `pubmed`, `crossref`, `openalex` |
| `import_id` | string | No | [AUTO] pipeline-set | ID in source system. Used with `import_source` for deduplication |
| `last_verified` | string (date) | **Yes** | [AUTO] pipeline-updated | When CoThesis last confirmed URL works / info is current |
| `freshness_flag` | string (enum) | No | [AUTO] derived | `fresh` \| `stale` \| `expired`. Auto-derived from `last_verified` vs type-specific threshold |
| `field_provenance` | object (JSON) | No | [AUTO] pipeline-written | Per-field provenance JSON for golden record |
| `golden_record_version` | string | No | [AUTO] pipeline-written | Version identifier for the golden record |
| `golden_record_hash` | string | No | [AUTO] pipeline-written | Hash for change detection |
| `suggested_by` | string | No | [AUTO] system-set | FK to UserProfile.user_id if submitted via "suggest a resource" flow |
| `notes_internal` | string | No | [HUMAN] editorial | Internal notes. Not public |
| `convex_id`, `neo4j_node_id`, `qdrant_point_id` | string | No | [AUTO] platform | System-managed cross-store IDs |
| `embedding_model` | string | No | [AUTO] platform | e.g. `gemini-embedding-001` |
| `i_use_this_count` | integer | No | [AUTO] derived | Aggregate from user interaction records. Not shown until threshold met |
| `save_count` | integer | No | [AUTO] derived | Aggregate from Collection saves |
| `type_fields` | object (JSON) | Yes (may be `{}`) | [AUTO] per-type enricher | JSONB. Shape discriminated by `resource_type_code`. Carries 9-18 subtype-specific fields |
| `created_at`, `updated_at` | datetime | Yes | [AUTO] system | Auto-set |

### 1.2 Resource.editorial Embedded Object

Source: `schema_entity_Resource.canonical.md`

"Embedded object on Resource carrying human-ratified editorial metadata. Distinct from AIAssessment fields (which are AI-generated)."

| Field | Provenance | Rules |
|---|---|---|
| `editorial_badges` | [HUMAN] human-ratifies AI proposals | Max 3 stored. Values: `editors_choice` \| `best_free` \| `best_beginners` \| `best_time_poor` \| `essential` \| `expert_pick`. Only 1 shown on card (priority order). AI-proposed badges live on AIAssessment.proposed_badges |
| `editorial_note` | [HUMAN] human-authored | "Why this matters." Required for `featured` status |
| `editorial_status` | [AUTO/HUMAN] | `proposed` \| `in_review` \| `published` \| `archived` \| `deprecated`. **⚠️ Duplicated at top-level — see §7.8** |
| `editorial_reviewed_by` | [AUTO] system-set | user_code of reviewer |
| `editorial_reviewed_at` | [AUTO] system-set | Timestamp of last editorial review |

### 1.3 Page Mixin Fields

Source: `schema_entity_Resource.canonical.md`. Resources surface at `/library/{subtype_slug}/{slug}`.

| Field | Required | Provenance |
|---|---|---|
| `slug` | Yes | [AUTO] generated from title |
| `page_title` | No | [AUTO] derived. Default: `{title} \| CoThesis` |
| `meta_description` | No | [AUTO] derived from editorial_description. ≤160 chars |
| `short_description` | No | [REVIEW] AI-drafted. ≤80 chars |
| `seo_keywords` | No | [AUTO] AI-generated |
| `icon` | No | [AUTO] sourced |
| `has_page` | Yes | [AUTO] pipeline-set |
| `is_active` | Yes | Default true |
| `phase` | Yes | Rollout phase 1–5 |

### 1.4 Per-Subtype Field Additions (type_fields content)

Source: individual `schema_entity_ResourceSubtype.*.canonical.md` files

**Article** (~93 total fields): `journal_code`, `volume`, `issue`, `pages`, `peer_reviewed`, `pmid`, `pmc_id`, `openalex_id`, `preprint_server`, `preprint_id`, `retracted`, `retraction_note`, `altmetric_score`, `citation_count`, `fwci`, `rcr`, `mesh_terms`, `author_keywords`, `abstract`, `ebm_level` (feeds `quality_dimensions.ebm_level`), `study_type`, `journal_impact_factor`, `is_erratum`, `linked_erratum_doi`. Sources: PubMed (NCBI eUtils), Crossref, Semantic Scholar, Unpaywall.

**Book** (~50+ fields): `isbn_13`, `isbn_10`, `edition`, `chapter_count`, `has_ebook`, `ebook_url`, `series_name`, `binding`, `citation_count`, `openalex_id`, `google_books_rating`, `goodreads_rating`, `open_syllabus_score`, `previous_edition_adequate` [AUTO — AI-authored per matrix Cluster L], `companion_url`, `key_chapters` [AUTO — AI-identified]. Sources: Google Books API, OpenLibrary, Crossref.

**Course** (~45 fields): `provider_code`, `course_url`, `duration_hours`, `effort_hours_per_week`, `duration_weeks`, `format` (enum: `self_paced` \| `cohort` \| `live` \| `workshop` \| `blended`), `certification_available`, `cost_aud`, `has_free_tier`, `financial_aid`, `cme_credits`, `is_peer_reviewed`, `platform_rating`, `class_central_rating`, `merlot_peer_review_score`, `enrollment_count`, `instructor_names`, `presenter_person_ids`, `sample_cards`, `card_count`, `time_commitment` [AUTO — AI assessment]. Sources: provider APIs, web scrape.

**Software** (~87 total fields): `platform`, `operating_systems`, `interface_type`, `primary_methodology_use`, `skill_level_required` (tool's stated requirement; **distinct from** `difficulty_level` on AIAssessment which is the AI's independent assessment), `learning_curve` [AUTO — AI-authored per Cluster L], `open_source`, `github_url`, `github_stars`, `github_forks`, `github_contributors`, `oss_health_signal`, `documentation_url`, `pypi_name`, `cran_name`, `rrid`, `rrid_publication_mentions`, `alternatives`, `integrations`, `features`, `comparable_tools` [AUTO — AI-authored], `key_limitations` [AUTO — AI-authored], `pricing_model`, `pricing_tiers`, `starting_price`, `has_free_tier`, `g2_rating`, `capterra_rating`, `app_store_rating`, `bio_tools_id`, `edam_topics`, `edam_operations`, `maturity`, `has_api`, `screenshot_urls`, `developer_name`. Sources: GitHub API, web scrape.

**Dataset** (~40 fields): `data_format`, `record_count`, `variable_count`, `date_range_start`, `date_range_end`, `data_access` (enum: `open` \| `credentialed` \| `restricted` \| `request`), `repository_url`, `data_doi`, `api_url`, `api_available`, `download_url`, `data_dictionary_url`, `geographic_scope`, `geographic_coverage`, `file_count`, `file_size`, `related_publication_dois`, `kaggle_usability_score`, `openalex_id`, `zenodo_doi`, `figshare_id`, `fairsharing_id`, `download_count`, `view_count`, `access_summary` [AUTO — AI-generated]. Sources: DataCite REST API, Zenodo API.

**Video** (~35 fields): `platform_code`, `channel_code`, `youtube_video_id`, `vimeo_id`, `duration_seconds`, `view_count`, `like_count`, `comment_count`, `total_video_count`, `total_view_count`, `subscriber_count`, `transcript_available`, `transcript_source`, `transcript_language`, `captions_available`, `presenter_person_ids`, `guest_person_ids`, `video_categories`, `is_jove`, `jove_doi`, `software_resource_code`, `conference_entity_id`, `relevant_video_count` [AUTO — AI signal]. Sources: YouTube Data API v3.

**Reporting Guideline** (~30 fields): `acronym`, `full_title`, `checklist_url`, `explanation_elaboration_url`, `flow_diagram_url`, `extension_codes`, `parent_guideline_code`, `extension_count`, `methodology_codes_covered`, `issuing_body_code`, `equator_url`, `fairsharing_id`, `applicable_study_types`, `guideline_scope` [AUTO — AI-generated], `endorsing_journals`, `endorsing_journals_count`, `development_group`, `status` (enum: `active` \| `superseded` \| `withdrawn`), `translations`, `pmid`, `citation_count`, `article_resource_code`. Source: EQUATOR Network scrape.

**Podcast** (~40 fields): `show_code`, `podcast_show_entity_id`, `episode_number`, `season_number`, `duration_seconds`, `transcript_url`, `air_date`, `rss_guid`, `podcast_index_id`, `listen_notes_id`, `spotify_id`, `podchaser_id`, `listen_score`, `listen_score_percentile`, `podchaser_rating`, `trending_score`, `total_episodes`, `host_person_ids`, `guest_person_ids`, `has_chapters`, `chapters`, `social_links`, `artwork_url`, `is_dead`, `primary_topics` [AUTO — AI-assessed], `relevant_episode_count` [AUTO — AI signal], `host_expertise_assessment` [AUTO — AI assessment]. Sources: iTunes Search API, Listen Notes API, RSS.

**Web Guide** (~35 fields): `site_name`, `parent_site_code`, `content_type` (enum: `tutorial` \| `reference` \| `blog_post` \| `faq` \| `tool` \| `guide` \| `news` \| `wiki`), `word_count`, `reading_time_minutes`, `post_frequency`, `post_count`, `outbound_academic_links`, `references_dois`, `wayback_url`, `permacc_url`, `is_archived`, `meta_description`, `og_image`, `favicon_url`, `operator_name`, `operator_person_id`, `operator_institution_id`, `primary_topics` [AUTO — AI-assessed], `credibility_assessment` [AUTO — AI-generated], `access_type`. Source: web scrape, Wayback Machine API.

**Visual Reference** (~37 fields): `visual_type` (enum: `infographic` \| `diagram` \| `slide_deck` \| `poster` \| `figure` \| `flowchart` \| `table` \| `illustration`), `file_format`, `resolution`, `dimensions`, `is_embargoed`, `embargo_end_date`, `view_count`, `download_count`, `like_count`, `figshare_id`, `zenodo_doi`, `f1000_id`, `openalex_id`, `creator_person_ids`, `conference_entity_id`, `source_article_code`.

**Funding** (~35 fields): `funding_type` (enum: `grant` \| `fellowship` \| `scholarship` \| `award` \| `bursary` \| `prize`), `funder_code`, `amount_aud_min`, `amount_aud_max`, `stipend_amount`, `currency`, `eligibility_stage`, `eligibility`, `application_deadline`, `application_url`, `application_frequency`, `recurrence`, `success_rate`, `typical_duration`, `duration_years`, `start_date`, `end_date`, `who_should_apply` [AUTO — AI-authored guidance], `resulting_publication_count`, `research_categories`, `gtr_id`, `nih_project_number`, `dimensions_grant_id`, `cordis_id`, `agency_name`, `contact_email`. Source: web scrape.

**Research Database** (~20 fields, added in taxonomy v2.2/OQ-005): `query_interface_type` (enum: `search_form` \| `api` \| `both`), `access_tier` (enum: `open` \| `registered` \| `institutional` \| `paid`), `api_documentation_url`, `record_count_approximate`, `data_dictionary_url`, `update_frequency` (enum: `daily` \| `weekly` \| `monthly` \| `quarterly` \| `irregular`), `coverage_start_year`, `primary_content_type` (enum: `literature` \| `trials` \| `systematic_reviews` \| `guidelines` \| `protocols` \| `mixed`), `indexing_criteria_url`, `search_filter_support`, `mesh_indexed`, `login_required`. Source: web scrape.

**Community** (~29 fields): `platform_code`, `member_count`, `subscriber_count`, `membership_type` (enum: `open` \| `invitation` \| `paid`), `moderation_level` (enum: `light` \| `moderate` \| `heavy`), `services_offered`, `geographic_scope`, `eligibility`, `newsletter_frequency`, `newsletter_subscribe_url`, `social_links`, `person_entity_ids`. Source: web scrape.

**Template** (~36 fields): `template_format` (enum: `docx` \| `xlsx` \| `pdf` \| `pptx` \| `csv` \| `other`), `template_url`, `download_url`, `methodology_codes_applicable`, `stage_codes_applicable`, `issuing_body_code`, `is_peer_reviewed`, `sections`, `applicable_study_types`, `jurisdiction`, `aligned_guideline_code`, `version_date`, `translations`, `github_url`, `github_stars`, `protocols_io_url`, `nct_id`.

### 1.5 comparison_guidance

**⚠️ This field does not exist in the canonical schema.** The concept is addressed across multiple related fields:
- `Methodology.vs_similar_methods` and `Methodology.differentiating_characteristics` — on the methodology entity (not on the resource)
- `ResourceSubtype.software.comparable_tools` [AUTO — AI-authored]
- Article subtype: `methodology_comparison` as a subtype code (not a field)

No field called `comparison_guidance` exists anywhere in the canonical schema. Any system built to populate it would need a schema addition or a mapping decision. **Decision required [HUMAN].**

---

## 2. CLASSIFICATION

### 2.1 Import Pipeline Classifier

Source: `cothesis_macmini_collected/cothesis_compendium_build_spec.md` §13 Stage 3

**Component:** `compendium-import-classify` | Queue job type: `import.classify`

**LLM routing:** LiteLLM → GLM-4.5-flash (free tier)

**Inputs to classifier:**
- Parsed import record (title, url, description, authors, etc.)
- Context: "medical research trainee audience"

**Outputs from classifier:**

| Output Field | Description |
|---|---|
| `resource_type` | One of 14 canonical type codes |
| `subtype` | One of 62 canonical subtype codes |
| `methodology_tags[]` | Methodology codes from 162-methodology taxonomy |
| `relevance_score` | 0–1 float: relevance to medical research trainees |
| `confidence` | 0–1 float: classifier confidence |
| `access_type` | One of 6 access type enum values |
| `skip_reason` | Why this is not a discrete citable resource (if applicable) |

**Routing logic based on thresholds:**

| Condition | Action |
|---|---|
| `relevance ≥ 0.6 AND confidence ≥ 0.8` | [AUTO] Auto-accept → enqueue Stage 4 |
| `relevance < 0.3 AND confidence ≥ 0.8` | [AUTO] Auto-exclude |
| Anything else | [REVIEW] → `review_needed` → Payload admin ImportCandidates queue |

**Environment variable overrides:**

```
IMPORT_RELEVANCE_AUTO_ACCEPT=0.6
IMPORT_RELEVANCE_AUTO_EXCLUDE=0.3
IMPORT_CONFIDENCE_AUTO_ACCEPT=0.8
IMPORT_CONFIDENCE_REVIEW=0.5
IMPORT_CLASSIFY_CONCURRENCY=4
```

**⚠️ No CLASSIFIER_SYSTEM_PROMPT found.** No verbatim prompt text appears in any project file. The pipeline stages are described by inputs, outputs, and thresholds — but the actual prompt is undefined.

### 2.2 AI Assessment Classifier (Post-Enrichment)

Source: `schema_entity_AIAssessment.canonical.md`

This is a separate, later-pipeline classification from the import classifier. It runs as part of the three-agent quality assessment pipeline and produces fields on `AIAssessment`:

| AIAssessment Field | Provenance | Distinction from Resource field |
|---|---|---|
| `relevance_to_methodology_codes` | [AUTO] AI-assessed | Stored on AIAssessment only. Human must ratify → `Resource.methodology_codes` |
| `relevance_to_discipline_codes` | [AUTO] AI-assessed | Stored on AIAssessment only. Human ratifies → `Resource.discipline_codes` |
| `thesis_stage_signals` | [AUTO] AI-assessed | Signals only. Human ratifies → `Resource.stage_codes` |
| `ai_subtype_signal` | [AUTO] AI-assessed | Ephemeral signal. Distinct from `Resource.resource_subtype_code` FK |
| `proposed_badges` | [AUTO] AI-proposed | Human ratification → `Resource.editorial.editorial_badges` |

### 2.3 Taxonomy Binding Rules

Source: `schema_entity_Resource.canonical.md`, `schema_taxonomy_resource_type_taxonomy.canonical.md`

- **Methodology codes** bind to `Methodology.code` from the 162-methodology taxonomy. [REVIEW] AI proposes on AIAssessment, human ratifies on Resource.
- **Discipline codes** bind to `ProfessionalDiscipline.code`. Renders as "Specialty" in Compendium medical presentation layer. Empty array = universal (not specialty-specific).
- **Stage codes** must be one of: `TH` \| `HI` \| `EV` \| `ST` \| `IN` \| `SH` (migration 08 renamed from longer forms).
- **Resource types** bind to 14 canonical ResourceType codes.
- **Subtypes** bind to 62 canonical ResourceSubtype codes (taxonomy v2.2). Two-step validation: subtype must (a) exist in ResourceSubtype AND (b) have a `type_code` matching `Resource.resource_type_code`.
- **46-agent-type → 14-UX-type mapping** documented in `schema_taxonomy_resource_type_taxonomy.canonical.md`. Examples:
  - `seminal_paper` → type: `article`, subtype: `seminal_paper`
  - `reporting_guideline` → type: `reporting_guideline`, subtype: `primary_guideline`
  - `wellbeing_resource` → assign by format; tag: `wellbeing`

### 2.4 Human Ratification of AI Classification Tags

Source: `schema_entity_Resource.canonical.md` Notes section

"The human-ratified values are on Resource.methodology_codes [and discipline_codes]. The AI assessment pipeline also produces methodology and discipline tags; these are stored on AIAssessment as `relevance_to_methodology_codes` and `relevance_to_discipline_codes`. They are distinct fields with distinct authorship."

Firm two-track model:
- **Track A (AI):** Tags on AIAssessment — provisional, automatically generated, not displayed to users
- **Track B (Human):** Tags on Resource — ratified, displayed, FK-validated against taxonomy

[REVIEW] for all classification fields: the agent populates the AIAssessment track; a human reviewer signs off before the Resource track is written.

---

## 3. QUALITY RATINGS / APPRAISAL

### 3.1 Quality Score

Source: `schema_entity_AIAssessment.canonical.md`, `schema_entity_Resource.canonical.md`, `cothesis_macmini_collected/cothesis_compendium_build_spec.md`

- **Scale:** 0–100. ⚠️ Earlier documents used 0–1; canonical wins. Migration: multiply × 100.
- **Computed by:** Three-agent AI pipeline (see §3.2). Stored on AIAssessment.
- **Denormalised to:** `Resource.quality_score` — updated when a new AIAssessment is created.
- **Display:** 5-segment indicator (`cmp-quality-bar`). `filledSegs = Math.round((quality_score / 100) * 5)`.
- **Hidden entirely if:** `quality_score < 60`.

**Routing thresholds (from `schema_entity_AIAssessment.canonical.md`):**

| Score Range | Outcome |
|---|---|
| ≥ 80 | [AUTO] Auto-approve |
| 60–79 | [REVIEW] Human review queue |
| < 60 | [AUTO] Auto-reject |
| `ai_confidence < 0.7` (any score) | [REVIEW] Forces human review regardless |

### 3.2 Three-Agent Assessment Pipeline

Source: `schema_entity_AIAssessment.canonical.md`

"The three-agent AI pipeline (Primary Assessor → Reviewer → Synthesis/Arbitrator, Z.AI GLM-4.6) writes one AIAssessment record per run."

| Agent | Role | Output |
|---|---|---|
| Primary Assessor | Initial quality assessment across all dimensions | Per-dimension scores, initial quality_score |
| Reviewer | Independent second-pass assessment | Validation or challenge of Primary scores |
| Synthesis/Arbitrator | Combines Primary + Reviewer outputs | Final `quality_score`, `ai_confidence`, all AIAssessment fields |

Agents are linked via `pipeline_run_id`. **⚠️ No per-agent prompts, role definitions, or per-agent rubric found in any file** — the three-agent structure is named but not specified.

### 3.3 Quality Dimensions

Source: `schema_entity_AIAssessment.canonical.md`, `cothesis_macmini_collected/compendium_content_types_reference.md`

`AIAssessment.quality_dimensions` is a JSON object of per-dimension sub-scores.

**Core dimensions (all subtypes):**
`relevance`, `accuracy`, `authority`, `currency`, `accessibility`, `practical_utility`

**Article-only dimension:**
`ebm_level` (evidence-based medicine level, populated from `article.ebm_level`)

**Extended dimensions by subtype (from `compendium_content_types_reference.md`):**

| Dimension | Subtypes |
|---|---|
| `pedagogy` | course, video |
| `production_quality` | video, podcast |
| `usability` | software, course |
| `functionality` | software |
| `documentation` | software |
| `support` | software, community |
| `value` | software, course, funding |
| `maintenance` | software |
| `adoption` | software, reporting_guideline |
| `specificity` | reporting_guideline, template |
| `interactivity` | course |
| `provenance` | dataset |
| `size` | dataset |
| `activity` | community |
| `expertise_level` | community |
| `responsiveness` | community |
| `visual_clarity` | visual_reference |
| `design_quality` | visual_reference |
| `completeness` | web_guide, book |
| `depth` | book, web_guide |
| `credibility` | web_guide |
| `prestige` | funding |
| `amount` | funding |

**⚠️ Dimension weighting and aggregation formula not defined in any file.** The build spec says the pipeline "computes a `quality_score` (0–100) using a weighted rubric that varies by type" but gives no weights or formula.

### 3.4 difficulty_level

Source: `schema_entity_Resource.canonical.md`, `schema_entity_AIAssessment.canonical.md`, `schema_entity_ResourceSubtype.software.canonical.md`

- **Values:** `beginner` \| `intermediate` \| `advanced`
- **Two distinct fields:**
  - `AIAssessment.difficulty_level` [AUTO] — AI's independent assessment of how hard it is to use/consume
  - `Resource.difficulty_level` [REVIEW] — the ratified value after human review
- **Software-specific note (verbatim from canonical file):** "`skill_level_required` is the tool's stated requirement; `difficulty_level` on AIAssessment is the AI's independent assessment of how hard it is to use — these can differ."
- **⚠️ Derivation rules not defined in any file.** [INFERRED: derived from content analysis of the resource, intended audience signals, prerequisite language, and technical depth indicators.]

### 3.5 source_authority Tiers

Source: `schema_entity_Resource.canonical.md`, `current_directory/cothesis_resource_directory_schema.md` §3.4

- **Values:** `tier_a` \| `tier_b` \| `tier_c`
- **Meaning (from older v1.0 spec — only available definition):**
  - `tier_a` — definitive reference
  - `tier_b` — useful supplement
  - `tier_c` — niche/secondary
- **⚠️ No assignment criteria defined in any canonical file.** Who assigns it, on what basis, and by what rubric is unspecified.

### 3.6 trainee_suitability_score

Source: `schema_entity_AIAssessment.canonical.md`

- **Type:** number (0-100)
- **Definition:** "AI-assessed suitability for trainees specifically." Distinct from `quality_score`.
- [AUTO] generated by assessment pipeline
- **⚠️ No rubric, derivation rules, or weights defined in any file.**

### 3.7 EBM Evidence Level (Article-only)

Source: `schema_entity_ResourceSubtype.article.canonical.md`

- **Field:** `article.ebm_level`
- **Values (examples from file):** `1a`, `2b`, `RCT`, `systematic_review`
- **Feeds:** `AIAssessment.quality_dimensions.ebm_level`
- **Source:** [AUTO] source-ingested from publisher metadata, or [AUTO] AI-classified from abstract/study_type
- **⚠️ No complete enum or assignment rubric defined in any file.**

---

## 4. QUALITY CONTROL / REVIEW WORKFLOW

### 4.1 Resource States: editorial_status

Source: `schema_entity_Resource.canonical.md`, `schema_layer_compendium.layer.md`

| Enum Value | Display Label (Compendium Layer) | Meaning |
|---|---|---|
| `proposed` | "AI Reviewing" (layer) / "Under Review" (field override — inconsistency) | Resource identified; pending assessment |
| `in_review` | "Under Editorial Review" | In human editorial queue |
| `published` | "Published" | Live and visible on Compendium |
| `archived` | "Archived" | Removed from active view; preserved |
| `deprecated` | "Deprecated" | Superseded; preserved for reference |

**Superseded values** (from `cothesis_resource_directory_schema.md` v1.0 — no longer canonical): `pending`, `approved`, `archived`, `flagged`.

### 4.2 Pipeline States (import_candidates table)

Source: `cothesis_macmini_collected/cothesis_compendium_build_spec.md` §13

| State | Set By | Trigger |
|---|---|---|
| `parsed` | [AUTO] Parse worker | File successfully read; `import_candidates` record created |
| `duplicate` | [AUTO] Dedup worker | Duplicate match found by any of 5 methods |
| `review_needed` | [AUTO] Classify worker | Relevance or confidence below auto-accept threshold |
| `enrichment_queued` | [AUTO] Accept worker | Auto-accept OR manual human approval |
| `human_accepted` | [HUMAN] Payload admin API | Reviewer approves a `review_needed` candidate |
| `human_rejected` | [HUMAN] Payload admin API | Reviewer rejects a candidate |

**Neo4j CompendiumResource node statuses:** `pending_enrichment` → `enriched` → `draft`

**Payload resource-editorial collection statuses:** `ai_draft` → `review_ready` → `published`

### 4.3 State Transition Diagram

```
[File/API Input]
       ↓
   [Parse] → status: parsed
       ↓
   [Dedup] → duplicate? → status: duplicate (dead end)
       ↓ (not duplicate)
  [Classify]
    ↙            ↓             ↘
auto-accept  review_needed  auto-exclude
    ↓               ↓
 [Accept]     [Human Review]
    ↓            ↙      ↘
[Enrich]    accepted   rejected
    ↓           ↓
[Neo4j: pending_enrichment → enriched]
    ↓
[Three-Agent AI Assessment]
    ↓                    ↓                     ↓
 score ≥80          score 60-79            score <60
[AUTO approve]    [REVIEW human]         [AUTO reject]
    ↓                   ↓
[Payload CMS: ai_draft → review_ready → published]
    ↓                              ↓
[Resource.editorial_status]   [Human signs off]
 proposed → in_review → published → archived/deprecated
```

### 4.4 Auto-Accept Conditions

Source: `cothesis_macmini_collected/cothesis_compendium_build_spec.md`, `schema_entity_AIAssessment.canonical.md`

**Import classification stage [AUTO]:**
- `relevance_score ≥ 0.6 AND confidence ≥ 0.8`

**AIAssessment quality stage [AUTO]:**
- `quality_score ≥ 80 AND ai_confidence ≥ 0.7`

### 4.5 Human Review Triggers

Source: `schema_entity_AIAssessment.canonical.md` (`requires_human_review` field definition)

**`AIAssessment.requires_human_review = true` when any of:**
- `ai_confidence < 0.7` (regardless of quality score)
- `quality_score` in range 60–79

**Import stage review triggers:**
- `relevance OR confidence` below auto-accept threshold but not in auto-exclude range

**What a reviewer checks [INFERRED from Payload CMS structure in build spec]:**
- AI Assessment tab: `aiDraftDescription`, `aiAssessmentNotes`, proposed classification fields, proposed badges
- Editorial tab: finalise `editorialDescription`, confirm or override classification tags, confirm `editorial_status`
- [HUMAN] Accept or reject `proposed_badges` → writes to `Resource.editorial.editorial_badges`
- [HUMAN] Confirm or override `methodology_codes`, `discipline_codes`, `stage_codes`
- [HUMAN] Set `editorial_note` if resource is to be `featured`
- [HUMAN] Set `source_authority` tier

### 4.6 Deduplication Rules

Source: `cothesis_macmini_collected/cothesis_compendium_build_spec.md` §13 Stage 2

Five-method check, in order:

| Method | Matching Criterion |
|---|---|
| 1. Exact URL match | `url = incoming_url` |
| 2. Normalised URL match | URL normalisation (scheme, trailing slash, utm params stripped) |
| 3. DOI match | `doi = incoming_doi` (where doi is non-null) |
| 4. ISBN match | `isbn_13 = incoming_isbn` (book subtype) |
| 5. Title fuzzy match | Levenshtein similarity ≥ 0.92 |

All five methods [AUTO]. If duplicate found → status: `duplicate` (dead end).

**⚠️ No conflict resolution rule defined.** If a duplicate is found but the incoming record has fresher metadata, the spec does not define whether to update the existing record or silently drop. [INFERRED: drop and log.]

### 4.7 Freshness Verification

Source: `current_directory/cothesis_resource_directory_schema.md` §6

> ⚠️ This table is from the superseded v1.0 spec. No canonical freshness threshold table exists in `project_upload/`. Values carry forward [INFERRED] pending canonical update.

| Resource Type | Verification Interval |
|---|---|
| software | 90 days |
| dataset | 90 days |
| funding | 90 days |
| preprint | 90 days |
| course | 120 days |
| article | 180 days |
| reporting_guideline | 180 days |
| template | 180 days |
| video | 180 days |
| podcast | 180 days |
| web_guide / web_resource | 180 days |
| community | 180 days |
| book | 365 days |

`Resource.freshness_flag` = `fresh` \| `stale` \| `expired`. Auto-derived from `last_verified` against above thresholds. [AUTO]

### 4.8 Publication Validation Gates

Source: `schema_entity_Resource.canonical.md`

Required fields before `editorial_status` can be set to `published`:

| Field | Condition |
|---|---|
| `resource_id`, `code` | Always required |
| `resource_type_code` | Always required |
| `title` | Always required |
| `access_type` | Always required |
| `last_verified` | Always required |
| `slug`, `has_page`, `is_active`, `phase` | Page mixin — required |
| `editorial_description` | Required for `reviewed` and `featured` tiers |
| `editorial_note` | Required for `featured` status only |

**Immutability rule (verbatim from build spec):** "Once status = `published`, pipeline workers must never overwrite `editorialDescription`, `badges`, or `qualityScore`."

**⚠️ No comprehensive gate checklist beyond the above found in any file.** Undefined: minimum `quality_score` for publish, `methodology_codes` completeness requirements, freshness staleness blocking, what constitutes "reviewed tier" vs "featured tier" vs base tier.

---

## 5. EDITORIAL DESCRIPTION

### 5.1 What It Is

Source: `schema_entity_Resource.canonical.md`, `cothesis_macmini_collected/compendium_content_types_reference.md`

- **Field:** `Resource.editorial_description`
- **Type:** string
- **Mandatory for publish:** Yes, for reviewed and featured tiers. [INFERRED: required for all published resources per Notes section.]
- **Rule:** Never copied from source. Editorial-independence rule.
- **Distinct from:**
  - `Resource.description` — publisher-supplied (abstract, tagline)
  - `AIAssessment.summary` — AI-generated long form
  - `editorial_note` — "why this matters" (human only, featured only)

**Length:**
- Field table (canonical): 1–2 sentences
- Older v1.0 spec: 2–3 sentences
- `compendium_content_types_reference.md`: ≤ 3 sentences
- No explicit character limit stated in any file.

### 5.2 Authorship (⚠️ Contradiction)

Three conflicting statements in the canonical files:

| Source Location | Statement |
|---|---|
| `Resource.canonical.md` field table | "CoThesis-authored 1–2 sentence summary. Never copied from source." |
| `Resource.canonical.md` Notes section | "editorial_description = AI-authored factual summary of what the resource is (required for all published resources)." |
| `AIAssessment.canonical.md` Notes | "`editorial_description` on Resource is CoThesis-editorial-authored and 'never copied from source'" |

**Operational resolution (from Payload CMS structure in build spec):**
- `aiDraftDescription` (AI Assessment tab) — AI generates a draft [AUTO]
- `editorialDescription` (Editorial tab) — human reviewer edits/finalises [REVIEW]
- Status flow: `ai_draft` → `review_ready` → `published`

**[INFERRED resolution]:** AI drafts → [REVIEW] human finalises. The field is "CoThesis-authored" in the sense that a human must ratify it before publish. The Notes' "AI-authored" language describes the draft state only and is erroneous in context.

**Decision required [HUMAN]:** Confirm this interpretation and update the canonical Notes to remove the contradiction.

### 5.3 Voice, Style, and Audience

Source: `compendium_content_types_reference.md`, general project context

- **Audience:** Research-naive medical trainees (stated throughout; explicit in `schema_layer_medical.layer.md` and classifier context)
- **Voice:** "Original prose" (`compendium_content_types_reference.md`). No further style guide found in any file.
- **Content:** Factual summary of what the resource is. Not evaluative (that's `editorial_note`).
- **Prohibited:** Copying from source description.

**SEO derivation:** `meta_description` (≤160 chars) is derived from `editorial_description`. `short_description` (≤80 chars) is a further derived variant.

### 5.4 Prompt / Template

**⚠️ No verbatim prompt, template, or style guide found for editorial_description generation in any project file.** The only operational definition is the pipeline component `AI_DESCRIBE` = "Z.AI / Ollama description generation — Original description writing."

**Decision required [HUMAN]:** Write and validate the AI_DESCRIBE prompt before enrichment pipeline build.

---

## 6. PIPELINE END TO END

Source: `cothesis_macmini_collected/cothesis_compendium_build_spec.md` §13–14, `current_directory/data_sources_by_resource_type.md`

### 6.1 Input Channels

| Channel | Method |
|---|---|
| Google Drive watch | n8n automation monitors a Drive folder; files trigger import |
| APISIX API endpoint | `POST internal-host:9066/compendium/import` |
| CLI tool | `pnpm pipeline:import <file>` |

Accepted input formats: JSON, CSV, Markdown table (Manus/Gemini output format)

### 6.2 Full Pipeline Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: PARSE                            [AUTO]                 │
│ Component: compendium-import-parse                               │
│ Queue: import.parse (BullMQ + Redis)                             │
│ Action: Read JSON/CSV/MD → create import_candidates records      │
│ State → parsed                                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: DEDUPLICATE                      [AUTO]                 │
│ Component: compendium-import-dedup                               │
│ Queue: import.dedup                                              │
│ Action: 5-method check (exact URL, normalised URL, DOI, ISBN,    │
│         title fuzzy match Levenshtein ≥ 0.92)                    │
│ State → duplicate (dead end) OR proceed to classify              │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: CLASSIFY                     [AUTO] routing            │
│ Component: compendium-import-classify                            │
│ Queue: import.classify                                           │
│ LLM: LiteLLM → GLM-4.5-flash                                    │
│ Outputs: resource_type, subtype, methodology_tags[],             │
│          relevance_score (0-1), confidence (0-1), access_type    │
│ State → enrichment_queued (auto) / review_needed [REVIEW]        │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: ACCEPT                       [AUTO] or [HUMAN]          │
│ Component: compendium-import-accept                              │
│ Queue: import.accept                                             │
│ Action: Create Neo4j CompendiumResource node                     │
│         (status: pending_enrichment)                             │
│         Write compendium.resource_provenance record              │
│         Enqueue to enrichment queue                              │
│ State → enrichment_queued                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: ENRICH                           [AUTO]                 │
│ Component: src/pipeline/enrichment/runner.ts                     │
│ Reads: compendium.enrichment_queue                               │
│ Dispatches: per-type enricher (article.ts, book.ts, etc.)       │
│                                                                  │
│ article → PubMed, Crossref, Semantic Scholar, Unpaywall          │
│ book    → Google Books API, OpenLibrary, Crossref                │
│ video   → YouTube Data API v3                                    │
│ podcast → iTunes Search API, Listen Notes API, RSS               │
│ software→ GitHub API, web scrape                                 │
│ rg      → EQUATOR Network scrape                                 │
│ course  → provider APIs, web scrape                              │
│ dataset → DataCite REST API, Zenodo API                          │
│ community, funding → web scrape                                  │
│                                                                  │
│ Computes: quality_score per type-specific weighted rubric        │
│ Updates: Neo4j node → status: enriched                           │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: AI ASSESSMENT (Three-Agent Pipeline)                    │
│ LLM: Z.AI GLM-4.6                                               │
│ Agents: Primary Assessor → Reviewer → Synthesis/Arbitrator       │
│ Writes: One AIAssessment record per run (linked via pipeline_id) │
│ Outputs: quality_score, ai_confidence, quality_dimensions,       │
│   proposed_badges, relevance_to_methodology_codes,               │
│   relevance_to_discipline_codes, thesis_stage_signals,           │
│   difficulty_level, summary, strengths, limitations,             │
│   trainee_suitability_score, language_detected                   │
│                                                                  │
│ Routes:                                                          │
│   score ≥80, confidence ≥0.7 → [AUTO] approve                   │
│   score 60-79 OR confidence <0.7 → [REVIEW] human queue          │
│   score <60 → [AUTO] reject                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: EDITORIAL REVIEW             [REVIEW] + [HUMAN]         │
│ System: Payload CMS 3                                            │
│ Collection: resource-editorial                                   │
│ Status flow: ai_draft → review_ready → published                 │
│                                                                  │
│ AI Assessment tab (pre-populated by pipeline):                   │
│   aiDraftDescription, aiAssessmentNotes, proposed               │
│   classifications, proposed badges, quality scores               │
│                                                                  │
│ Editorial tab (human fills):                                     │
│   editorialDescription (finalise from AI draft)                  │
│   editorial_note (required for featured)                         │
│   editorial_badges (ratify from proposed_badges, max 3)          │
│   methodology_codes, discipline_codes, stage_codes (confirm)     │
│   source_authority (tier_a/b/c)                                  │
│   difficulty_level (ratify AI assessment)                        │
│                                                                  │
│ Immutability: once published, pipeline never overwrites          │
│   editorialDescription, badges, or qualityScore                  │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: PUBLISH                          [AUTO] post-approval   │
│ Resource.editorial_status → published                            │
│ Resource visible at /library/{subtype_slug}/{slug}               │
│ Embedding generated (Qdrant) for AI features                     │
│ Neo4j graph edges established                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Technology Stack

Source: `cothesis_macmini_collected/cothesis_compendium_build_spec.md`

| Layer | Technology |
|---|---|
| Queue | BullMQ + Redis |
| LLM gateway | LiteLLM |
| Import classification LLM | Z.AI GLM-4.5-flash (free tier) |
| Assessment LLM | Z.AI GLM-4.6 |
| Embeddings | Ollama nomic-embed-text |
| Primary graph store | Neo4j |
| Pipeline state | PostgreSQL (`compendium.*` schema) |
| Editorial CMS | Payload CMS 3 (`payload.*` schema) |
| Vector store | Qdrant (AI features, future) |

### 6.4 External Source Codes

Source: `current_directory/data_sources_by_resource_type.md`

All codes used in `field_provenance` JSON to identify data origin:

`CROSSREF`, `PUBMED`, `OPENALEX`, `SEMANTIC`, `UNPAYWALL`, `GBOOKS`, `OPENLIBRARY`, `YOUTUBE_API`, `YT_TRANSCRIPT`, `LISTENNOTES_API`, `ITUNES`, `SPOTIFY`, `RSS`, `ORCID`, `ROR`, `DOAB_API`, `OAPEN_API`, `NCBI_BOOKS`, `WAYBACK`, `FAVICON`, `AI_ASSESS`, `AI_CLASSIFY`, `AI_DESCRIBE`, `EMBEDDINGS`

---

## 7. GAPS AND OPEN QUESTIONS

### 7.1 ⚠️ CRITICAL: editorial_description authorship is contradicted three times

**Files:** `schema_entity_Resource.canonical.md` (field table, Notes) + `schema_entity_AIAssessment.canonical.md` Notes

- Field table: "CoThesis-authored" (human)
- Notes: "AI-authored factual summary"
- AIAssessment notes: "CoThesis-editorial-authored"
- Payload build spec: AI drafts (`aiDraftDescription`) → human finalises (`editorialDescription`)

**Decision required [HUMAN]:** Confirm the AI-draft-human-finalise model and update canonical Notes.

### 7.2 ⚠️ No verbatim prompt text for any AI stage

No CLASSIFIER_SYSTEM_PROMPT, no three-agent assessment prompts, no editorial_description generation prompt, no `AI_DESCRIBE` template exists in any project file. The pipeline stages are described by inputs, outputs, and thresholds only.

**Decision required [HUMAN]:** Write and test prompts for: (a) classification, (b) primary assessment, (c) reviewer, (d) synthesis/arbitration, (e) editorial_description generation.

### 7.3 ⚠️ comparison_guidance field does not exist

The field `comparison_guidance` does not appear in any canonical file, spec, or build document. Concept is partially addressed by `Methodology.vs_similar_methods`, `software.comparable_tools`, and the `methodology_comparison` article subtype.

**Decision required [HUMAN]:** Define whether this needs to be added as a new schema field, and if so where and how it is populated.

### 7.4 ⚠️ Quality dimension weights and aggregation formula undefined

`quality_score` (0-100) is described as derived from `quality_dimensions`, but no weighting formula, per-dimension weights, or aggregation method is defined anywhere.

**Decision required [HUMAN]:** Define per-dimension weights per resource type and the aggregation formula.

### 7.5 ⚠️ Three-agent pipeline agent roles undefined

The names exist (Primary Assessor, Reviewer, Synthesis/Arbitrator) but no per-agent instructions, constraints, or specific quality criteria are defined in any file.

**Decision required [HUMAN]:** Define per-agent roles and prompts.

### 7.6 ⚠️ source_authority tier criteria undefined

`source_authority = tier_a | tier_b | tier_c` with no assignment criteria in any canonical file. The older spec provides label names only (definitive / useful supplement / niche). No rubric for how to assign, whether AI can propose, or whether it's mandatory for publish.

**Decision required [HUMAN]:** Define tier criteria, assignment process (AI vs human), and publish requirements.

### 7.7 ⚠️ difficulty_level derivation rules undefined

Both `AIAssessment.difficulty_level` and `Resource.difficulty_level` exist with the enum `beginner | intermediate | advanced`, but no criteria for assignment are defined anywhere.

**Decision required [HUMAN]:** Define rubric for beginner/intermediate/advanced per resource type.

### 7.8 ⚠️ editorial_status duplicated at two schema levels

`editorial_status` appears both as a top-level field on Resource AND as a field inside `Resource.editorial` embedded object. The canonical file does not address this redundancy. Risk of divergence.

**Decision required [HUMAN]:** Which is authoritative? Should the embedded object version be removed?

### 7.9 ⚠️ Build spec subtypes diverge from taxonomy canonical

The build spec §7 uses subtype names `systematic_review`, `rct`, `cohort_study`, `case_report` under `article`. The canonical taxonomy uses: `seminal_paper`, `methodology_review`, `exemplar_study`, `methodology_comparison`, `research_article`, `review_article`, `preprint`, `editorial`, `guideline_article`. Completely different vocabularies — the build spec is using a pre-canonical subtype set and must be updated before implementation.

### 7.10 ⚠️ Freshness threshold table not in canonical files

Type-specific freshness intervals (90–365 days) exist only in the superseded v1.0 spec. No canonical freshness threshold table exists in `project_upload/`. Should be promoted to a canonical location.

### 7.11 ⚠️ OQ-RG-01 (OPEN): ReportingGuideline entity vs ResourceSubtype coexistence

Source: `schema_meta_open_questions.md`

"OQ-RG-01 — ReportingGuideline vs reporting_guideline ResourceSubtype coexistence. Recommend: coexist — Resource.reporting_guideline subtype links to ReportingGuideline.code via `reporting_guideline_code` field. Confirm with Dave." — STATUS: OPEN.

Affects enrichment: whether a reporting guideline resource links to a ReportingGuideline entity and how that relationship is maintained.

### 7.12 ⚠️ OQ-METHCAT-01 (OPEN): MethodCategory entity missing canonical

Source: `schema_meta_open_questions.md`

"OQ-METHCAT-01 — MethodCategory entity referenced by FoundationSkill.category_code='FS' but no canonical file exists. Until then, `category_code: 'FS'` on FoundationSkill is an unresolvable FK." Affects how `skill_codes` are validated during enrichment.

### 7.13 ⚠️ quality_score scale inconsistency in legacy data

Legacy records using 0-1 scale need migration (multiply × 100). Migration acknowledged in canonical notes but no migration script found in project files.

### 7.14 ⚠️ trainee_suitability_score rubric completely undefined

Field exists on AIAssessment (0-100), purpose stated, no criteria, dimensions, or weighting defined in any file.

### 7.15 ⚠️ Duplicate detection conflict resolution undefined

When deduplication finds a match, the pipeline sets `duplicate` status and stops. No rule exists for whether the incoming record's (potentially fresher) metadata should update the existing record's fields.

### 7.16 ⚠️ No comprehensive publication gate checklist

The spec requires `editorial_description` for reviewed/featured tiers and `editorial_note` for featured, but no single document lists all required fields for `editorial_status = published`. Undefined: minimum `quality_score` for publish, whether `methodology_codes` must be non-empty, whether freshness staleness blocks publish, what constitutes "reviewed tier" vs "featured tier" vs base tier.

---

*Specification grounded in project files as at audit date 2026-06-04. All contradictions and gaps flagged with ⚠️ and marked as requiring a decision. No requirements invented. All [INFERRED] items are explicitly tagged.*
