# CoThesis Compendium — Complete Field Mapping & Merge Logic: `dataset`

**Type:** Datasets & Data Sources
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `research_dataset`, `teaching_dataset`, `open_data_portal`

**Note:** `open_data_portal` is a container resource (a platform listing many datasets, e.g., PhysioNet, data.gov.au) — similar in concept to `blog_site` or `video_channel`. The portal itself is a resource, and individual notable datasets from it may also be separate `research_dataset` or `teaching_dataset` resources.

---

## 1. Architecture

```
dataset_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── dataset_source_datacite (API)
  │     ├── dataset_source_figshare (API)
  │     ├── dataset_source_zenodo (API)
  │     ├── dataset_source_re3data (API — for open_data_portal subtype)
  │     ├── dataset_source_physionet (scrape)
  │     ├── dataset_source_kaggle (scrape)
  │     ├── dataset_source_openalex (API — for datasets with DOIs)
  │     ├── dataset_source_scrape (source website / data portal page)
  │     ├── dataset_source_discovery
  │     └── dataset_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (data creator/custodian)
  │     ├── institution_entity_id (provider organisation)
  │     ├── content_platform_id (hosting platform)
  │     ├── funder_entity_ids[] (who funded data collection)
  │     └── described_in_article_id (cross-ref: paper describing the dataset)
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
| 1 | DataCite | `datacite` | T1 | Standard | Free | Authoritative DOI metadata for datasets |
| 2 | Figshare | `figshare` | T1 | Standard | Free | Academic data with DOIs, rich metadata |
| 3 | Zenodo | `zenodo` | T1 | Standard | Free | Research data with DOIs |
| 4 | re3data | `re3data` | T1 | Standard | Free | Registry of 3,400+ data repositories (for open_data_portal) |
| 5 | PhysioNet | `physionet` | T1 | N/A (scrape) | Free (credentialed) | Premier clinical datasets (MIMIC-IV etc.) |
| 6 | OpenAlex | `openalex` | T1 | 100K/day | Free | Citation counts for datasets with DOIs |
| 7 | Kaggle | `kaggle` | T2 | N/A (scrape) | Free | Health/medical practice datasets |
| 8 | Data portal page | `scrape` | T2 | N/A | Free | Portal/dataset metadata |
| 9 | Discovery | `discovery` | — | N/A | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 DataCite API (`dataset_source_datacite`)

**Lookup key:** DOI
**API endpoint:** `GET https://api.datacite.org/dois/{doi}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `doi` | `data.attributes.doi` | String | DOI |
| `title` | `data.attributes.titles[0].title` | String | Dataset title |
| `creators` | `data.attributes.creators[]` | Array[Object] | `{name, nameType, givenName, familyName, affiliation[], nameIdentifiers[]}` |
| `publisher` | `data.attributes.publisher` | String | Publishing repository |
| `publication_year` | `data.attributes.publicationYear` | Integer | Year published |
| `resource_type` | `data.attributes.types.resourceTypeGeneral` | String | Dataset, Software, Collection, etc. |
| `resource_type_specific` | `data.attributes.types.resourceType` | String | Specific type |
| `subjects` | `data.attributes.subjects[]` | Array[Object] | `{subject, subjectScheme, schemeUri}` |
| `descriptions` | `data.attributes.descriptions[]` | Array[Object] | `{description, descriptionType}` (Abstract, Methods, etc.) |
| `dates` | `data.attributes.dates[]` | Array[Object] | `{date, dateType}` (Created, Updated, Available, etc.) |
| `language` | `data.attributes.language` | String | Language |
| `identifiers` | `data.attributes.identifiers[]` | Array[Object] | Alternative identifiers |
| `related_identifiers` | `data.attributes.relatedIdentifiers[]` | Array[Object] | `{relatedIdentifier, relationType, relatedIdentifierType}` — links to papers, software |
| `sizes` | `data.attributes.sizes[]` | Array[String] | File sizes |
| `formats` | `data.attributes.formats[]` | Array[String] | File formats (CSV, XLSX, etc.) |
| `version` | `data.attributes.version` | String | Dataset version |
| `rights` | `data.attributes.rightsList[]` | Array[Object] | `{rights, rightsUri, rightsIdentifier}` |
| `funding_references` | `data.attributes.fundingReferences[]` | Array[Object] | `{funderName, funderIdentifier, awardNumber, awardTitle}` |
| `geo_locations` | `data.attributes.geoLocations[]` | Array[Object] | Geographic coverage |
| `citation_count` | `data.attributes.citationCount` | Integer | Citation count |
| `view_count` | `data.attributes.viewCount` | Integer | View count |
| `download_count` | `data.attributes.downloadCount` | Integer | Download count |
| `url` | `data.attributes.url` | String | Landing page URL |

---

### 3.2 Figshare / Zenodo

Same as defined in `field_mapping_visual_reference_complete.md`. Key fields: DOI, title, description, authors, files, license, views, downloads, categories, tags, funding.

### 3.3 re3data API (`dataset_source_re3data`)

**For:** `open_data_portal` subtype — registry of data repositories
**Lookup key:** Repository name or re3data ID
**API endpoint:** `GET https://www.re3data.org/api/v1/repository/{id}`

| Field | XML Path | Data Type | Description |
|-------|----------|-----------|-------------|
| `re3data_id` | `r3d:re3data/r3d:repository/r3d:re3data.orgIdentifier` | String | re3data ID (e.g., r3d100010082) |
| `repository_name` | `r3d:repositoryName` | String | Repository name |
| `additional_names` | `r3d:additionalName[]` | Array[Object] | Alternative names with languages |
| `repository_url` | `r3d:repositoryURL` | String | Repository URL |
| `description` | `r3d:description` | Text | Description |
| `repository_type` | `r3d:type[]` | Array[String] | disciplinary, institutional, other |
| `subjects` | `r3d:subject[]` | Array[Object] | Subject classifications (DFG scheme) |
| `content_types` | `r3d:contentType[]` | Array[Object] | Databases, images, plain text, software, structured text, etc. |
| `provider_types` | `r3d:providerType[]` | Array[String] | dataProvider, serviceProvider |
| `keywords` | `r3d:keyword[]` | Array[String] | Keywords |
| `institutions` | `r3d:institution[]` | Array[Object] | Operating institutions with names, countries, types |
| `data_access` | `r3d:dataAccess[]` | Array[Object] | `{dataAccessType, dataAccessRestriction}` — open, embargoed, restricted, closed |
| `data_upload` | `r3d:dataUpload[]` | Array[Object] | Whether external data upload is allowed |
| `data_licenses` | `r3d:dataLicense[]` | Array[Object] | Licenses used (CC0, CC-BY, etc.) |
| `pid_systems` | `r3d:pidSystem[]` | Array[String] | DOI, Handle, ARK, etc. |
| `apis` | `r3d:api[]` | Array[Object] | Available APIs with types |
| `certificates` | `r3d:certificate[]` | Array[String] | CoreTrustSeal, CLARIN, etc. |
| `software` | `r3d:software[]` | Array[Object] | Repository software (DSpace, Dataverse, etc.) |
| `start_date` | `r3d:startDate` | Date | When repository started |
| `end_date` | `r3d:endDate` | Date | When repository ended (if discontinued) |
| `last_update` | `r3d:lastUpdate` | Date | Last re3data record update |
| `size` | `r3d:size` | Object | Number of items/records |
| `enhanced_publications` | `r3d:enhancedPublication` | String | yes, no, unknown |

---

### 3.4 PhysioNet (`dataset_source_physionet`)

**Source:** physionet.org (scrape)
**Coverage:** 500+ clinical datasets including MIMIC-IV, eICU

| Field | Type | Description |
|-------|------|-------------|
| `physionet_url` | String | PhysioNet project URL |
| `title` | String | Dataset title |
| `abstract` | Text | Dataset abstract |
| `authors` | Array[String] | Authors |
| `version` | String | Current version |
| `doi` | String | DOI |
| `license` | String | License |
| `access_type` | String | Open, credentialed, restricted |
| `credentialing_requirements` | Text | What's needed for access (CITI training, DUA, etc.) |
| `size` | String | Dataset size |
| `file_count` | Integer | Number of files |
| `publication_date` | Date | Publication date |
| `related_publications` | Array[Object] | `{title, doi}` — papers using this dataset |
| `citation` | String | How to cite |
| `keywords` | Array[String] | Keywords |
| `data_description` | Text | Description of data contents |

---

### 3.5 Kaggle (`dataset_source_kaggle`)

| Field | Type | Description |
|-------|------|-------------|
| `kaggle_url` | String | Kaggle dataset URL |
| `title` | String | Dataset title |
| `description` | Text | Description |
| `creator` | String | Uploader name |
| `file_count` | Integer | Number of files |
| `total_size` | String | Total size |
| `download_count` | Integer | Downloads |
| `vote_count` | Integer | Upvotes |
| `usability_score` | Float | Kaggle usability score (0–10) |
| `tags` | Array[String] | Tags |
| `license` | String | License |
| `last_updated` | Date | Last update date |
| `columns_preview` | Array[Object] | `{name, type}` — column schema preview |

---

### 3.6 AI Assessment (`dataset_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{documentation, accessibility, relevance, size, currency, provenance}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | What methodologies this dataset is useful for |
| `thesis_stages` | Array[String] | Primarily "Study" (data analysis) |
| `difficulty_level` | String | |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | research_dataset, teaching_dataset, open_data_portal |
| `editorial_description` | Text | What this dataset contains and who it's useful for |
| `editorial_description_long` | Text | Extended |
| `editorial_badges` | Array[String] | Max 3 |
| `access_summary` | Text | Plain-language summary of how to access this data |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Golden Record Merge Rules

### 4.1 Core Fields

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `doi` | String | V | DataCite → Figshare → Zenodo → PhysioNet | |
| `url` | String | D | Derived | DataCite `url` → Figshare → Zenodo → PhysioNet → Kaggle → scrape |
| `title` | String | V | DataCite → Figshare → Zenodo → PhysioNet → Kaggle → scrape | |
| `description` | Text | V | DataCite `descriptions[type=Abstract]` → Figshare → Zenodo → PhysioNet → Kaggle | |
| `creators` | Array[Object] | V | DataCite `creators` → Figshare → Zenodo → PhysioNet | |
| `publisher_repository` | String | V | DataCite `publisher` → re3data `repository_name` | Name of the repository hosting the data. |
| `publication_date` | Date | V | DataCite → Figshare → Zenodo → PhysioNet → Kaggle | |
| `publication_year` | Integer | D | Derived | |
| `version` | String | V | DataCite → Figshare → Zenodo → PhysioNet | |
| `license` | String | V | DataCite `rightsList` → Figshare → Zenodo → PhysioNet → Kaggle | |
| `language` | String | V | DataCite → scrape | |

### 4.2 Access & Format

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `access_type` | String | V | PhysioNet → re3data `dataAccess` → Figshare → Kaggle | `open`, `credentialed`, `restricted`, `application_required`. |
| `access_requirements` | Text | V | PhysioNet `credentialing_requirements` → re3data → scrape | What's needed to access (ethics approval, CITI training, DUA, etc.). |
| `file_formats` | Array[String] | V | DataCite `formats` → Figshare `files[].mimetype` → Zenodo → Kaggle | CSV, XLSX, JSON, Parquet, etc. |
| `file_count` | Integer | V | Figshare → Zenodo → PhysioNet → Kaggle | |
| `total_size` | String | V | DataCite `sizes` → Figshare → Zenodo → PhysioNet → Kaggle | |
| `download_url` | String | V | Figshare `files[0].download_url` → Zenodo → PhysioNet → Kaggle | |
| `api_url` | String | V | re3data `apis` → scrape | If dataset has API access. |
| `pid_system` | String | V | re3data `pidSystem` | DOI, Handle, etc. |

### 4.3 Metrics

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `citation_count` | Integer | V | DataCite → OpenAlex | |
| `download_count` | Integer | V+max | max(Figshare, Zenodo, DataCite, Kaggle) | |
| `view_count` | Integer | V+max | max(Figshare, Zenodo, DataCite) | |
| `kaggle_usability_score` | Float | V | Kaggle | Kaggle's own quality metric. |

### 4.4 Data Content Description

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `subjects` | Array[String] | D | Merge DataCite `subjects` + Figshare `categories` + Zenodo `keywords` + Kaggle `tags` | |
| `geographic_coverage` | Array[String] | V | DataCite `geoLocations` | |
| `temporal_coverage` | String | V | DataCite `dates[type=Collected]` → scrape | Date range of data. |
| `record_count` | Integer | V | scrape → Kaggle | Number of records/rows. |
| `variable_count` | Integer | V | Kaggle `columns_preview` (count) → scrape | Number of variables/columns. |
| `data_dictionary_url` | String | V | scrape → PhysioNet | Link to data dictionary/codebook. |
| `related_publications` | Array[Object] | D | DataCite `relatedIdentifiers[type=IsDescribedBy]` + PhysioNet `related_publications` | Papers describing this dataset. |
| `described_in_article_id` | String | D | Entity resolution | Link to article resource record. |
| `funding` | Array[Object] | V | DataCite `fundingReferences` → Figshare `funding_list` | |
| `citation` | String | V | DataCite → Figshare → PhysioNet → Zenodo | Formatted citation. |

### 4.5 Open Data Portal Fields (for open_data_portal subtype)

| Golden Field | Type | Cat | Source | Applies To |
|-------------|------|-----|--------|-----------|
| `re3data_id` | String | V | re3data | open_data_portal |
| `repository_type` | Array[String] | V | re3data | disciplinary, institutional, etc. |
| `content_types` | Array[String] | V | re3data | What types of data are stored |
| `data_upload_allowed` | Boolean | V | re3data | Whether external deposits accepted |
| `certificates` | Array[String] | V | re3data | CoreTrustSeal, CLARIN, etc. |
| `repository_software` | String | V | re3data | DSpace, Dataverse, CKAN, etc. |
| `operating_institution` | String | V | re3data `institutions` | |
| `start_date` | Date | V | re3data | When repository launched |
| `dataset_count` | Integer | V | re3data `size` → scrape | Number of datasets hosted |

### 4.6 Teaching Dataset Fields (for teaching_dataset subtype)

| Golden Field | Type | Cat | Source | Applies To |
|-------------|------|-----|--------|-----------|
| `analysis_guide_url` | String | V | scrape | Link to analysis tutorial/guide |
| `intended_analyses` | Array[String] | L | AI Assessment | What analyses this dataset is designed to teach |
| `companion_course_id` | String | D | Entity resolution | Link to course resource if part of a course |

### 4.7 LLM-Authored Fields

| Golden Field | Type | Cat | Notes |
|-------------|------|-----|-------|
| `editorial_description` | Text | L | What this dataset contains and how trainees can use it. |
| `editorial_description_long` | Text | L | Extended. |
| `access_summary` | Text | L | Plain-language "how to access this data" guide. |
| `methodology_tags` | Array[String] | L | What research methodologies this dataset supports. |
| `thesis_stages` | Array[String] | L | |
| `difficulty_level` | String | L | |
| `editorial_badges` | Array[String] | L | Max 3. |
| `quality_score` | Float (0–1) | L | |
| `quality_dimensions` | Object | L | `{documentation, accessibility, relevance, size, currency, provenance}` |
| `subtype_classification` | String | L | |

### 4.8 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `creator_person_ids` | Array[String] | D | Dataset creators → Person entities. |
| `institution_entity_id` | String | D | Provider organisation → Institution via ROR. |
| `content_platform_id` | String | D | Hosting platform → Content Platform entity. |
| `funder_entity_ids` | Array[String] | D | Funding references → Funder entities. |
| `described_in_article_id` | String | D | Related publication → article resource record. |

---

## 5. Refresh & Field Summary

**Refresh:** Quarterly for active repositories (new datasets, download counts); biannually for stable datasets; annually for portals.

| Category | Count |
|----------|-------|
| Verbatim (V) | ~30 |
| Derived (D) | ~12 |
| LLM-authored (L) | ~10 |
| **Total** | **~52** |
