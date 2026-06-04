# CoThesis Compendium — Complete Field Mapping & Merge Logic: `template`

**Type:** Templates & Forms
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `protocol_template`, `ethics_application_template`, `data_extraction_form`, `statistical_analysis_plan_template`, `methodology_checklist_decision_aid`

---

## 1. Architecture

```
template_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── template_source_scrape (source website — SPIRIT, PRISMA, university ethics offices, etc.)
  │     ├── template_source_protocols_io (API)
  │     ├── template_source_zenodo (API — for templates with DOIs)
  │     ├── template_source_osf (API — for pre-registration templates)
  │     ├── template_source_clinicaltrials_gov (API — published SAPs/protocols)
  │     ├── template_source_discovery
  │     └── template_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_id (template author — rare)
  │     ├── institution_entity_id (issuing body)
  │     └── reporting_guideline_id (cross-ref: template aligned with which standard)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

---

## 2. Source Trust Ranking

| Rank | Source | Code | Tier | Rate Limit | Free? | Rationale |
|------|--------|------|------|-----------|-------|-----------|
| 1 | Source website scrape | `scrape` | T1 | N/A | Free | Authoritative — templates from their official source |
| 2 | protocols.io | `protocols_io` | T1 | Standard | Free | DOI-assigned, versioned, peer-reviewed protocols |
| 3 | Zenodo | `zenodo` | T2 | Standard | Free | Templates with DOIs |
| 4 | OSF | `osf` | T2 | Throttled | Free | Pre-registration templates |
| 5 | ClinicalTrials.gov | `ctgov` | T2 | 50 req/min | Free | Published SAPs/protocols from registered trials |
| 6 | Discovery | `discovery` | — | N/A | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Source Website Scrape (`template_source_scrape`)

**Sources:** SPIRIT, PRISMA, CONSORT, ICH, university ethics offices, NHMRC/HRA/OHRP, Cochrane/JBI, REDCap shared library, TransCelerate, Global Health Network, ACTA, MRCT Center, NIH consent templates

| Field | Type | Description |
|-------|------|-------------|
| `source_url` | String | Template download/information page URL |
| `template_name` | String | Template name/title |
| `template_description` | Text | Description of what the template covers |
| `issuing_body` | String | Organisation that created/maintains the template |
| `issuing_body_url` | String | Organisation URL |
| `download_url` | String | Direct download URL |
| `download_format` | String | Word, PDF, Excel, online form |
| `file_size` | String | File size (if shown) |
| `version` | String | Template version |
| `version_date` | Date | When this version was released |
| `previous_versions` | Array[Object] | `{version, date, url}` |
| `aligned_with_guideline` | String | Which reporting guideline this template supports (e.g., SPIRIT, PRISMA) |
| `jurisdiction` | String | Geographic jurisdiction (e.g., Australia, UK, US, International) |
| `applicable_study_types` | Array[String] | Which study types this template is for |
| `sections` | Array[String] | Template section headings |
| `instructions_url` | String | Link to completion instructions/guidance |
| `example_url` | String | Link to completed example (if available) |
| `language` | String | Template language |
| `translations` | Array[Object] | `{language, url}` |
| `license` | String | License if stated |
| `last_checked` | DateTime | When last scraped |

---

### 3.2 protocols.io (`template_source_protocols_io`)

**Lookup key:** Protocol title search or DOI
**API endpoint:** `GET https://www.protocols.io/api/v4/protocols?filter=public&key={query}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `protocol_id` | `id` | Integer | protocols.io ID |
| `doi` | `doi` | String | DOI |
| `uri` | `uri` | String | protocols.io URL |
| `title` | `title` | String | Protocol title |
| `description` | `description` | Text | Protocol description |
| `steps` | `steps[]` | Array[Object] | Step-by-step protocol: `{description, components[], duration}` |
| `authors` | `authors[]` | Array[Object] | Authors with names, affiliations, ORCIDs |
| `created_on` | `created_on` | DateTime | Creation date |
| `published_on` | `published_on` | DateTime | Publication date |
| `version_id` | `version_id` | Integer | Current version |
| `version_count` | `versions[]` (count) | Integer | Number of versions |
| `stats_views` | `stats.number_of_views` | Integer | View count |
| `stats_steps` | `stats.number_of_steps` | Integer | Step count |
| `stats_forks` | `stats.number_of_forks` | Integer | Fork count |
| `stats_bookmarks` | `stats.number_of_bookmarks` | Integer | Bookmark count |
| `keywords` | `keywords[]` | Array[String] | Keywords |
| `categories` | `categories[]` | Array[Object] | Category classifications |
| `has_peer_review` | Boolean | Derived | Whether peer-reviewed on protocols.io |
| `materials` | `materials[]` | Array[Object] | Materials/reagents needed |
| `guidelines` | `guidelines[]` | Array[String] | Linked guidelines |

---

### 3.3 Zenodo / OSF

Same fields as in `field_mapping_course_complete.md` (Zenodo/OSF source sections). Templates with DOIs from these repositories include files, creators, license, keywords, description.

### 3.4 ClinicalTrials.gov (`template_source_ctgov`)

**For:** Extracting real-world SAPs and protocol documents attached to registered trials.

| Field | Type | Description |
|-------|------|-------------|
| `nct_id` | String | ClinicalTrials.gov NCT number |
| `study_title` | String | Study title |
| `protocol_url` | String | URL to attached protocol document |
| `sap_url` | String | URL to attached SAP document |
| `study_type` | String | Interventional, observational, etc. |
| `study_phase` | String | Phase 1–4 (if applicable) |
| `conditions` | Array[String] | Studied conditions |
| `sponsor` | String | Study sponsor |

---

### 3.5 AI Assessment (`template_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{completeness, usability, authority, currency, specificity}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | |
| `thesis_stages` | Array[String] | Primarily "Study" and "Evaluate" |
| `difficulty_level` | String | |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | One of 5 subtypes |
| `editorial_description` | Text | What this template is for and when to use it |
| `editorial_description_long` | Text | Extended |
| `editorial_badges` | Array[String] | Max 3 |
| `when_to_use` | Text | When a trainee should use this template |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Golden Record Merge Rules

### 4.1 Identifiers & Core

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `url` | String | V | scrape `source_url` → protocols_io `uri` → zenodo/osf URL | |
| `doi` | String | V | protocols_io → zenodo → osf | Null for most scraped templates. |
| `download_url` | String | V | scrape → protocols_io → zenodo | Direct download link. |
| `download_format` | String | V | scrape → zenodo `files[].type` | Word, PDF, Excel. |
| `title` | String | V | scrape `template_name` → protocols_io `title` → discovery | |
| `description` | Text | V | scrape → protocols_io `description` → zenodo | |
| `issuing_body` | String | V | scrape `issuing_body` → protocols_io `authors[0].affiliation` | |
| `version` | String | V | scrape → protocols_io `version_id` | |
| `version_date` | Date | V | scrape → protocols_io `published_on` | |
| `jurisdiction` | String | V | scrape | Geographic scope (International, AU, UK, US). |
| `applicable_study_types` | Array[String] | V | scrape → AI Assessment | |
| `aligned_guideline_name` | String | V | scrape `aligned_with_guideline` → AI Assessment | |
| `aligned_guideline_id` | String | D | Entity resolution | Link to reporting_guideline resource. |
| `language` | String | V | scrape → protocols_io | |
| `translations` | Array[Object] | V | scrape | |
| `sections` | Array[String] | V | scrape → protocols_io `steps` (step titles) | |
| `instructions_url` | String | V | scrape | |
| `example_url` | String | V | scrape | |
| `license` | String | V | protocols_io → zenodo → scrape | |

### 4.2 protocols.io-Specific Fields

| Golden Field | Type | Cat | Source | Applies To |
|-------------|------|-----|--------|-----------|
| `protocol_steps` | Array[Object] | V | protocols_io | For protocols.io resources |
| `step_count` | Integer | V | protocols_io | |
| `view_count` | Integer | V | protocols_io | |
| `fork_count` | Integer | V | protocols_io | How many researchers adapted this protocol |
| `version_count` | Integer | V | protocols_io | |
| `is_peer_reviewed` | Boolean | V | protocols_io | |

### 4.3 LLM-Authored Fields

| Golden Field | Type | Cat | Notes |
|-------------|------|-----|-------|
| `editorial_description` | Text | L | What this template helps with and when to use it. |
| `editorial_description_long` | Text | L | Extended. |
| `when_to_use` | Text | L | Plain-language guidance. |
| `methodology_tags` | Array[String] | L | |
| `thesis_stages` | Array[String] | L | |
| `difficulty_level` | String | L | |
| `editorial_badges` | Array[String] | L | Max 3. |
| `quality_score` | Float (0–1) | L | |
| `quality_dimensions` | Object | L | `{completeness, usability, authority, currency, specificity}` |
| `subtype_classification` | String | L | |

### 4.4 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `author_person_id` | String | D | Template author → Person entity (rare). |
| `institution_entity_id` | String | D | Issuing body → Institution entity via ROR. |
| `reporting_guideline_id` | String | D | Aligned guideline → reporting_guideline resource record. |

---

## 5. Refresh Tiers

| Tier | Scope | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Active** | Templates with versioning (protocols.io) | Quarterly | protocols.io version check, link check |
| **Stable** | Most templates | Biannually | Link check, scrape (still available?) |
| **Archive** | Old versions of templates | Annually | Link check only |

---

## 6. Field Summary

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~22 | title, description, download_url, format, issuing_body, jurisdiction, sections, protocol_steps |
| Derived (D) | ~4 | url, aligned_guideline_id, entity IDs |
| LLM-authored (L) | ~10 | editorial_description, when_to_use, methodology_tags, quality_score |
| **Total template golden record fields** | **~36** | |
