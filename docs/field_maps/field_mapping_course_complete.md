# CoThesis Compendium — Complete Field Mapping & Merge Logic: `course`

**Type:** Courses & Learning
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `free_online_course`, `paid_course`, `open_courseware`, `workshop_materials`, `flashcard_study_set`

**Note:** Subtypes are very heterogeneous — a Coursera MOOC has structured syllabus data while an Anki flashcard deck has almost none. The schema accommodates all subtypes with many fields being null for simpler subtypes.

---

## 1. Architecture

```
course_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── course_source_platform_scrape (Coursera, edX, FutureLearn, etc.)
  │     ├── course_source_class_central (scrape)
  │     ├── course_source_mededportal (scrape)
  │     ├── course_source_merlot (scrape)
  │     ├── course_source_oer_commons (scrape)
  │     ├── course_source_carpentries (GitHub/scrape)
  │     ├── course_source_flashcard_platform (AnkiWeb/Quizlet/Brainscape scrape)
  │     ├── course_source_zenodo (API — for workshop materials with DOIs)
  │     ├── course_source_osf (API — for workshop materials)
  │     ├── course_source_conference_scrape (for workshop_materials)
  │     ├── course_source_discovery
  │     └── course_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (instructor/presenter)
  │     ├── content_platform_id (Coursera, edX, AnkiWeb, etc.)
  │     ├── institution_entity_id (offering institution)
  │     └── conference_entity_id (for workshop_materials)
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
| 1 | Platform website | `platform_scrape` | T1 | N/A (scrape) | Free | Authoritative for course content, syllabus, instructor, pricing |
| 2 | MedEdPORTAL | `mededportal` | T1 | N/A (scrape) | Free | Peer-reviewed medical education resources (MEDLINE-indexed) |
| 3 | Class Central | `class_central` | T1 | N/A (scrape) | Free | Best MOOC aggregator; reviews, follows, ratings |
| 4 | MERLOT | `merlot` | T2 | N/A (scrape) | Free | 100K+ peer-reviewed OERs |
| 5 | OER Commons | `oer_commons` | T2 | N/A (scrape) | Free | OER with quality rubrics |
| 6 | The Carpentries | `carpentries` | T2 | GitHub limits | Free (CC-BY) | Data/Software Carpentry lessons |
| 7 | Zenodo | `zenodo` | T2 | Standard | Free | Workshop materials with DOIs |
| 8 | OSF | `osf` | T2 | Throttled | Free | Workshop materials |
| 9 | Flashcard platforms | `flashcard_platform` | T2 | N/A (scrape) | Free | AnkiWeb, Quizlet, Brainscape |
| 10 | Conference website | `conference_scrape` | T2 | N/A (scrape) | Free | For workshop materials |
| 11 | Discovery | `discovery` | — | N/A | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Platform Scrape — MOOC Platforms (`course_source_platform_scrape`)

**For:** Coursera, edX, FutureLearn, OpenLearn, Khan Academy, MIT OCW, Cochrane Learning, BMJ Learning
**Note:** Each platform has different page structures. Fields below represent the union; many will be null for specific platforms.

| Field | Type | Description |
|-------|------|-------------|
| `platform_url` | String | Course page URL on platform |
| `platform_name` | String | Platform name (Coursera, edX, etc.) |
| `course_title` | String | Course title |
| `course_description` | Text | Full course description |
| `instructor_names` | Array[String] | Instructor/presenter names |
| `instructor_bios` | Array[Text] | Instructor biographies |
| `instructor_credentials` | Array[String] | Instructor qualifications |
| `institution_name` | String | Offering institution (e.g., Johns Hopkins University) |
| `institution_logo_url` | String | Institution logo |
| `syllabus` | Array[Object] | `{week/module_number, title, description, duration_minutes, items[]}` |
| `learning_objectives` | Array[String] | Stated learning outcomes |
| `prerequisites` | Array[String] | Prerequisite courses or knowledge |
| `language` | String | Primary language |
| `subtitle_languages` | Array[String] | Available subtitle languages |
| `duration_weeks` | Integer | Course duration in weeks |
| `effort_hours_per_week` | Float | Estimated weekly effort |
| `total_hours` | Float | Total estimated time |
| `level` | String | Beginner, Intermediate, Advanced |
| `rating` | Float | Platform rating (0–5) |
| `rating_count` | Integer | Number of ratings |
| `review_count` | Integer | Number of text reviews |
| `enrollment_count` | Integer | Total enrollees (if shown) |
| `pricing` | Object | `{is_free, price, currency, financial_aid, audit_available, certificate_price}` |
| `certificate_type` | String | None, statement, professional, verified, specialization |
| `skills_gained` | Array[String] | Skills tags |
| `topics` | Array[String] | Topic/category tags |
| `start_date` | String | Next start date (self-paced, specific date, or "always available") |
| `pacing` | String | self-paced, instructor-led, cohort-based |
| `has_assignments` | Boolean | Whether graded assignments exist |
| `has_peer_review` | Boolean | Whether peer review is used |
| `has_quizzes` | Boolean | Whether quizzes/assessments exist |
| `has_capstone` | Boolean | Whether capstone project exists |
| `video_count` | Integer | Number of video lectures |
| `total_video_hours` | Float | Total video content hours |
| `reading_count` | Integer | Number of readings |
| `part_of_specialization` | Object | `{specialization_name, url, position_in_sequence}` |
| `course_image_url` | String | Course thumbnail/banner |
| `last_updated` | Date | When course was last updated |
| `cpd_credits` | Object | `{credit_type, credit_hours, accrediting_body}` — for CME/CPD courses |

---

### 3.2 Class Central (`course_source_class_central`)

**Source:** classcentral.com (scrape)

| Field | Type | Description |
|-------|------|-------------|
| `class_central_url` | String | Class Central page URL |
| `class_central_rating` | Float | Bayesian rating (0–5) |
| `class_central_review_count` | Integer | Number of reviews |
| `class_central_follows` | Integer | Number of users following this course |
| `class_central_provider` | String | Platform provider |
| `class_central_institution` | String | Offering institution |
| `class_central_subjects` | Array[String] | Subject classifications |
| `class_central_certificate` | Boolean | Whether certificate available |
| `class_central_free` | Boolean | Whether free to audit |

---

### 3.3 MedEdPORTAL (`course_source_mededportal`)

**Source:** mededportal.org (scrape — MEDLINE-indexed, peer-reviewed)

| Field | Type | Description |
|-------|------|-------------|
| `mededportal_url` | String | MedEdPORTAL resource URL |
| `mededportal_id` | String | Resource ID |
| `title` | String | Resource title |
| `authors` | Array[Object] | Authors with affiliations |
| `abstract` | Text | Educational summary report abstract |
| `pmid` | String | PubMed ID (MEDLINE-indexed) |
| `doi` | String | DOI |
| `publication_date` | Date | Publication date |
| `resource_type` | String | Simulation, case-based learning, module, etc. |
| `target_audience` | Array[String] | Medical students, residents, faculty, etc. |
| `learning_objectives` | Array[String] | Objectives |
| `assessment_methods` | Array[String] | How learning is assessed |
| `competencies` | Array[String] | ACGME/CanMEDS competencies addressed |
| `keywords` | Array[String] | Keywords |
| `download_formats` | Array[String] | What's included (slides, facilitator guide, assessment forms) |

---

### 3.4 MERLOT (`course_source_merlot`)

| Field | Type | Description |
|-------|------|-------------|
| `merlot_url` | String | MERLOT page URL |
| `merlot_id` | String | MERLOT material ID |
| `title` | String | Resource title |
| `description` | Text | Description |
| `author` | String | Author/creator |
| `material_type` | String | Tutorial, Simulation, Lecture, etc. (19 types) |
| `peer_review_score` | Float | MERLOT peer review rating (1–5) |
| `user_rating` | Float | User rating (1–5) |
| `date_added` | Date | When added to MERLOT |
| `subjects` | Array[String] | Subject categories |
| `audience` | Array[String] | Target audience |
| `technical_requirements` | String | Technical requirements |

---

### 3.5 Flashcard Platform Scrape (`course_source_flashcard_platform`)

**For:** `flashcard_study_set` subtype
**Platforms:** AnkiWeb, Quizlet, Brainscape

| Field | Type | Description |
|-------|------|-------------|
| `platform_url` | String | Deck/set URL |
| `platform_name` | String | AnkiWeb, Quizlet, Brainscape |
| `deck_title` | String | Deck/set title |
| `deck_description` | Text | Description |
| `card_count` | Integer | Number of cards |
| `creator_name` | String | Deck creator |
| `rating` | Float | Rating (if available) |
| `download_count` | Integer | Downloads/copies (if shown) |
| `tags` | Array[String] | Tags |
| `last_updated` | Date | When last updated |
| `sample_cards` | Array[Object] | `{front, back}` — first few cards for preview |

---

### 3.6 Zenodo / OSF (`course_source_zenodo` / `course_source_osf`)

**For:** `workshop_materials` subtype with DOIs

| Field | Type | Description |
|-------|------|-------------|
| `zenodo_doi` | String | DOI |
| `zenodo_url` | String | Zenodo/OSF record URL |
| `title` | String | Workshop title |
| `creators` | Array[Object] | Creators with ORCIDs and affiliations |
| `description` | Text | Description |
| `publication_date` | Date | Upload date |
| `license` | String | License |
| `files` | Array[Object] | `{filename, size, type, download_url}` |
| `keywords` | Array[String] | Keywords |
| `communities` | Array[String] | Zenodo communities |
| `access_right` | String | open, embargoed, restricted, closed |
| `related_identifiers` | Array[Object] | Related DOIs |

---

### 3.7 Conference Scrape (`course_source_conference_scrape`)

**For:** `workshop_materials` subtype

| Field | Type | Description |
|-------|------|-------------|
| `conference_name` | String | Conference/workshop name |
| `conference_url` | String | Conference website URL |
| `workshop_title` | String | Workshop session title |
| `workshop_date` | Date | When the workshop ran |
| `presenter_names` | Array[String] | Workshop presenters |
| `presenter_credentials` | Array[String] | Presenter qualifications |
| `slides_url` | String | URL to downloadable slides |
| `recording_url` | String | URL to recording (if available) |
| `materials_url` | String | URL to supplementary materials |
| `abstract` | Text | Workshop abstract |

---

### 3.8 AI Assessment (`course_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{authority, currency, relevance, pedagogy, interactivity, accessibility}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | 162-methodology taxonomy |
| `thesis_stages` | Array[String] | THESIS stages |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | One of 5 subtypes |
| `editorial_description` | Text | 1–2 sentences |
| `editorial_description_long` | Text | Extended description |
| `editorial_badges` | Array[String] | Max 3 |
| `time_commitment` | String | AI summary of time required (e.g., "4 weeks, ~3 hours/week") |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Secondary Entity Links

### 4.1 Person (Instructor/Presenter)
**Relationship:** `course -[TAUGHT_BY]-> person`
**Resolution:** Instructor names from platform scrape → Person entity match via name + institution + credentials

### 4.2 Content Platform
**Relationship:** `course -[HOSTED_ON]-> content_platform`
**Values:** Coursera, edX, FutureLearn, Khan Academy, OpenLearn, MIT OCW, MedEdPORTAL, AnkiWeb, Quizlet, Brainscape, Zenodo, OSF

### 4.3 Institution (Offering Institution)
**Relationship:** `course -[OFFERED_BY]-> institution`
**Resolution:** Institution name from platform scrape → ROR match

### 4.4 Conference/Event (for Workshop Materials)
**Relationship:** `course -[PRESENTED_AT]-> conference`
**Resolution:** Conference name → Conference entity match

---

## 5. Golden Record Merge Rules

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `doi` | String | V | Zenodo/OSF → MedEdPORTAL → CrossRef | Null for most MOOCs. |
| `pmid` | String | V | MedEdPORTAL | Only for peer-reviewed MedEdPORTAL resources. |
| `platform_url` | String | V | platform_scrape | Course page URL on hosting platform. |
| `class_central_url` | String | V | Class Central | |
| `merlot_url` | String | V | MERLOT | |
| `url` | String | D | Derived | `platform_url` (always the canonical URL). |

### 5.2 Core Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `title` | String | V | platform_scrape → MedEdPORTAL → Class Central → MERLOT → discovery | |
| `description` | Text | V | platform_scrape → MedEdPORTAL `abstract` → Class Central → MERLOT | |
| `instructor_names` | Array[String] | V | platform_scrape → MedEdPORTAL `authors` | |
| `institution_name` | String | V | platform_scrape → Class Central → MedEdPORTAL (author affiliation) | |
| `language` | String | V | platform_scrape → discovery | ISO 639-1. |
| `subtitle_languages` | Array[String] | V | platform_scrape | |
| `level` | String | V | platform_scrape → Class Central | Beginner, Intermediate, Advanced. |
| `last_updated` | Date | V | platform_scrape → MERLOT `date_added` | When course content was last updated. |
| `course_image_url` | String | V | platform_scrape → Class Central | |

### 5.3 Duration & Effort

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `duration_weeks` | Integer | V | platform_scrape | |
| `effort_hours_per_week` | Float | V | platform_scrape | |
| `total_hours` | Float | D | Derived | `duration_weeks × effort_hours_per_week` if both available; else platform_scrape `total_hours`. |
| `pacing` | String | V | platform_scrape | self-paced, instructor-led, cohort-based. |
| `start_date` | String | V | platform_scrape | Next start date or "always available". |
| `card_count` | Integer | V | flashcard_platform | For flashcard_study_set only. |

### 5.4 Pricing & Access

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `is_free` | Boolean | D | Derived | `true` if platform_scrape `pricing.is_free` OR `pricing.audit_available`. |
| `price` | Float | V | platform_scrape `pricing.price` | Null if free. |
| `price_currency` | String | V | platform_scrape | |
| `audit_available` | Boolean | V | platform_scrape `pricing.audit_available` | Whether free audit (no certificate) is available. |
| `certificate_type` | String | V | platform_scrape | None, statement, professional, verified. |
| `certificate_price` | Float | V | platform_scrape `pricing.certificate_price` | |
| `financial_aid` | Boolean | V | platform_scrape `pricing.financial_aid` | |
| `cpd_credits` | Object | V | platform_scrape | `{credit_type, credit_hours, accrediting_body}`. |
| `license` | String | V | Zenodo/OSF → MedEdPORTAL → MERLOT | CC license for OER. |

### 5.5 Pedagogy & Content Structure

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `learning_objectives` | Array[String] | V | platform_scrape → MedEdPORTAL → MERLOT | |
| `syllabus` | Array[Object] | V | platform_scrape | Full syllabus structure. |
| `prerequisites` | Array[String] | V | platform_scrape | |
| `skills_gained` | Array[String] | V | platform_scrape | |
| `has_assignments` | Boolean | V | platform_scrape | |
| `has_quizzes` | Boolean | V | platform_scrape | |
| `has_peer_review` | Boolean | V | platform_scrape | |
| `has_capstone` | Boolean | V | platform_scrape | |
| `video_count` | Integer | V | platform_scrape | |
| `total_video_hours` | Float | V | platform_scrape | |
| `competencies` | Array[String] | V | MedEdPORTAL | ACGME/CanMEDS competencies. |
| `assessment_methods` | Array[String] | V | MedEdPORTAL → platform_scrape | |

### 5.6 Ratings & Adoption

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `platform_rating` | Float | V | platform_scrape `rating` | |
| `platform_rating_count` | Integer | V | platform_scrape | |
| `class_central_rating` | Float | V | Class Central | |
| `class_central_review_count` | Integer | V | Class Central | |
| `class_central_follows` | Integer | V | Class Central | |
| `merlot_peer_review_score` | Float | V | MERLOT | MERLOT's expert peer review. |
| `enrollment_count` | Integer | V | platform_scrape | If shown. |

### 5.7 Specialization/Series

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `part_of_specialization` | Object | V | platform_scrape | `{name, url, position_in_sequence}`. |
| `series_name` | String | D | Derived from `part_of_specialization.name` | Tag field. |

### 5.8 Workshop-Specific Fields

| Golden Field | Type | Cat | Source | Applies To |
|-------------|------|-----|--------|-----------|
| `conference_name` | String | V | conference_scrape | `workshop_materials` |
| `conference_entity_id` | String | D | Entity resolution | `workshop_materials` |
| `workshop_date` | Date | V | conference_scrape / Zenodo | `workshop_materials` |
| `slides_url` | String | V | conference_scrape / Zenodo `files` | `workshop_materials` |
| `recording_url` | String | V | conference_scrape | `workshop_materials` |
| `materials_files` | Array[Object] | V | Zenodo/OSF `files` | `workshop_materials` |

### 5.9 LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Title, description, instructor, institution, platform | Original 1–2 sentences. |
| `editorial_description_long` | Text | L | All data including syllabus | Extended. |
| `methodology_tags` | Array[String] | L | AI Assessment | 162-methodology taxonomy. |
| `thesis_stages` | Array[String] | L | AI Assessment | |
| `difficulty_level` | String | L | AI Assessment + platform level | |
| `specialty_tags` | Array[String] | L | AI Assessment | |
| `time_commitment` | String | L | Duration, effort, pacing | Human-readable summary. |
| `editorial_badges` | Array[String] | L | Quality, ratings, peer review status, OER | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `quality_dimensions` | Object | L | | `{authority, currency, relevance, pedagogy, interactivity, accessibility}` |
| `subtype_classification` | String | L | AI Assessment | One of 5 subtypes. |

### 5.10 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `instructor_person_ids` | Array[String] | D | Instructor names → Person entities. |
| `content_platform_id` | String | D | Platform name → Content Platform entity. |
| `institution_entity_id` | String | D | Institution name → Institution entity via ROR. |
| `conference_entity_id` | String | D | For workshops → Conference entity. |

---

## 6. Refresh Tiers

| Tier | Scope | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Active** | Courses currently running or recently updated | Quarterly | Platform scrape (pricing, dates, ratings), Class Central, link check |
| **Stable** | Self-paced courses, OER, archived MOOCs | Biannually | Platform scrape (still available?), link check |
| **Workshop** | Workshop materials | Annually | Link check only; materials don't change |
| **Flashcard** | Flashcard decks | Biannually | Flashcard platform (card count, last update), link check |

---

## 7. Field Summary

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~40 | title, description, instructor, institution, syllabus, pricing, ratings, duration, learning_objectives |
| Derived (D) | ~8 | url, is_free, total_hours, series_name, entity IDs |
| LLM-authored (L) | ~10 | editorial_description, methodology_tags, time_commitment, quality_score, subtype |
| **Total course golden record fields** | **~58** | |

---

## 8. Source Coverage Heatmap

| Field Category | PlatScr | ClassCen | MedEdP | MERLOT | OERComm | Carp | Zenodo | FlashPl | ConfScr |
|---------------|---------|----------|--------|--------|---------|------|--------|---------|---------|
| **Identity** | ●●● | ●●○ | ●●● | ●●○ | ●○○ | ●○○ | ●●○ | ●○○ | ●○○ |
| **Core metadata** | ●●● | ●●○ | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | ●●○ | ●●○ |
| **Pedagogy** | ●●● | — | ●●● | ●○○ | ●○○ | ●●○ | — | — | ●○○ |
| **Pricing** | ●●● | ●○○ | — | — | — | — | — | — | — |
| **Ratings** | ●●● | ●●● | — | ●●● | ●○○ | — | — | ●○○ | — |
| **CPD/CME** | ●●○ | — | ●●○ | — | — | — | — | — | — |
| **Files/downloads** | — | — | ●●○ | — | — | ●●● | ●●● | — | ●●○ |

PlatScr=Platform Scrape, ClassCen=Class Central, MedEdP=MedEdPORTAL, Carp=Carpentries, FlashPl=Flashcard Platform, ConfScr=Conference Scrape
