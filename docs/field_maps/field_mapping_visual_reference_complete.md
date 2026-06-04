# CoThesis Compendium — Complete Field Mapping & Merge Logic: `visual_reference`

**Type:** Visual References & Slides
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `infographic`, `flowchart_decision_tree`, `cheat_sheet`, `presentation_slide_deck`, `academic_poster`

---

## 1. Architecture

```
visual_reference_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── visual_source_figshare (API)
  │     ├── visual_source_zenodo (API)
  │     ├── visual_source_f1000 (scrape/OAI-PMH)
  │     ├── visual_source_slideshare (scrape)
  │     ├── visual_source_speaker_deck (scrape)
  │     ├── visual_source_scrape (source website)
  │     ├── visual_source_discovery
  │     └── visual_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (creator/presenter)
  │     ├── conference_entity_id (for presentations/posters)
  │     ├── content_platform_id (Figshare, Zenodo, SlideShare, etc.)
  │     ├── institution_entity_id (for institutional slide decks)
  │     └── source_article_id (cross-ref: for infographics derived from papers)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

---

## 2. Source Trust Ranking

| Rank | Source | Code | Tier | Free? | Rationale |
|------|--------|------|------|-------|-----------|
| 1 | F1000Research | `f1000` | T1 | Free (CC BY) | Peer-reviewed posters/slides with DOIs |
| 2 | Figshare | `figshare` | T1 | Free | Academic repository with DOIs, citation counts |
| 3 | Zenodo | `zenodo` | T1 | Free | Academic repository with DOIs |
| 4 | SlideShare | `slideshare` | T1 | Free (scrape) | Largest slide hosting platform |
| 5 | Speaker Deck | `speaker_deck` | T2 | Free (scrape) | Developer/academic presentations |
| 6 | Source website | `scrape` | T2 | Free | For infographics/cheat sheets hosted on blogs/institutional sites |
| 7 | Conference website | `conference_scrape` | T2 | Free | Conference poster/presentation archives |
| 8 | Discovery | `discovery` | — | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Figshare API (`visual_source_figshare`)

**Lookup key:** Figshare article ID or DOI
**API endpoint:** `GET https://api.figshare.com/v2/articles/{id}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `figshare_id` | `id` | Integer | Figshare article ID |
| `doi` | `doi` | String | DOI |
| `title` | `title` | String | Title |
| `description` | `description` | Text | Description |
| `defined_type_name` | `defined_type_name` | String | poster, presentation, figure, fileset, etc. |
| `authors` | `authors[]` | Array[Object] | `{full_name, orcid_id, url_name}` |
| `categories` | `categories[]` | Array[Object] | `{id, title}` |
| `tags` | `tags[]` | Array[String] | Tags |
| `files` | `files[]` | Array[Object] | `{id, name, size, download_url, mimetype}` |
| `license` | `license.name` | String | License name |
| `license_url` | `license.url` | String | License URL |
| `created_date` | `created_date` | DateTime | Upload date |
| `modified_date` | `modified_date` | DateTime | Last modified |
| `published_date` | `published_date` | DateTime | Published date |
| `citation` | `citation` | String | Formatted citation |
| `views` | `stats.views` | Integer | View count |
| `downloads` | `stats.downloads` | Integer | Download count |
| `shares` | `stats.shares` | Integer | Share count |
| `funding_list` | `funding_list[]` | Array[Object] | `{funder_name, grant_code, title}` |
| `is_embargoed` | `is_embargoed` | Boolean | Whether under embargo |
| `embargo_date` | `embargo_date` | DateTime | Embargo lift date |
| `thumbnail` | `thumb` | String | Thumbnail URL |

---

### 3.2 Zenodo API (`visual_source_zenodo`)

Same structure as defined in course type. Key fields: DOI, title, creators, description, publication_date, license, files, keywords, communities, access_right.

### 3.3 F1000Research (`visual_source_f1000`)

**Source:** f1000research.com/posters and /slides (scrape or OAI-PMH)

| Field | Type | Description |
|-------|------|-------------|
| `f1000_id` | String | F1000Research article ID |
| `doi` | String | DOI (F1000 assigns DOIs to posters/slides) |
| `title` | String | Title |
| `authors` | Array[Object] | Authors with affiliations |
| `abstract` | Text | Abstract |
| `publication_date` | Date | Publication date |
| `license` | String | CC BY (standard for F1000) |
| `conference_name` | String | Conference where presented |
| `resource_type` | String | poster, slide presentation |
| `download_url` | String | File download URL |
| `thumbnail_url` | String | Thumbnail |
| `views` | Integer | Views |
| `downloads` | Integer | Downloads |
| `citation` | String | Formatted citation |
| `funding` | Array[Object] | Funding information |
| `subjects` | Array[String] | Subject categories |
| `peer_review_status` | String | Approved, approved with reservations, not approved |
| `referees` | Array[Object] | Referee names and reports |

---

### 3.4 SlideShare / Speaker Deck (`visual_source_slideshare` / `visual_source_speaker_deck`)

| Field | Type | Description |
|-------|------|-------------|
| `platform_url` | String | Slide deck URL |
| `platform_name` | String | SlideShare or Speaker Deck |
| `title` | String | Deck title |
| `description` | Text | Description |
| `author_name` | String | Author/presenter name |
| `slide_count` | Integer | Number of slides |
| `views` | Integer | View count |
| `likes` | Integer | Like count |
| `downloads` | Integer | Download count (if available) |
| `upload_date` | Date | Upload date |
| `categories` | Array[String] | Categories/tags |
| `embed_code` | String | Embed code |
| `thumbnail_url` | String | First slide thumbnail |

---

### 3.5 AI Assessment (`visual_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{visual_clarity, accuracy, authority, currency, design_quality}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | |
| `thesis_stages` | Array[String] | |
| `difficulty_level` | String | |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | One of 5 subtypes |
| `editorial_description` | Text | |
| `editorial_description_long` | Text | |
| `editorial_badges` | Array[String] | Max 3 |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Golden Record Merge Rules

### 4.1 Core Fields

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `doi` | String | V | Figshare → Zenodo → F1000 | Many visuals lack DOIs. |
| `url` | String | D | Derived | F1000 URL → Figshare URL → Zenodo URL → SlideShare → scrape. |
| `title` | String | V | F1000 → Figshare → Zenodo → SlideShare → scrape → discovery | |
| `description` | Text | V | F1000 `abstract` → Figshare → Zenodo → SlideShare → scrape | |
| `creator_names` | Array[String] | V | F1000 → Figshare → Zenodo → SlideShare | |
| `publication_date` | Date | V | F1000 → Figshare → Zenodo → SlideShare → scrape | |
| `license` | String | V | F1000 (CC BY default) → Figshare → Zenodo | |
| `download_url` | String | V | F1000 → Figshare `files[0].download_url` → Zenodo files → SlideShare | Direct download. |
| `file_format` | String | D | Derived from download URL or MIME type | PDF, PPTX, PNG, SVG. |
| `slide_count` | Integer | V | SlideShare → Speaker Deck | For presentation subtype. |
| `thumbnail_url` | String | V | F1000 → Figshare `thumb` → Zenodo → SlideShare → scrape | |
| `views` | Integer | V+max | max(Figshare, F1000, SlideShare) | |
| `downloads` | Integer | V+max | max(Figshare, F1000, SlideShare) | |
| `conference_name` | String | V | F1000 → conference_scrape | For poster/presentation subtypes. |
| `conference_entity_id` | String | D | Entity resolution | → Conference entity. |
| `source_article_doi` | String | V | discovery / AI Assessment | For infographics derived from papers. |
| `source_article_id` | String | D | Entity resolution | → article resource record. |
| `citation` | String | V | Figshare → F1000 → Zenodo | Formatted citation string. |
| `funding` | Array[Object] | V | Figshare `funding_list` → F1000 | |
| `categories` | Array[String] | D | Merge Figshare `categories` + `tags` + F1000 `subjects` + SlideShare `categories` | |

### 4.2 LLM-Authored Fields

| Golden Field | Type | Cat | Notes |
|-------------|------|-----|-------|
| `editorial_description` | Text | L | What this visual shows and who it's useful for. |
| `editorial_description_long` | Text | L | Extended. |
| `methodology_tags` | Array[String] | L | |
| `thesis_stages` | Array[String] | L | |
| `difficulty_level` | String | L | |
| `editorial_badges` | Array[String] | L | Max 3. |
| `quality_score` | Float (0–1) | L | |
| `quality_dimensions` | Object | L | `{visual_clarity, accuracy, authority, currency, design_quality}` |
| `subtype_classification` | String | L | |

### 4.3 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `creator_person_ids` | Array[String] | D | Creator names → Person entities. |
| `conference_entity_id` | String | D | Conference name → Conference entity. |
| `content_platform_id` | String | D | Hosting platform → Content Platform entity. |
| `institution_entity_id` | String | D | For institutional slide decks → Institution. |
| `source_article_id` | String | D | For derived infographics → article record. |

---

## 5. Refresh & Field Summary

**Refresh:** Quarterly for Figshare/Zenodo (view/download counts); biannually for SlideShare; annually for posters/presentations (stable after publication).

| Category | Count |
|----------|-------|
| Verbatim (V) | ~20 |
| Derived (D) | ~8 |
| LLM-authored (L) | ~9 |
| **Total** | **~37** |
