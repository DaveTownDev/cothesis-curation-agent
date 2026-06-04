# CoThesis Compendium — Enrichment, Classification & Quality Specification
**Date:** 2026-05-29  
**Grounded in:** source code, SQL schemas, docs, Payload collections  
**Purpose:** Multi-agent enrichment system design reference

Tag key: **[AUTO]** fully automatable · **[REVIEW]** agent drafts, human approves · **[HUMAN]** human judgement required

---

## 1. ENRICHMENT — Complete Field Inventory

### 1.1 Pipeline Write Target

All enrichment workers write to **Neo4j** `CompendiumResource` node properties via `SET r += $props`. There is also a **PostgreSQL** canonical `compendium.resource` table defined in `schema_reference_data.sql` but it is **⚠️ not yet populated by the pipeline** (noted in `BUILD_SPEC.md`: "P0 — keystone table, not yet populated by pipeline").

Source: `src/pipeline/enrichment/*.ts`, `src/pipeline/schema_reference_data.sql`

---

### 1.2 Universal Fields (written by every enrichment worker)

Every resource type receives the following fields, sourced from `assessResource()` in `src/pipeline/lib/litellm.ts`:

| Field | Type | Source | Mandatory for publish | Notes |
|---|---|---|---|---|
| `editorial_description` | string | assessor LLM | **[AUTO]** Yes | 1–2 sentences, accessible to medical trainees |
| `editorial_description_long` | string | assessor LLM | **[AUTO]** No | 3–5 sentences |
| `quality_score` | number | assessor LLM | **[AUTO]** Yes | 0.0–1.0 in `AssessorResult`; ⚠️ **inconsistency: schema defines 0.0–100.0** |
| `quality_dimensions` | JSON string | assessor LLM | **[AUTO]** No | See §3 for schema |
| `methodology_tags` | string[] | assessor LLM (may override classify tags) | **[AUTO]** Yes | CoThesis prefix codes |
| `thesis_stages` | string[] | assessor LLM | **[AUTO]** Yes | THESIS codes: TH/HI/EV/ST/IN/SH |
| `specialty_tags` | string[] | assessor LLM | **[AUTO]** No | Medical specialty slugs, max 3 |
| `difficulty_level` | string | assessor LLM | **[AUTO]** No | beginner / intermediate / advanced |
| `editorial_badges` | string[] | assessor LLM | **[AUTO]** No | Max 3; see §3 for allowed values |
| `requires_human_review` | boolean | assessor LLM | **[AUTO]** flag | True → ⚠️ **no defined workflow to act on this flag** |
| `subtype` | string | assessor LLM | **[AUTO]** No | Type-specific subtype string |
| `confidence` | number | assessor LLM | internal only | 0.0–1.0; not written to Neo4j (discarded) |
| `status` | string | enrichment runner | **[AUTO]** | Set to `enriched` on success, `enrichment_failed` on total failure |
| `compendium_updated_at` | datetime | enrichment runner | **[AUTO]** | Set on every update |
| `lastVerified` | datetime | runner post-hook | **[AUTO]** | Set by `setFreshnessFlag()` after enrichment |
| `freshness_flag` | string | runner post-hook | **[AUTO]** | Logic: funding→`check`; article/book >5yr old→`stale`; software >2yr old→`stale`; else null |

Source: `src/pipeline/lib/litellm.ts` (AssessorResult interface, ASSESSOR_SYSTEM_PROMPT), `src/pipeline/enrichment/runner.ts` (setFreshnessFlag, markFailed)

---

### 1.3 Per-Resource-Type Field Inventory

#### article

**API sources:** PubMed (XML), CrossRef, OpenAlex, Unpaywall, iCite, Altmetric  
**Failure condition:** All three primary sources (PubMed + CrossRef + OpenAlex) fail → `enrichment_failed`

| Field | Source | Priority/Merge rule |
|---|---|---|
| `title` | known_fields → PubMed → CrossRef | First non-null |
| `abstract` | PubMed → CrossRef → OpenAlex | First non-null |
| `journal_name` | PubMed → CrossRef container_title | First non-null |
| `journal_abbreviation` | PubMed → CrossRef | First non-null |
| `publication_year` | CrossRef → PubMed → OpenAlex | First non-null |
| `doi` | CrossRef → OpenAlex ID → input doi | First non-null |
| `pmid` | input → PubMed response | First non-null |
| `url` | derived from DOI: `https://doi.org/{doi}` | — |
| `citation_count` | max(OpenAlex, CrossRef, iCite) | Highest value wins |
| `is_open_access` | Unpaywall → OpenAlex | First non-null |
| `oa_status` | Unpaywall → OpenAlex | First non-null |
| `pdf_url` | Unpaywall → OpenAlex oa_url | First non-null |
| `authors` | union(PubMed authors, CrossRef authors) deduplicated | — |
| `mesh_terms` | PubMed only | — |
| `topics` | OpenAlex only | — |
| `is_retracted` | CrossRef or OpenAlex or PubMed retraction notice | Any true → true |
| `volume`, `issue`, `pages` | CrossRef → PubMed | — |
| `publisher` | CrossRef | — |
| `issn` | CrossRef | — |
| `language` | PubMed → CrossRef | — |
| `license` | Unpaywall → CrossRef | — |
| `reference_count` | CrossRef | — |
| `grant_ids` | PubMed | — |
| `fwci` | OpenAlex | — |
| `openalex_id` | OpenAlex | — |
| `relative_citation_ratio` | iCite | — |
| `nih_percentile` | iCite | — |
| `apt` | iCite | — |
| `altmetric_score` | Altmetric | — |
| `altmetric_score_1y` | Altmetric | — |
| `altmetric_id` | Altmetric | — |

Source: `src/pipeline/enrichment/article.ts`

---

#### book / book_chapter

**API sources:** ISBNdb, Google Books, OpenLibrary, Springer, CrossRef, OpenAlex  
**Failure condition:** No source returns data → `enrichment_failed`

| Field | Source |
|---|---|
| `title`, `authors`, `publisher`, `publication_year` | Merged from ISBNdb/Google Books/OpenLibrary/Springer |
| `description` | First 600 chars from best source |
| `page_count`, `language`, `cover_image_url` | ISBNdb/Google Books |
| `subjects`, `categories` | ISBNdb/Google Books |
| `is_open_access` | OpenAlex |
| `isbn`, `isbn_13` | ISBNdb |
| `doi`, `citation_count`, `openalex_id` | CrossRef/OpenAlex |
| `chapter_title`, `book_title`, `page_start`, `page_end` | book_chapter only |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/book.ts`

---

#### software

**API sources:** GitHub API, bio.tools API, Crawl4AI (web scrape for pricing/platforms)

| Field | Source |
|---|---|
| `github_full_name`, `github_description`, `github_stars`, `github_forks`, `github_open_issues`, `github_watchers`, `github_language`, `github_topics`, `github_is_archived`, `github_last_commit`, `github_created_at` | GitHub |
| `license`, `license_name`, `homepage`, `latest_release_tag`, `latest_release_date` | GitHub |
| `biotools_id`, `name`, `description`, `language`, `maturity`, `edam_topics`, `edam_operations`, `publication_dois`, `operating_system` | bio.tools |
| `scraped_pricing_hint`, `scraped_platforms`, `scraped_text_length` | Crawl4AI |
| `oss_health_signal` | Derived: github_last_commit age |
| `access_type` | assessor (overrides classify) |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/software.ts`

---

#### web_guide / template / visual_reference

**API sources:** Crawl4AI (primary); protocols.io for templates; Figshare for visual_reference

| Field | Source |
|---|---|
| `title`, `description`, `featured_image_url`, `site_name` | Crawl4AI |
| `author_name`, `publication_date`, `publication_year`, `word_count`, `reading_time_minutes` | Crawl4AI |
| `template_format`, `free_download_available`, `download_url`, `download_format`, `issuing_body`, `version`, `version_date`, `jurisdiction`, `aligned_guideline_name` | Crawl4AI / template-specific |
| `doi`, `view_count`, `step_count`, `fork_count`, `is_peer_reviewed` | protocols.io (template only) |
| `image_width`, `image_height`, `slide_count`, `figshare_id`, `defined_type_name`, `creator_names`, `categories`, `license`, `download_count` | Figshare (visual_reference only) |
| + all universal fields | assessResource() |

**Note:** web_guide.ts handles all three types (web_guide, template, visual_reference) by detecting resource_subtype. Source: `src/pipeline/enrichment/web_guide.ts`, `src/pipeline/enrichment/template.ts`, `src/pipeline/enrichment/visual_reference.ts`

---

#### reporting_guideline

**API sources:** Crawl4AI, CrossRef

| Field | Source |
|---|---|
| `title`, `acronym`, `checklist_url`, `pdf_url`, `version_year`, `target_study_type`, `publisher`, `abstract` | Crawl4AI |
| `doi` | CrossRef |
| `guideline_type` | assessor (assessment.subtype) |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/reporting_guideline.ts`

---

#### course

**API sources:** Crawl4AI only

| Field | Source |
|---|---|
| `title`, `description`, `course_image_url`, `instructor_names`, `institution_name` | Crawl4AI |
| `duration_weeks`, `effort_hours_per_week`, `total_hours`, `level` | Crawl4AI |
| `platform_rating`, `platform_rating_count`, `is_free`, `audit_available`, `price`, `certificate_available` | Crawl4AI |
| `language`, `prerequisites`, `pacing`, `platform_name`, `platform_url` | Crawl4AI |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/course.ts`

---

#### video

**API sources:** YouTube Data API v3, Crawl4AI fallback

| Field | Source |
|---|---|
| `title`, `description`, `channel_name`, `channel_id`, `published_date`, `publication_year`, `tags`, `language` | YouTube API |
| `duration_seconds`, `duration_display`, `thumbnail_url`, `thumbnail_small`, `definition`, `has_captions` | YouTube API |
| `view_count`, `like_count`, `comment_count`, `youtube_video_id`, `embed_url` | YouTube API |
| `engagement_ratio` | Derived: (likes+comments)/views |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/video.ts`

---

#### podcast

**API sources:** Crawl4AI, RSS feed parsing

| Field | Source |
|---|---|
| `title`, `description`, `thumbnail_url`, `site_name`, `rss_url` | Crawl4AI |
| `total_episodes`, `latest_episode_date`, `language`, `categories` | RSS |
| `is_active` | Derived: latest_episode_date within 3 months |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/podcast.ts`

---

#### dataset

**API sources:** Zenodo, OpenAlex, CrossRef/DataCite, Crawl4AI

| Field | Source |
|---|---|
| `title`, `description`, `publisher_repository`, `publication_year`, `license`, `access_type` | Best of Zenodo/CrossRef/Crawl4AI |
| `file_formats`, `citation_count`, `sample_size`, `creators` | Zenodo/Crawl4AI |
| `doi` | Zenodo/CrossRef |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/dataset.ts`

---

#### community

**API sources:** Reddit API, Stack Exchange API, Crawl4AI

| Field | Source |
|---|---|
| `name`, `description`, `member_count`, `active_users`, `platform_name`, `subreddit_name` | Reddit/Crawl4AI |
| `community_url`, `icon_url`, `membership_type`, `created_date`, `geographic_scope` | Crawl4AI |
| `newsletter_frequency`, `newsletter_subscribe_url` | Crawl4AI |
| `total_questions`, `total_answers`, `questions_per_minute` | Stack Exchange (if applicable) |
| `subtype_classification` | assessor (assessment.subtype) |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/community.ts`

---

#### funding

**API sources:** Crawl4AI, NIH Reporter API

| Field | Source |
|---|---|
| `programme_name`, `description`, `site_name`, `funder_name`, `funder_country` | Crawl4AI |
| `amount_min`, `amount_max`, `currency`, `application_deadline`, `application_frequency` | Crawl4AI |
| `career_stage`, `eligibility`, `success_rate`, `application_url`, `status` | Crawl4AI |
| `nih_project_number`, `nih_activity_code` | NIH Reporter |
| `subtype_classification` | assessor (assessment.subtype) |
| `freshness_flag` | Always set to `check` (hardcoded in runner.ts) |
| + all universal fields | assessResource() |

Source: `src/pipeline/enrichment/funding.ts`

---

### 1.4 Fields Defined in Schema But NOT Written by Current Enrichment Workers

The following fields exist in `compendium.resource` (PostgreSQL, `schema_reference_data.sql`) or are described in specs but have no confirmed write path in the current enrichment workers:

| Field | Defined in | Gap |
|---|---|---|
| `editorial_status` | schema_reference_data.sql: `'catalogued' \| 'reviewed' \| 'featured'` | No pipeline code writes this |
| `resource_status` (active/draft/archived/removed) | schema_reference_data.sql | No pipeline code writes this — Neo4j uses different status field |
| `compendium.resource` canonical table | schema_reference_data.sql | ⚠️ **Not populated by pipeline** — pipeline writes to Neo4j only |
| `assessment_status` | schema_reference_data.sql: `'pending \| running \| complete \| failed \| skipped'` | Not confirmed written by current workers |
| `last_assessed_at` | schema_reference_data.sql | Not confirmed written by current workers |
| `assessment_agent_version` | schema_reference_data.sql | Not confirmed written by current workers |
| `aiDraftDescription`, `aiAssessmentNotes`, `assessorModel`, `assessedAt` | ResourceEditorial Payload collection | Written to Payload CMS, not Neo4j — sync mechanism **undefined** |

---

## 2. CLASSIFICATION

### 2.1 Classifier Overview

**Model:** `compendium-classifier` — glm-4.5-flash via LiteLLM proxy  
**Concurrency:** 4 workers (default), rate-limited to 20 calls/60s  
**Location:** `src/pipeline/workers/classify.ts`

### 2.2 CLASSIFIER_SYSTEM_PROMPT (verbatim)

```
You are a resource classifier for a medical research training directory.
Given a resource's title, URL, and description, classify it for medical trainees doing research projects.

Respond with JSON only — no markdown, no explanation:
{
  "resource_type": one of [article, book, book_chapter, video, podcast, software, reporting_guideline, course, web_guide, template, visual_reference, dataset, community, funding],
  "subtype": string (specific subtype within the type),
  "methodology_tags": string[] (use ONLY CoThesis prefix codes from the list below — max 5, return [] if none apply),
  "thesis_stages": string[] (subset of THESIS phase codes: TH=Theory/question formulation, HI=History/literature, EV=Evaluate/planning+ethics, ST=Study/doing the research, IN=Interpret/analysis, SH=Share/writing+dissemination),
  "relevance_score": float 0-1 (relevance to medical trainees doing research),
  "relevance_reasoning": string (one sentence),
  "classification_confidence": float 0-1,
  "access_type": one of [free, freemium, paid, subscription, institutional],
  "skip_reason": null or string (if this is NOT a discrete citable resource — e.g. homepage, 404, generic department page),
  "specialty_tags": string[] (max 3 — medical specialty slugs if the resource is specific to a specialty; omit or use [] if it applies broadly across medicine. Use slugs from: psychiatry, cardiology, general-practice, emergency-medicine, surgery, internal-medicine, paediatrics, obstetrics-gynaecology, radiology, pathology, anaesthetics, oncology, neurology, dermatology, ophthalmology, orthopaedics, urology, ent, geriatrics, rheumatology, endocrinology, gastroenterology, respiratory, nephrology, haematology, infectious-diseases, immunology, public-health, sports-medicine, palliative-care, intensive-care, rehabilitation, psychiatry-child-adolescent, addiction-medicine),
  "difficulty_level": one of [beginner, intermediate, advanced] (for medical trainees: beginner = no prior research experience, advanced = assumes research background)
}

METHODOLOGY CODES — you MUST use these exact codes, never free text:
Research Study Design: RS-01 Systematic Review, RS-02 Meta-Analysis, RS-03 RCT, RS-04 Quasi-Experimental, RS-05 Cohort Study, RS-06 Case-Control, RS-07 Cross-Sectional Survey, RS-08 Case Report/Series, RS-09 Ecological Study, RS-10 Diagnostic Accuracy Study
Observational & Data Methods: OD-01 Retrospective Chart Review, OD-02 Registry/Database Study, OD-03 Secondary Data Analysis, OD-04 Biostatistics & Data Analysis, OD-05 Epidemiological Methods, OD-06 Clinical Audit & QI, OD-07 Health Economic Analysis, OD-08 Survey Design & Validation
Qualitative Research: QR-01 Qualitative Methods General, QR-02 Interviews & Focus Groups, QR-03 Thematic & Content Analysis, QR-04 Grounded Theory, QR-05 Ethnography & Observation, QR-06 Narrative Research, QR-07 Action Research
Evidence Synthesis (evidence review methodologies — NOT literature searching or appraisal skills; use FS-02/FS-04 for those): EI-03 Scoping Review, EI-04 Narrative Review, EI-05 Evidence-Based Practice, EI-06 Clinical Practice Guideline Development
Research Conduct: CR-01 Research Ethics & Governance, CR-02 Grant Writing & Funding, CR-03 Sample Size & Power Calculation, CR-04 Measurement & Instrument Development, CR-05 Clinical Trial Management, CR-06 Consent & Recruitment
Mixed Methods: MM-01 Mixed Methods Design, MM-02 Convergent Design, MM-03 Explanatory Sequential, MM-04 Exploratory Sequential
Foundation Skills (cross-cutting competencies — use FS codes for resources that directly teach these skills; do NOT use FS codes for resources that merely use a skill): FS-01 Project Management, FS-02 Literature Searching (database search strategy, MeSH, Boolean), FS-03 Literature Synthesis (evidence synthesis, narrative/thematic review), FS-04 Critical Appraisal (study quality assessment, bias, appraisal tools), FS-05 Research Ethics (HREC, consent, governance, integrity), FS-06 Quantitative Methods (quantitative study design foundations), FS-07 Qualitative Methods (qualitative research foundations), FS-08 Mixed Methods (combining QUAL+QUAN), FS-09 Statistical Literacy (interpreting statistics, p-values, confidence intervals), FS-10 Data Management (REDCap, FAIR data, data governance), FS-11 Research Software (R, SPSS, NVivo, Zotero, Covidence), FS-12 Academic Writing (scholarly writing, IMRaD, manuscript preparation), FS-13 Research Presentation (conference talks, posters, 3MT), FS-14 Research Dissemination (journal submission, open access, peer review process), FS-15 Supervision and Mentoring (supervisory relationships, feedback), FS-16 Grant Writing (funding applications, NHMRC, MRFF)
```

Source: `src/pipeline/workers/classify.ts`

---

### 2.3 Classification Routing Logic

From `src/pipeline/types.ts` (`routeCandidate()`) and `classify.ts`:

```
if (skip_reason set)                                    → auto_exclude
if (confidence ≥ 0.8 AND relevance ≥ 0.6)             → auto_accept
if (confidence ≥ 0.8 AND relevance < 0.3)             → auto_exclude
if (confidence < 0.5)                                  → review_needed
else                                                   → review_needed
```

**Default thresholds** (overridable via env vars):

| Threshold | Env var | Default |
|---|---|---|
| relevanceAutoAccept | `IMPORT_RELEVANCE_AUTO_ACCEPT` | 0.6 |
| relevanceAutoExclude | `IMPORT_RELEVANCE_AUTO_EXCLUDE` | 0.3 |
| confidenceAutoAccept | `IMPORT_CONFIDENCE_AUTO_ACCEPT` | 0.8 |
| confidenceReview | `IMPORT_CONFIDENCE_REVIEW` | 0.5 |
| titleSimilarity | `IMPORT_TITLE_SIMILARITY_THRESHOLD` | 0.9 |

Source: `src/pipeline/types.ts`

---

### 2.4 Fast-Path: Pre-Classified Resources

If `classified_type` is already set on the candidate (e.g. imported from Manus with explicit type), the LLM is skipped entirely. The resource is auto-accepted with `confidence=1.0` and `relevance=0.8` hardcoded.

---

### 2.5 LLM Retry Behaviour

1. First attempt with `temperature=0.1`
2. If JSON parse fails: retry once with `temperature=0` and explicit `Respond with valid JSON only.` appended
3. If second attempt fails: status set to `review_needed` with `review_notes='LLM classification failed — JSON parse error'`

---

### 2.6 Tag Validation

**specialty_tags:** Validated to array of non-empty strings, sliced to max 3. No canonical lookup against taxonomy nodes — **[INFERRED]** assumes slugs match Specialty nodes in Neo4j.

**difficulty_level:** If LLM returns value outside `['beginner', 'intermediate', 'advanced']`, defaults to `'intermediate'`.

**thesis_stages:** Normalized via migration map from legacy snake_case/Title case to two-letter THESIS codes (TH/HI/EV/ST/IN/SH). Source: `STAGE_MIGRATION` record in classify.ts.

---

### 2.7 Methodology Tag Code Mismatch ⚠️

**Critical inconsistency:** The classifier system prompt uses codes like `RS-01` (Systematic Review), `OD-01` (Chart Review), etc. These are the **Compendium display codes** (13-category scheme, `cothesis_compendium_category_cross_reference.md`). However, Neo4j methodology nodes use the **platform model codes** (SYN-01, OBS-01, EVAL-01, etc.) as confirmed by `seed-neo4j.ts` and live database queries.

| Classifier output | Actual Neo4j code | Mapping needed |
|---|---|---|
| RS-01 | SYN-01 (Narrative Systematic Review) | Yes |
| RS-04 | SYN-02 (Scoping Review) | Yes |
| OD-01 | OBS-01 (Retrospective Chart Review) | Yes |
| OD-06 | EVAL-01 (Standards-Based Clinical Audit) | Yes |

The `USES_METHODOLOGY` relationships in Neo4j therefore cannot be created correctly until the methodology_tags from the classifier are translated to platform codes — or the classifier prompt is updated to emit platform codes.

Source: `src/pipeline/workers/classify.ts` (SYSTEM_PROMPT), `cothesis_compendium_category_cross_reference.md`, live Neo4j queries

---

### 2.8 Foundation Skill Binding

The classifier assigns FS-01 through FS-16 codes (16 skills). The Neo4j taxonomy only has 16 FoundationSkill nodes (FS codes through FS-16). No FS codes appear in the classifier prompt up to FS-07 in `src/pipeline/schema_reference_data.sql` comments ("7 in classifier") but the actual classifier prompt has FS-01–FS-16.

**⚠️ Inconsistency:** setup.md says `pnpm neo4j:seed` seeds "11 FoundationSkill nodes" but `seed-neo4j.ts` queries `WHERE is_active = TRUE` — the actual count depends on Postgres data. Live Neo4j has 16 FoundationSkill nodes (confirmed).

---

### 2.9 External Classify Worker Gap

A **separate** classify worker exists at `/Users/dtownsend/dev/compendium/workers/compendium-import/` that uses an **old version** of the classifier prompt (snake_case thesis stages, old methodology codes, no specialty_tags or difficulty_level). This worker is responsible for classifying new pipeline imports and must be updated before importing new resources.

Source: `REMAINING_TASKS_PLAN.md` Block 2.1, `BUILD_RECONCILIATION.md`

---

## 3. QUALITY RATINGS / APPRAISAL

### 3.1 Assessor System Prompt (verbatim)

```
You are an editorial quality assessor for a medical research training resource directory.
Return ONLY a single JSON object (no prose, no markdown fences). Schema:
{
  "quality_score": number,              // 0.0–1.0 weighted quality
  "quality_dimensions": {
    "credibility": number,
    "relevance": number,
    "clarity": number,
    "currency": number,
    "practicality": number
  },
  "editorial_description": string,     // 1-2 sentences, accessible to medical trainees
  "editorial_description_long": string,// 3-5 sentences
  "methodology_tags": string[],        // from CoThesis 166-term taxonomy
  "thesis_stages": string[],           // THESIS phase codes: TH=Theory, HI=History, EV=Evaluate, ST=Study, IN=Interpret, SH=Share
  "difficulty_level": string,          // "beginner" | "intermediate" | "advanced"
  "specialty_tags": string[],          // medical specialty tags
  "editorial_badges": string[],        // max 3: from: Free Access, Open Access, Peer Reviewed, Seminal Work, Essential Reference, Editors Choice, Guideline Endorsed, High Impact, Beginner Friendly
  "subtype": string,                   // type-specific subtype
  "confidence": number,                // 0.0–1.0
  "requires_human_review": boolean     // flag if uncertain or sensitive
}
```

**Model:** `compendium-assessor` (via LiteLLM, `LITELLM_ASSESSOR_MODEL` env var, defaults to `glm-4.5-flash`)  
**Temperature:** 0  
**Max tokens:** 2000  
**Response format:** `json_object`

Source: `src/pipeline/lib/litellm.ts`

---

### 3.2 Quality Score

| Attribute | Value |
|---|---|
| Field name | `quality_score` |
| Scale in AssessorResult | **0.0–1.0** (float) |
| Scale in schema_reference_data.sql | **0.0–100.0** (FLOAT) |
| Scale in ResourceEditorial Payload | 0–100 (integer, `min: 0, max: 100`) |

**⚠️ Critical inconsistency:** The pipeline writes 0.0–1.0 values but the schema defines 0.0–100.0. The Payload ResourceEditorial collection also uses 0–100. No normalisation code found. This means all quality_score values in Neo4j are in the wrong range relative to the schema definition.

---

### 3.3 Quality Dimensions

**Assessor output (5 dimensions):**
```json
{
  "credibility": number,
  "relevance": number,
  "clarity": number,
  "currency": number,
  "practicality": number
}
```

**Schema definition (6 dimensions, different names):**
```
{relevance, accuracy, authority, currency, accessibility, practical_utility}
each dimension: {score: float, weight: float, reasoning: text}
```

**⚠️ Inconsistency:** The assessor outputs 5 dimensions with different names than the schema specifies. The schema expects `authority`, `accuracy`, `accessibility`, `practical_utility`; the assessor generates `credibility`, `clarity`, `practicality`. There is no mapping or translation between them. Stored as a JSON string in Neo4j (no structure enforcement).

Source: `src/pipeline/lib/litellm.ts` (AssessorResult), `src/pipeline/schema_reference_data.sql` (Layer 7 compendium.resource)

---

### 3.4 Editorial Badges

**Assessor prompt instructs model to pick from:**
```
Free Access, Open Access, Peer Reviewed, Seminal Work, Essential Reference, 
Editors Choice, Guideline Endorsed, High Impact, Beginner Friendly
```

**ResourceEditorial Payload collection defines (different set):**
```
essential, editors_choice, best_free, best_beginners, best_time_poor, expert_pick
```

**schema_reference_data.sql compendium.resource defines:**
```
editors_choice | best_free | best_for_beginners | evidence_based | widely_used | 
foundational | au_nz_focus | open_access
```

**⚠️ Three-way inconsistency.** The pipeline writes assessor-generated badges (human-readable strings with spaces) to Neo4j. These do not match the snake_case enum values used in the frontend or the schema. No normalisation code found.

---

### 3.5 Difficulty Level

| Location | Allowed values |
|---|---|
| `types.ts` ClassificationResult | `beginner \| intermediate \| advanced` |
| classify.ts validation | `beginner \| intermediate \| advanced` (defaults to `intermediate`) |
| litellm.ts AssessorResult | `beginner \| intermediate \| advanced` |
| ResourceEditorial Payload collection | `beginner \| intermediate \| advanced \| expert` |
| schema_reference_data.sql | `beginner \| intermediate \| advanced \| mixed` |

**⚠️ Inconsistency:** The pipeline only produces 3 values; Payload UI allows a 4th (`expert`); schema allows a different 4th (`mixed`). No `expert` or `mixed` will ever be written by the pipeline.

---

### 3.6 Freshness / Recency

Managed by `setFreshnessFlag()` in `src/pipeline/enrichment/runner.ts`:

| Condition | freshness_flag value |
|---|---|
| resource_type = 'funding' | `check` (always) |
| article/book/book_chapter AND year > 5yr ago | `stale` |
| software AND year > 2yr ago | `stale` |
| All other cases | `null` (cleared) |
| After link-check worker detects broken link | `broken` (set by linkcheck worker) |

`lastVerified` is set to `datetime()` after every enrichment.

---

### 3.7 Frontend Quality Sorting

All Neo4j browse queries sort by `quality_score DESC, compendium_created_at DESC`. Quality score is the **primary sort signal** — all resources without a quality_score rank last.

Source: `src/lib/neo4j-queries.ts` (multiple query functions)

---

### 3.8 Human Override Layer (Payload)

The `ResourceEditorial` Payload collection allows curators to override pipeline-generated quality fields. Fields overridable by humans:

| Field | Type | Notes |
|---|---|---|
| `editorialDescription` | textarea | Human-written or edited description |
| `aiDraftDescription` | textarea | AI draft (editable, not read-only) |
| `aiAssessmentNotes` | textarea | AI reasoning notes |
| `qualityScore` | number 0–100 | Human override of AI score |
| `badges` | multi-select | Human-assigned badges |
| `difficultyLevel` | select | Human override |
| `assessorModel` | text | Which LLM assessed it |
| `assessedAt` | date | When assessment ran |

Source: `src/collections/ResourceEditorial/index.ts`

**⚠️ Undefined sync mechanism:** How human overrides in Payload propagate back to Neo4j (which the frontend reads) is not defined in any code found. An `afterChange` hook is mentioned in `BUILD_RECONCILIATION.md` ("Editorial workflow (afterChange hooks, ISR): ✅") but the implementation was not found in the files read.

---

## 4. QUALITY CONTROL / REVIEW WORKFLOW

### 4.1 Complete State Machine

```
                    [PARSE]
                       │
                    parsed
                       │
                    [DEDUP]
                       │
              ┌────────┴─────────┐
           duplicate         dedup_checking
              │                  │
           duplicate          [CLASSIFY]
           (terminal)             │
                        ┌─────────┼──────────┐
                   auto_excluded  │      review_needed
                   (terminal*) classified        │
                                  │         [HUMAN REVIEW]
                             auto_accepted    │         │
                                  │     human_accepted  human_rejected
                                  └────────┘            (terminal)
                                       │
                                [ACCEPT worker]
                                       │
                               enrichment_queued
                                       │
                               [ENRICHMENT worker]
                                       │
                          ┌────────────┴───────────┐
                       enriched              enrichment_failed
                       (terminal)            (terminal†)
```

`*` auto_excluded items go to `excluded_resources` blocklist  
`†` enrichment_failed can be retried via `retry-enrichment-failed.ts` CLI

**⚠️ No "published" state in the pipeline.** The candidate status enum in `types.ts` has no `published` state. Neo4j resources transition from `pending_enrichment` (set on node creation) to `enriched` (set on enrichment completion). There is no publishing gate, approval step, or `published` status in any pipeline code.

Source: `src/pipeline/types.ts`, `src/pipeline/workers/`, `BUILD_SPEC.md`

---

### 4.2 State Definitions

| Status | Location | Meaning |
|---|---|---|
| `parsed` | import_candidates | File parsed, row created, pre-dedup |
| `dedup_checking` | import_candidates | In dedup queue |
| `classifying` | import_candidates | In classify queue |
| `classified` | import_candidates | Classify done, routing in progress (transient) |
| `auto_accepted` | import_candidates | LLM confidence≥0.8 + relevance≥0.6 |
| `review_needed` | import_candidates | Below auto-accept threshold or LLM failure |
| `auto_excluded` | import_candidates | skip_reason set, or high confidence low relevance |
| `duplicate` | import_candidates | Matched existing resource by URL/DOI/ISBN/title |
| `human_accepted` | import_candidates | Curator approved review_needed item |
| `human_rejected` | import_candidates | Curator rejected review_needed item |
| `enrichment_queued` | import_candidates | Neo4j node created, enrichment job enqueued |
| `enriched` | import_candidates | ⚠️ **never written** — this status exists in the enum but no code sets it on import_candidates |
| `pending_enrichment` | Neo4j node | Node created, awaiting enrichment |
| `enriched` | Neo4j node | Enrichment completed successfully |
| `enrichment_failed` | Neo4j node | All API sources failed |
| `enrichment_pending` | Neo4j node | Unknown resource_type (fallback) |

---

### 4.3 Dedup Logic

**Sources checked:**
1. Neo4j: `MATCH (r:CompendiumResource) WHERE r.url = $url OR r.doi = $doi OR r.isbn = $isbn` — exact URL, DOI, ISBN
2. PostgreSQL cross-batch: title similarity check (threshold: 0.9 Jaro-Winkler or similar) against existing candidates

**DuplicateType values** (recorded on the candidate):
`exact_url | normalised_url | doi | isbn | title_match | cross_type_duplicate`

Source: `src/pipeline/types.ts`, `BUILD_SPEC.md`

---

### 4.4 Validation Gates

**⚠️ No formal publish gate defined.** There is no code that checks a resource against a list of required fields before making it publicly visible. Resources go directly from `pending_enrichment` → `enriched` on the Neo4j node. The frontend browse queries do not filter on `status=enriched` — they return all nodes regardless of enrichment status.

**[INFERRED]** Resources are implicitly "published" when they have been enriched (status=enriched in Neo4j). There is no explicit approval step or required-field gate.

---

### 4.5 Auto-Accept vs Human Review

| Condition | Decision | Tag |
|---|---|---|
| confidence ≥ 0.8 AND relevance ≥ 0.6 | auto_accept | **[AUTO]** |
| skip_reason set | auto_exclude | **[AUTO]** |
| confidence ≥ 0.8 AND relevance < 0.3 | auto_exclude | **[AUTO]** |
| confidence < 0.5 | review_needed | **[REVIEW]** |
| Any other combination | review_needed | **[REVIEW]** |
| LLM parse error after 2 retries | review_needed | **[REVIEW]** |
| Already has classified_type | auto_accept (bypass LLM) | **[AUTO]** |
| `requires_human_review=true` from assessor | ⚠️ **no action defined** | **[HUMAN]** should trigger |

---

## 5. EDITORIAL DESCRIPTION

### 5.1 Assessor System Prompt Requirements

From `ASSESSOR_SYSTEM_PROMPT` in `src/pipeline/lib/litellm.ts`:

- **`editorial_description`:** "1-2 sentences, accessible to medical trainees"
- **`editorial_description_long`:** "3-5 sentences"
- No explicit voice, tone, or structural guidance beyond "accessible to medical trainees"

### 5.2 Manus Extraction Context

From `src/pipeline/docs/manus-extraction/agent-prompt.md`, the extraction agent prompt instructs:

> `"description": "1–3 sentences"` — brief description of why useful for trainees

This is a **pre-enrichment** field written at import time by human extraction agents. It becomes `known_fields.description` passed to the assessor, not the final editorial_description.

### 5.3 Full-Text Search Indexing

Both `editorial_description` and `editorial_description_long` are indexed in Neo4j full-text search:

```cypher
CREATE FULLTEXT INDEX compendium_fulltext IF NOT EXISTS
  FOR (r:CompendiumResource)
  ON EACH [r.title, r.editorial_description, r.editorial_description_long]
  OPTIONS { indexConfig: { `fulltext.analyzer`: 'english' } }
```

Source: `src/pipeline/seed-neo4j.ts`

### 5.4 Audience Assumption

**Target reader:** Medical registrar or trainee undertaking their first or early research project. No prior research experience assumed unless `difficulty_level=advanced`. Must be comprehensible without jargon. Framing should be practical ("this helps you…") rather than abstract.

**[INFERRED from:** manus extraction prompt context, difficulty_level definitions in classify.ts ("beginner = no prior research experience"), BUILD_SPEC.md audience framing]

### 5.5 What Good vs Bad Looks Like

**Not defined in any project file.** No rubric, no examples, no style guide beyond length and "accessible."

**[HUMAN]** — Style guide for editorial descriptions does not exist and should be created before quality review can be meaningfully performed.

---

## 6. PIPELINE END TO END

### 6.1 Ingestion → Published Sequence

```
INPUT FILE (JSON/CSV/MD)
        │
        ▼
[Stage 1 — Parse] src/pipeline/workers/parse.ts
  • Normalize URLs, strip duplicates within file
  • Create import_candidates rows (status: parsed)
  • Enqueue dedup jobs
        │
        ▼
[Stage 2 — Dedup] src/pipeline/workers/dedup.ts
  • Check Neo4j by URL/DOI/ISBN
  • Check Postgres for cross-batch duplicates
  • Duplicates → status: duplicate (terminal)
  • New → enqueue classify jobs
        │
        ▼
[Stage 3 — Classify] src/pipeline/workers/classify.ts
  • Call compendium-classifier (glm-4.5-flash)
  • Route by confidence × relevance thresholds
  • auto_excluded → terminal
  • review_needed → human queue (no UI defined yet)
  • auto_accepted → enqueue accept job
        │
        ▼
[Stage 4 — Accept] src/pipeline/workers/accept.ts
  • Create CompendiumResource node in Neo4j
    (status: pending_enrichment)
  • Create USES_METHODOLOGY relationships
  • Persist resource_id to Postgres
  • Enqueue enrichment job
  • Set import_candidates status: enrichment_queued
        │
        ▼
[ENRICHMENT PIPELINE — separate service]
src/pipeline/enrichment/runner.ts
  • Route by resource_type to type-specific worker
  • Call external APIs (type-dependent, see §1.3)
  • Call assessResource() for quality + editorial fields
  • Write all props to Neo4j (SET r += $props)
  • Set status: enriched (success) or enrichment_failed (total failure)
  • Set lastVerified + freshness_flag
        │
        ▼
[NEO4J — CompendiumResource node status: enriched]
  • Visible in frontend browse immediately (no gate)
  • Sorted by quality_score DESC
        │
        ▼ (optional, human-triggered)
[PAYLOAD CMS — ResourceEditorial collection]
  • Curator can override editorial_description, badges, quality_score, difficulty_level
  • afterChange hook (implementation not found) presumably syncs back to Neo4j
```

### 6.2 Separate Services

| Service | What it runs |
|---|---|
| `compendium-web` | Next.js frontend + Payload CMS |
| `compendium-workers` | Parse + Dedup + Classify + Accept workers (BullMQ, Redis) |
| `compendium-enrichment` | Enrichment runner (separate service) |
| External classify worker | `/compendium/workers/compendium-import/` — **outdated, needs update** |

Source: `BUILD_SPEC.md`

### 6.3 Queue Architecture

- **Import queue** (BullMQ): parse → dedup → classify → accept jobs
- **Classify queue** (separate BullMQ queue): Decoupled to prevent LLM-slow jobs starving fast parse/dedup jobs
- **Enrichment queue** (BullMQ + Postgres backup): `compendium.enrichment_queue` table mirrors queue state for durability
- **Startup backfill:** On enrichment runner startup, any `pending` rows in `enrichment_queue` table are re-enqueued with jobId deduplication

Source: `src/pipeline/enrichment/runner.ts`, `BUILD_SPEC.md`

---

## 7. GAPS AND OPEN QUESTIONS

### 7.1 Critical Inconsistencies

| # | Issue | Files involved | Severity |
|---|---|---|---|
| 1 | **quality_score scale mismatch** | litellm.ts (0.0–1.0) vs schema_reference_data.sql (0.0–100.0) vs ResourceEditorial (0–100) | CRITICAL — all enriched scores wrong |
| 2 | **quality_dimensions field names mismatch** | litellm.ts: `credibility, relevance, clarity, currency, practicality` vs schema: `relevance, accuracy, authority, currency, accessibility, practical_utility` | HIGH |
| 3 | **editorial_badges value set mismatch** | litellm.ts prompt: space-separated strings vs ResourceEditorial: snake_case vs schema: different snake_case | HIGH |
| 4 | **Methodology tag code scheme mismatch** | classify.ts uses Compendium display codes (RS-01) but Neo4j taxonomy uses platform codes (SYN-01) | CRITICAL — taxonomy relationships cannot be created |
| 5 | **difficulty_level enum divergence** | pipeline: 3 values; Payload: 4 values (adds `expert`); schema: 4 values (adds `mixed`) | MEDIUM |
| 6 | **`enriched` never written to import_candidates** | types.ts defines it, no worker writes it | LOW — tracking gap only |

### 7.2 Undefined Mechanisms

| # | Gap | Impact |
|---|---|---|
| 1 | **No Payload → Neo4j sync** for editorial overrides | Human curator edits in Payload are not reflected in frontend browse unless a hook exists (not found) | HIGH |
| 2 | **No published/visibility gate** | All enriched resources are immediately visible. No approval or review step before surfacing to users | HIGH |
| 3 | **`requires_human_review=true` flag** | The assessor sets this flag but no code reads it or routes the resource to a review queue | MEDIUM |
| 4 | **Human review UI** | `review_needed` candidates accumulate (8,649 in prod) but no review interface exists | MEDIUM |
| 5 | **`compendium.resource` PostgreSQL table** | Defined in schema, "keystone table," but never populated by pipeline — dual write to both Neo4j and Postgres is undefined | MEDIUM |
| 6 | **USES_METHODOLOGY relationship creation** | accept.ts presumably creates these, but with which codes? If it uses classifier output codes (RS-01 etc.) and Neo4j has platform codes (SYN-01), relationships will fail silently | CRITICAL |

### 7.3 Decisions Unmade

| # | Question |
|---|---|
| 1 | Should quality_score be stored as 0.0–1.0 or 0.0–100.0? One store needs to normalise. |
| 2 | What exactly does "published" mean? Is it `status=enriched` in Neo4j, or does a separate step exist? |
| 3 | Should `requires_human_review=true` block visibility, route to a queue, or just flag? |
| 4 | What are the minimum required fields for a resource to surface in browse results? |
| 5 | How does editorial description quality get reviewed? No rubric, no examples, no style guide. |
| 6 | Should the assessor's methodology_tags override the classifier's, or supplement them? (Currently: assessor overrides — `assessment?.methodology_tags ?? known_fields?.methodology_tags`) |
| 7 | Which badge set is canonical? The assessor prompt, the Payload UI, or the schema? |
| 8 | Should the canonical resource store be Neo4j only, or also Postgres `compendium.resource`? |
| 9 | What happens to resources with `enrichment_failed` — do they surface to users, get hidden, or get retried automatically? |

### 7.4 Data Quality Issues (Live Production)

From status report 2026-05-29:

- 1,479 resources in Neo4j — **all** at `pending_enrichment`, zero `editorial_description`, zero `quality_score`
- Enrichment worker not deployed in Railway (2,505 queue items unprocessed)
- 8,649 candidates in `review_needed` with no review interface
- Queue count mismatch: 1,479 candidates with `enrichment_queued` status but 2,505 rows in `enrichment_queue` table (1,026 excess)

---

## 8. REFERENCE: Allowed Values Quick Reference

### Resource Types (14)
`article | book | book_chapter | video | podcast | software | reporting_guideline | course | web_guide | template | visual_reference | dataset | community | funding`

### Thesis Stages (6)
`TH (Theory) | HI (History) | EV (Evaluate) | ST (Study) | IN (Interpret) | SH (Share)`

### Access Types (5 in pipeline, 6 in frontend constants)
`free | freemium | paid | subscription | institutional` (+ `open_access` in frontend)

### Difficulty Levels (3 in pipeline)
`beginner | intermediate | advanced`

### Editorial Badges (assessor prompt — 9 values, space-separated strings)
`Free Access | Open Access | Peer Reviewed | Seminal Work | Essential Reference | Editors Choice | Guideline Endorsed | High Impact | Beginner Friendly`

### Candidate Statuses (12)
`parsed | dedup_checking | classifying | classified | auto_accepted | review_needed | auto_excluded | duplicate | human_accepted | human_rejected | enrichment_queued | enriched`

### Neo4j Resource Statuses (3)
`pending_enrichment | enriched | enrichment_failed`

### Freshness Flags
`check | stale | broken | null`

### Duplicate Types (6)
`exact_url | normalised_url | doi | isbn | title_match | cross_type_duplicate`

### Source Tools (5)
`gemini | claude | manus | manual | discovery_prompt`
