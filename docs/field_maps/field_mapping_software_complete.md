# CoThesis Compendium — Complete Field Mapping & Merge Logic: `software`

**Type:** Software & Tools
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `statistical_software`, `qualitative_analysis_software`, `reference_manager`, `systematic_review_tool`, `data_collection_platform`, `literature_discovery_tool`, `writing_tool`, `project_management_tool`, `data_visualisation_tool`, `sample_size_calculator`, `clinical_coding_tool`, `ai_research_tool`, `protocol_registration_platform`, `mobile_app`

---

## 1. Architecture

```
software_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── software_source_product_website (scrape)
  │     ├── software_source_alternativeto (scrape)
  │     ├── software_source_g2 (scrape)
  │     ├── software_source_capterra (scrape)
  │     ├── software_source_github (API — OSS only)
  │     ├── software_source_biotools (API — life science tools)
  │     ├── software_source_scicrunch (API — RRID lookup)
  │     ├── software_source_pypi (API — Python packages)
  │     ├── software_source_cran (metadata — R packages)
  │     ├── software_source_wikipedia (scrape — comparison tables)
  │     ├── software_source_sr_toolbox (scrape — SR tools)
  │     ├── software_source_app_store (scrape — mobile apps)
  │     ├── software_source_joss (CrossRef — peer-reviewed OSS)
  │     ├── software_source_discovery
  │     └── software_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_id (solo developer, if applicable)
  │     ├── institution_entity_id (maintainer org — e.g., Vanderbilt for REDCap)
  │     ├── publisher_entity_id (commercial publisher, if applicable)
  │     ├── os_platform_ids[] (platform compatibility with version constraints)
  │     ├── content_platform_ids[] (distribution: web, app stores)
  │     └── alternative_resource_ids[] (cross-ref to alternative tools)
  │
  ├── Cross-References
  │     ├── alternative_resource_ids[] (ALTERNATIVE_TO relationship)
  │     ├── integration_resource_ids[] (INTEGRATES_WITH relationship)
  │     └── demo_video_ids[] (DEMONSTRATES relationship — from video type)
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
| 1 | Product website | `product_website` | T1 | N/A (scrape) | Free | Authoritative for features, pricing, platform support, current version |
| 2 | bio.tools | `biotools` | T1 | Unspecified | Yes | Curated life science software with EDAM ontology; 25K+ tools |
| 3 | SciCrunch / RRID | `scicrunch` | T1 | Reasonable use | Yes (key) | Citable research resource identifiers; 30K+ resources |
| 4 | GitHub API | `github` | T1 | 5K req/hr (auth) | Yes | Authoritative for OSS: stars, forks, license, commits, contributors |
| 5 | AlternativeTo | `alternativeto` | T1 | N/A (scrape) | Free | Best source for alternatives and "similar to" relationships |
| 6 | G2 | `g2` | T1 | N/A (scrape) | Free | Enterprise reviews, feature ratings, market position |
| 7 | Capterra | `capterra` | T1 | N/A (scrape) | Free | Reviews, categories, pricing transparency |
| 8 | SR Toolbox | `sr_toolbox` | T1 | N/A (scrape) | Free | Systematic review tools catalogue (niche but authoritative) |
| 9 | CAQDAS Project | `caqdas` | T1 | N/A (scrape) | Free | Qualitative analysis software comparison (niche but authoritative) |
| 10 | Wikipedia | `wikipedia` | T1 | N/A (scrape) | Free | Comparison tables for major software categories |
| 11 | PyPI | `pypi` | T2 | Reasonable | Yes | Python package metadata, versions, downloads |
| 12 | CRAN | `cran` | T2 | N/A | Yes | R package metadata, dependencies |
| 13 | JOSS (via CrossRef) | `joss` | T2 | Same as CrossRef | Yes | Peer-reviewed open-source software with DOIs |
| 14 | Apple App Store | `app_store_apple` | T2 | N/A (scrape) | Free | Mobile app metadata, ratings |
| 15 | Google Play Store | `app_store_google` | T2 | N/A (scrape) | Free | Mobile app metadata, ratings |
| 16 | StatPages.info | `statpages` | T2 | N/A (scrape) | Free | Free statistical tools listing |
| 17 | Discovery record | `discovery` | — | N/A | N/A | Agent-provided |

**Source applicability by software type:**

| Source | Statistical | Qual | RefMgr | SR | DataColl | LitDisc | Writing | ProjMgt | DataViz | SampSize | ClinCode | AI | Protocol | Mobile |
|--------|-----------|------|--------|----|---------|---------|---------|---------|---------|---------|---------|----|----------|--------|
| Product website | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| bio.tools | ● | — | — | — | — | — | — | — | ● | — | — | ● | — | — |
| SciCrunch | ● | ● | ● | ● | ● | — | — | — | ● | — | — | ● | — | — |
| GitHub | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | — | ● | — | — |
| AlternativeTo | ● | ● | ● | ● | ● | ● | ● | ● | ● | — | — | ● | — | ● |
| G2 | ● | ● | ● | ● | ● | ● | ● | ● | ● | — | ● | ● | — | — |
| Capterra | ● | ● | ● | ● | ● | ● | ● | ● | ● | — | ● | ● | — | — |
| SR Toolbox | — | — | — | ● | — | — | — | — | — | — | — | — | — | — |
| CAQDAS | — | ● | — | — | — | — | — | — | — | — | — | — | — | — |
| PyPI | ● | — | — | ● | — | ● | — | — | ● | ● | — | ● | — | — |
| CRAN | ● | — | — | ● | — | — | — | — | ● | ● | — | — | — | — |
| App stores | — | — | — | — | ● | — | — | — | — | — | — | — | — | ● |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Product Website Scrape (`software_source_product_website`)

| Field | Type | Description |
|-------|------|-------------|
| `product_url` | String | Product homepage URL |
| `product_name` | String | Official product name |
| `tagline` | String | Product tagline/one-liner |
| `description` | Text | Product description from website |
| `features` | Array[String] | Feature list |
| `current_version` | String | Latest version number |
| `version_date` | Date | Date of latest version release |
| `pricing_model` | String | `free`, `freemium`, `subscription`, `one_time`, `institutional`, `open_source` |
| `pricing_tiers` | Array[Object] | `{tier_name, price, currency, billing_period, features[]}` |
| `has_free_tier` | Boolean | Whether a free tier exists |
| `has_student_discount` | Boolean | Whether student/academic discount available |
| `student_price` | Float | Student/academic price |
| `platforms` | Array[String] | Windows, macOS, Linux, Web, iOS, Android, ChromeOS |
| `platform_details` | Array[Object] | `{platform, min_version, download_url}` |
| `system_requirements` | Text | Minimum system requirements |
| `license_type` | String | GPL, MIT, Apache, proprietary, etc. |
| `developer_name` | String | Developer/company name |
| `developer_url` | String | Developer website |
| `documentation_url` | String | Link to documentation |
| `tutorial_url` | String | Link to tutorials/getting started |
| `support_url` | String | Link to support/community |
| `changelog_url` | String | Link to changelog/release notes |
| `api_available` | Boolean | Whether API is available |
| `integrations` | Array[String] | Named integrations with other tools |
| `data_formats_import` | Array[String] | Supported import formats |
| `data_formats_export` | Array[String] | Supported export formats |
| `has_mobile_app` | Boolean | Whether mobile app exists |
| `has_browser_extension` | Boolean | Whether browser extension exists |
| `screenshot_urls` | Array[String] | Product screenshots |
| `logo_url` | String | Product logo |
| `favicon_url` | String | Favicon |
| `founded_year` | Integer | Year the product was created |
| `last_updated` | Date | When the website was last updated (from scrape timestamp) |

---

### 3.2 AlternativeTo (`software_source_alternativeto`)

| Field | Type | Description |
|-------|------|-------------|
| `alternativeto_url` | String | AlternativeTo page URL |
| `alternativeto_name` | String | Product name on AlternativeTo |
| `likes` | Integer | Number of likes |
| `alternatives` | Array[Object] | `{name, url, likes, is_free, platforms[]}` — alternative tools |
| `tags` | Array[String] | User-assigned tags |
| `platforms` | Array[String] | Platforms listed |
| `is_free` | Boolean | Whether marked as free |
| `is_open_source` | Boolean | Whether marked as open source |
| `description` | Text | Community description |
| `categories` | Array[String] | Categories |
| `recent_activity` | String | Whether "discontinued", "no longer maintained", etc. |

---

### 3.3 G2 (`software_source_g2`)

| Field | Type | Description |
|-------|------|-------------|
| `g2_url` | String | G2 product page URL |
| `g2_name` | String | Product name |
| `g2_rating` | Float | Overall G2 rating (0–5, one decimal) |
| `g2_review_count` | Integer | Number of reviews |
| `g2_satisfaction_score` | Float | User satisfaction percentage |
| `g2_ease_of_use` | Float | Ease of use rating |
| `g2_quality_of_support` | Float | Support quality rating |
| `g2_ease_of_setup` | Float | Setup ease rating |
| `g2_market_segment` | Array[String] | Small business, mid-market, enterprise |
| `g2_category` | String | G2 category |
| `g2_competitors` | Array[Object] | `{name, rating, review_count}` |
| `g2_pros` | Array[String] | Most-mentioned pros |
| `g2_cons` | Array[String] | Most-mentioned cons |
| `g2_best_for` | String | Best for description |

---

### 3.4 Capterra (`software_source_capterra`)

| Field | Type | Description |
|-------|------|-------------|
| `capterra_url` | String | Capterra page URL |
| `capterra_name` | String | Product name |
| `capterra_rating` | Float | Overall rating (0–5) |
| `capterra_review_count` | Integer | Number of reviews |
| `capterra_ease_of_use` | Float | Ease of use rating |
| `capterra_value_for_money` | Float | Value for money rating |
| `capterra_customer_support` | Float | Customer support rating |
| `capterra_functionality` | Float | Functionality rating |
| `capterra_deployment` | Array[String] | Cloud, on-premise, etc. |
| `capterra_pricing_starting` | Float | Starting price |
| `capterra_free_trial` | Boolean | Whether free trial available |
| `capterra_free_version` | Boolean | Whether free version available |

---

### 3.5 GitHub API (`software_source_github`)

**Lookup key:** GitHub repository (owner/repo)
**API endpoint:** `GET https://api.github.com/repos/{owner}/{repo}`
**Only for:** Open-source tools with GitHub repositories

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `github_url` | `html_url` | String | Repository URL |
| `github_full_name` | `full_name` | String | owner/repo |
| `github_description` | `description` | String | Repository description |
| `stars` | `stargazers_count` | Integer | Star count |
| `forks` | `forks_count` | Integer | Fork count |
| `open_issues` | `open_issues_count` | Integer | Open issues |
| `watchers` | `subscribers_count` | Integer | Watcher count |
| `language` | `language` | String | Primary programming language |
| `languages` | Via `/repos/{owner}/{repo}/languages` | Object | All languages with byte counts |
| `license` | `license.spdx_id` | String | SPDX license identifier |
| `license_name` | `license.name` | String | License name |
| `created_at` | `created_at` | DateTime | Repository creation date |
| `updated_at` | `updated_at` | DateTime | Last push date |
| `pushed_at` | `pushed_at` | DateTime | Last push to any branch |
| `default_branch` | `default_branch` | String | Default branch name |
| `size` | `size` | Integer | Repository size (KB) |
| `homepage` | `homepage` | String | Homepage URL |
| `topics` | `topics[]` | Array[String] | Repository topics/tags |
| `has_wiki` | `has_wiki` | Boolean | Whether wiki enabled |
| `has_pages` | `has_pages` | Boolean | Whether GitHub Pages enabled |
| `is_archived` | `archived` | Boolean | Whether archived |
| `is_disabled` | `disabled` | Boolean | Whether disabled |
| `is_fork` | `fork` | Boolean | Whether this is a fork |
| `contributors_count` | Via `/repos/{owner}/{repo}/contributors` (count) | Integer | Number of contributors |
| `latest_release_tag` | Via `/repos/{owner}/{repo}/releases/latest` → `tag_name` | String | Latest release version |
| `latest_release_date` | Via `/repos/{owner}/{repo}/releases/latest` → `published_at` | DateTime | Latest release date |
| `latest_release_name` | Via `/repos/{owner}/{repo}/releases/latest` → `name` | String | Release name |
| `commit_activity` | Via `/repos/{owner}/{repo}/stats/commit_activity` | Array[Object] | Weekly commit counts (last year) |
| `readme_content` | Via `/repos/{owner}/{repo}/readme` | Text | README content (for AI assessment) |

---

### 3.6 bio.tools API (`software_source_biotools`)

**Lookup key:** Tool name or bio.tools ID
**API endpoint:** `GET https://bio.tools/api/t/{id}?format=json`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `biotools_id` | `biotoolsID` | String | bio.tools identifier |
| `name` | `name` | String | Tool name |
| `description` | `description` | Text | Tool description |
| `homepage` | `homepage` | String | Homepage URL |
| `version` | `version[]` | Array[String] | Version(s) |
| `tool_type` | `toolType[]` | Array[String] | Command-line tool, Web application, Library, etc. |
| `topic` | `topic[]` | Array[Object] | EDAM topics: `{term, uri}` |
| `function` | `function[]` | Array[Object] | Operations with inputs/outputs: `{operation[{term,uri}], input[{data,format}], output[{data,format}]}` |
| `operating_system` | `operatingSystem[]` | Array[String] | Linux, Mac, Windows |
| `language` | `language[]` | Array[String] | Programming languages (Python, R, Java, etc.) |
| `license` | `license` | String | SPDX license |
| `maturity` | `maturity` | String | Emerging, Mature, Legacy |
| `cost` | `cost` | String | Free, Free of charge (with restrictions), Commercial |
| `accessibility` | `accessibility[]` | Array[String] | Open access, Restricted access |
| `collection` | `collectionID[]` | Array[String] | Collection memberships |
| `credit` | `credit[]` | Array[Object] | Credits: `{name, email, url, orcidid, typeEntity, typeRole}` |
| `publication` | `publication[]` | Array[Object] | Linked publications: `{doi, pmid, pmcid, type, version}` |
| `documentation` | `documentation[]` | Array[Object] | Documentation links: `{url, type}` (API, User manual, Terms of use, etc.) |
| `download` | `download[]` | Array[Object] | Download links: `{url, type}` (Source code, Container file, etc.) |
| `link` | `link[]` | Array[Object] | Other links: `{url, type}` (Repository, Mailing list, etc.) |
| `edam_topics` | Derived from `topic[]` | Array[String] | EDAM ontology term names |
| `edam_operations` | Derived from `function[].operation[]` | Array[String] | EDAM operation names |

---

### 3.7 SciCrunch / RRID Portal (`software_source_scicrunch`)

**Lookup key:** RRID or tool name search
**API endpoint:** `GET https://scicrunch.org/api/1/resource/fields/view/{rrid}?key={key}`

| Field | Type | Description |
|-------|------|-------------|
| `rrid` | String | Research Resource Identifier (e.g., RRID:SCR_001905 for SPSS) |
| `scicrunch_name` | String | Resource name |
| `scicrunch_description` | Text | Description |
| `resource_type` | String | software application, database, etc. |
| `proper_citation` | String | How to cite this resource (e.g., "SPSS Statistics, RRID:SCR_001905") |
| `url` | String | Resource URL |
| `keywords` | Array[String] | Keywords |
| `related_resources` | Array[Object] | Related resources with RRIDs |
| `used_by_publications` | Integer | Number of publications mentioning this RRID |
| `availability` | String | Availability status |
| `alternate_ids` | Array[String] | Other identifiers |

---

### 3.8 PyPI (`software_source_pypi`)

**Lookup key:** Package name
**API endpoint:** `GET https://pypi.org/pypi/{package}/json`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `name` | `info.name` | String | Package name |
| `version` | `info.version` | String | Latest version |
| `summary` | `info.summary` | String | One-line summary |
| `description` | `info.description` | Text | Full description (may be markdown/RST) |
| `description_content_type` | `info.description_content_type` | String | text/markdown, text/x-rst, etc. |
| `author` | `info.author` | String | Author name |
| `author_email` | `info.author_email` | String | Author email |
| `maintainer` | `info.maintainer` | String | Maintainer name |
| `license` | `info.license` | String | License |
| `home_page` | `info.home_page` | String | Homepage URL |
| `project_url` | `info.project_url` | String | PyPI project URL |
| `project_urls` | `info.project_urls` | Object | `{Documentation, Homepage, Source, Tracker}` |
| `requires_python` | `info.requires_python` | String | Python version requirement |
| `requires_dist` | `info.requires_dist[]` | Array[String] | Dependencies |
| `classifiers` | `info.classifiers[]` | Array[String] | Trove classifiers (topics, frameworks, licenses, audiences) |
| `keywords` | `info.keywords` | String | Comma-separated keywords |
| `platform` | `info.platform` | String | Target platform |
| `downloads` | Via BigQuery or pypistats.org | Object | Download counts (recent_daily, recent_weekly, recent_monthly) |
| `releases` | `releases` | Object | All versions with upload dates |
| `first_release_date` | Derived from `releases` | Date | Date of first version |

---

### 3.9 CRAN (`software_source_cran`)

**Lookup key:** Package name
**Access:** `https://cran.r-project.org/web/packages/{package}/` (scrape) or crandb API

| Field | Type | Description |
|-------|------|-------------|
| `cran_name` | String | Package name |
| `cran_version` | String | Latest version |
| `title` | String | Package title |
| `description` | Text | Package description |
| `authors` | String | Authors (R-style author string with roles) |
| `maintainer` | String | Current maintainer |
| `license` | String | License |
| `depends` | Array[String] | R dependencies |
| `imports` | Array[String] | Imported packages |
| `suggests` | Array[String] | Suggested packages |
| `url` | String | Package URL(s) |
| `bug_reports` | String | Bug tracker URL |
| `needs_compilation` | Boolean | Whether needs compilation |
| `published` | Date | Publication date of latest version |
| `cran_checks` | Object | CRAN check results across platforms |
| `reverse_depends` | Integer | Number of packages depending on this one |
| `vignettes` | Array[Object] | Vignette titles and URLs |
| `bioc_views` | Array[String] | Bioconductor views (if also on Bioconductor) |

---

### 3.10 Wikipedia Comparison Tables (`software_source_wikipedia`)

| Field | Type | Description |
|-------|------|-------------|
| `wikipedia_url` | String | Wikipedia article URL (e.g., "Comparison of statistical software") |
| `wikipedia_features` | Object | Features extracted from comparison table (varies by category) |
| `wikipedia_description` | Text | Wikipedia description paragraph |
| `wikipedia_last_edited` | Date | Last edit date of comparison article |

---

### 3.11 SR Toolbox (`software_source_sr_toolbox`)

**Source:** systematicreviewtools.com (scrape)
**Only for:** Systematic review tools

| Field | Type | Description |
|-------|------|-------------|
| `sr_toolbox_name` | String | Tool name |
| `sr_toolbox_url` | String | SR Toolbox page URL |
| `sr_toolbox_description` | Text | Description from SR Toolbox |
| `sr_stages` | Array[String] | SR stages supported (Searching, Screening, Extraction, etc.) |
| `sr_features` | Array[String] | Features relevant to systematic reviews |
| `sr_pricing` | String | Pricing information |

---

### 3.12 App Store Scrape (`software_source_app_store`)

**For:** Mobile app subtype

| Field | Type | Description |
|-------|------|-------------|
| `app_store_url` | String | App Store / Play Store URL |
| `app_store_name` | String | App name |
| `app_store_developer` | String | Developer name |
| `app_store_rating` | Float | Average rating (0–5) |
| `app_store_rating_count` | Integer | Number of ratings |
| `app_store_price` | Float | Price (0 if free) |
| `app_store_category` | String | Store category |
| `app_store_last_updated` | Date | Last update date |
| `app_store_size` | String | App size |
| `app_store_requires` | String | Minimum OS version |
| `app_store_downloads` | String | Download count range (Play Store only) |
| `app_store_screenshots` | Array[String] | Screenshot URLs |

---

### 3.13 JOSS (`software_source_joss`)

**Lookup key:** DOI (JOSS assigns DOIs via CrossRef)
**API endpoint:** Standard CrossRef API for JOSS-published software papers

| Field | Type | Description |
|-------|------|-------------|
| `joss_doi` | String | JOSS paper DOI |
| `joss_title` | String | JOSS paper title |
| `joss_authors` | Array[Object] | Authors |
| `joss_review_url` | String | GitHub review issue URL |
| `joss_repository_url` | String | Software repository URL |
| `joss_published_date` | Date | JOSS publication date |
| `joss_citation_count` | Integer | Citations (from CrossRef) |

---

### 3.14 Discovery Record & AI Assessment

Same structure as previous types, with software-specific AI assessment fields:

#### AI Assessment (`software_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Overall quality |
| `quality_dimensions` | Object | `{functionality, usability, documentation, support, value, maintenance}` — software-specific dimensions |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | Which research methodologies this tool supports |
| `thesis_stages` | Array[String] | THESIS stages |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | Medical specialty relevance |
| `subtype_classification` | String | One of 14 subtypes |
| `editorial_description` | Text | 1–2 sentence original description |
| `editorial_description_long` | Text | 3–5 sentence extended description |
| `editorial_badges` | Array[String] | Max 3 |
| `use_case_summary` | Text | When/why a trainee would use this tool |
| `learning_curve` | String | minimal, moderate, steep |
| `comparable_tools` | Array[String] | Tools that serve similar purposes |
| `key_limitations` | Array[String] | Main limitations for medical trainees |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Secondary Entity Links

### 4.1 Person (Developer/Creator)

**Relationship:** `software -[DEVELOPED_BY]-> person`
**Only for:** Individual developers (e.g., Taguette by Rémi Rampin). Most software links to Institution instead.

### 4.2 Institution (Maintainer/Developer Org)

**Relationship:** `software -[MAINTAINED_BY]-> institution`
**Examples:** Vanderbilt (REDCap), QSR International (NVivo), IBM (SPSS), Cochrane (RevMan)
**Resolution:** Developer name from product website → ROR match

### 4.3 Publisher (Commercial Publisher)

**Relationship:** `software -[PUBLISHED_BY]-> publisher`
**Only for:** Commercial software with a distinct publisher (rare — most software companies are both developer and publisher)

### 4.4 Operating System Platform

**Relationship:** `software -[RUNS_ON {min_version, max_version, notes}]-> os_platform`
**Cardinality:** Many-to-many
**Resolution:** Extract from product website `platforms` + `platform_details` → match to OS Platform entity
**Version constraints stored on relationship:**
- `min_version`: Minimum OS version required (e.g., "10" for Windows 10+)
- `max_version`: Maximum OS version supported (null if current)
- `notes`: Compatibility notes

### 4.5 Content Platform (Distribution)

**Relationship:** `software -[AVAILABLE_ON]-> content_platform`
**Values:** Web (any browser), Apple App Store, Google Play Store, Microsoft Store, PyPI, CRAN, Bioconductor, GitHub

### 4.6 Cross-References

**ALTERNATIVE_TO:** `software -[ALTERNATIVE_TO]-> software` — bidirectional relationship. Source: AlternativeTo, AI assessment.
**INTEGRATES_WITH:** `software -[INTEGRATES_WITH]-> software` — directional. Source: product website `integrations`.
**DEMONSTRATES:** `video -[DEMONSTRATES]-> software` — incoming relationship from video type.

---

## 5. Golden Record Merge Rules

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `product_url` | String | V | product_website → AlternativeTo → G2 → discovery | Official product homepage. |
| `github_url` | String | V | GitHub (if OSS) | Null for proprietary software. |
| `rrid` | String | V | SciCrunch | Research Resource Identifier. Null if not registered. |
| `biotools_id` | String | V | bio.tools | Null if not in bio.tools. |
| `pypi_name` | String | V | PyPI | Null if not a Python package. |
| `cran_name` | String | V | CRAN | Null if not an R package. |
| `joss_doi` | String | V | JOSS/CrossRef | Null if not JOSS-published. |
| `g2_url` | String | V | G2 | |
| `capterra_url` | String | V | Capterra | |
| `alternativeto_url` | String | V | AlternativeTo | |
| `url` | String | D | Derived | `product_url` (always the canonical URL). |

### 5.2 Core Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `name` | String | V | product_website → bio.tools → SciCrunch → AlternativeTo → G2 | Official product name from product website. |
| `tagline` | String | V | product_website → G2 | Short one-liner. |
| `description` | Text | V | product_website → bio.tools → SciCrunch | Official product description. **Not the editorial description.** |
| `developer` | String | V | product_website → G2 → Capterra → bio.tools `credit` | Developer/company name. |
| `developer_url` | String | V | product_website | |
| `current_version` | String | V | product_website → GitHub `latest_release_tag` → PyPI `version` → CRAN `version` → bio.tools `version` | |
| `version_date` | Date | V | product_website → GitHub `latest_release_date` → PyPI (release date) → CRAN `published` | |
| `founded_year` | Integer | V | product_website → GitHub `created_at` (year) → PyPI first release year | |
| `logo_url` | String | V | product_website → G2 | |
| `favicon_url` | String | V | Google Favicon API | |
| `screenshot_urls` | Array[String] | V | product_website → app_store → G2 | |

### 5.3 Pricing

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `pricing_model` | String | V | product_website → G2 → Capterra | `free`, `freemium`, `subscription`, `one_time`, `institutional`, `open_source` |
| `is_free` | Boolean | D | Derived | `true` if pricing_model is `free` or `open_source`. |
| `is_open_source` | Boolean | D | Derived | `true` if GitHub repo exists AND license is OSI-approved, OR AlternativeTo `is_open_source`, OR bio.tools `cost == "Free"`. |
| `has_free_tier` | Boolean | V | product_website → Capterra `free_version` → AlternativeTo `is_free` | |
| `has_student_discount` | Boolean | V | product_website | |
| `pricing_tiers` | Array[Object] | V | product_website | Full tier breakdown. |
| `starting_price` | Float | V | Capterra `pricing_starting` → product_website (cheapest paid tier) | |
| `price_currency` | String | V | product_website → Capterra | |

### 5.4 Platform Compatibility

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `platforms` | Array[String] | D | Merge product_website `platforms` + AlternativeTo `platforms` + bio.tools `operatingSystem` + app_store presence | Deduplicate. Normalise to: `windows`, `macos`, `linux`, `web`, `ios`, `android`, `chromeos`. |
| `os_platform_ids` | Array[Object] | D | Entity resolution | `{os_platform_id, min_version, max_version}` → linked to OS Platform entities. |
| `platform_details` | Array[Object] | V | product_website | Detailed: `{platform, min_version, download_url, notes}`. |
| `is_web_based` | Boolean | D | Derived | `true` if "web" in `platforms`. |
| `is_mobile` | Boolean | D | Derived | `true` if "ios" or "android" in `platforms`. |
| `is_desktop` | Boolean | D | Derived | `true` if "windows", "macos", or "linux" in `platforms`. |

### 5.5 License & Open Source

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `license` | String | V | GitHub `license.spdx_id` → PyPI → CRAN → bio.tools → product_website | SPDX identifier preferred. |
| `license_name` | String | V | GitHub `license.name` → product_website | Human-readable license name. |
| `proper_citation` | String | V | SciCrunch `proper_citation` | How to formally cite this software. |
| `joss_doi` | String | V | JOSS/CrossRef | DOI for peer-reviewed software paper. |

### 5.6 Open Source Health (OSS only)

| Golden Field | Type | Cat | Source | Merge Rule |
|-------------|------|-----|--------|------------|
| `github_stars` | Integer | V | GitHub | |
| `github_forks` | Integer | V | GitHub | |
| `github_open_issues` | Integer | V | GitHub | |
| `github_contributors` | Integer | V | GitHub | |
| `github_last_commit` | Date | V | GitHub `pushed_at` | |
| `github_language` | String | V | GitHub | Primary language. |
| `github_languages` | Object | V | GitHub | All languages with proportions. |
| `github_topics` | Array[String] | V | GitHub | |
| `github_is_archived` | Boolean | V | GitHub | Project abandoned signal. |
| `pypi_downloads_monthly` | Integer | V | PyPI/pypistats | Monthly downloads. |
| `cran_reverse_depends` | Integer | V | CRAN | Packages depending on this. |
| `oss_health_signal` | String | D | Derived | `active` (commit <3 months), `maintained` (commit <1 year), `stale` (commit <3 years), `abandoned` (no commit >3 years or archived). |

### 5.7 Reviews & Ratings

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `g2_rating` | Float | V | G2 | |
| `g2_review_count` | Integer | V | G2 | |
| `g2_ease_of_use` | Float | V | G2 | |
| `capterra_rating` | Float | V | Capterra | |
| `capterra_review_count` | Integer | V | Capterra | |
| `capterra_ease_of_use` | Float | V | Capterra | |
| `alternativeto_likes` | Integer | V | AlternativeTo | |
| `app_store_rating` | Float | V | App Store | For mobile apps. |
| `app_store_rating_count` | Integer | V | App Store | |
| `rrid_publication_mentions` | Integer | V | SciCrunch `used_by_publications` | How many papers cite this RRID. |

### 5.8 Functionality & Features

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `features` | Array[String] | V | product_website → G2 → Capterra | Product-described features. |
| `data_formats_import` | Array[String] | V | product_website | |
| `data_formats_export` | Array[String] | V | product_website | |
| `has_api` | Boolean | V | product_website → bio.tools (documentation type=API) | |
| `api_documentation_url` | String | V | product_website → bio.tools | |
| `documentation_url` | String | V | product_website → bio.tools → GitHub (wiki/pages) | |
| `tutorial_url` | String | V | product_website | |
| `integrations` | Array[String] | V | product_website | Named tool integrations. |
| `edam_topics` | Array[String] | V | bio.tools | EDAM ontology topics (for bioinformatics tools). |
| `edam_operations` | Array[String] | V | bio.tools | EDAM ontology operations. |
| `sr_stages` | Array[String] | V | SR Toolbox | Systematic review stages supported. |

### 5.9 Alternatives & Relationships

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `alternatives` | Array[Object] | V | AlternativeTo → G2 `competitors` | `{name, url, is_free, match_score}`. |
| `alternative_resource_ids` | Array[String] | D | Entity resolution | Links to alternative software resource records in directory. |
| `integration_resource_ids` | Array[String] | D | Entity resolution | Links from `integrations` names → software resource records. |

### 5.10 Classification & LLM Fields

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `software_subtype` | String | L | AI Assessment | One of 14 subtypes. |
| `methodology_tags` | Array[String] | L | AI Assessment | Which research methodologies this tool supports. |
| `thesis_stages` | Array[String] | L | AI Assessment | |
| `difficulty_level` | String | L | AI Assessment | beginner, intermediate, advanced. |
| `learning_curve` | String | L | AI Assessment | minimal, moderate, steep. |
| `specialty_tags` | Array[String] | L | AI Assessment | |
| `editorial_description` | Text | L | All sources | Original 1–2 sentence description for trainees. |
| `editorial_description_long` | Text | L | All sources | Extended description. |
| `use_case_summary` | Text | L | Features, methodology tags, description | When/why a trainee would use this. |
| `key_limitations` | Array[String] | L | Reviews, features, pricing | Main limitations. |
| `comparable_tools` | Array[String] | L | AlternativeTo, G2, AI analysis | Similar tools (for those not yet in directory). |
| `editorial_badges` | Array[String] | L | Quality, reviews, OSS health, RRID, pricing | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `quality_dimensions` | Object | L | | `{functionality, usability, documentation, support, value, maintenance}` |

### 5.11 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `developer_person_id` | String | D | For solo developers → Person entity. |
| `maintainer_institution_id` | String | D | Developer org → Institution entity via ROR. |
| `os_platform_ids` | Array[Object] | D | Platforms → OS Platform entities with version constraints. |
| `content_platform_ids` | Array[String] | D | Distribution channels → Content Platform entities. |

---

## 6. Subtype-Specific Fields

Some subtypes have additional fields not applicable to all software:

| Field | Applies To | Source | Description |
|-------|-----------|--------|-------------|
| `sr_stages` | `systematic_review_tool` | SR Toolbox | Which SR stages are supported |
| `caqdas_comparison` | `qualitative_analysis_software` | CAQDAS Project | CAQDAS comparison data |
| `calculator_methods` | `sample_size_calculator` | product_website | Which power/sample size methods are supported |
| `coding_systems` | `clinical_coding_tool` | product_website | Which coding systems (ICD-10, SNOMED, etc.) |
| `ai_capabilities` | `ai_research_tool` | product_website | What AI/ML capabilities are offered |
| `registration_types` | `protocol_registration_platform` | product_website | What can be registered (trials, SRs, protocols) |
| `app_store_category` | `mobile_app` | app_store | App store category |
| `app_store_downloads` | `mobile_app` | app_store | Download count range |
| `reference_styles_count` | `reference_manager` | product_website | Number of citation styles supported |
| `supported_databases` | `literature_discovery_tool` | product_website | Which databases can be searched |

---

## 7. Field Provenance & Versioning

Same structure as previous types.

---

## 8. Refresh Tiers

| Tier | Software | Frequency | Sources Refreshed |
|------|----------|-----------|-------------------|
| **Hot** | OSS with active development (commit <1 month) | Monthly | GitHub (stars, issues, releases), product_website, link check |
| **Warm** | Active commercial tools OR OSS commit <1 year | Quarterly | Product website (version, pricing), G2/Capterra (ratings), GitHub, link check |
| **Cold** | Established tools, stable versions | Biannually | Product website (pricing, version), link check |
| **Archive** | Deprecated/abandoned tools | Annually | Link check, GitHub archived status, product website (still exists?) |

**Key monitoring signals:**
- GitHub: new releases (RSS via releases.atom), archived status
- Product website: version changes, pricing changes, sunset announcements
- AlternativeTo: "discontinued" flag
- CRAN/PyPI: new version releases

---

## 9. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| Version/release | GitHub, PyPI, CRAN, product website | New versions may add features relevant to trainees |
| Pricing | Product website, Capterra | Pricing changes affect recommendations |
| GitHub stats | GitHub API | Stars/forks indicate community health |
| Reviews/ratings | G2, Capterra | Accumulate over time |
| Platform support | Product website | New platform support may be added |
| RRID citations | SciCrunch | Grows as more papers cite the tool |
| Alternatives | AlternativeTo | New alternatives may emerge |
| OSS health | GitHub commits, issues | Activity indicates maintenance status |

---

## 10. Field Summary

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~55 | name, description, version, pricing, platforms, features, ratings (G2, Capterra, app store), GitHub stats, RRID, bio.tools data |
| Derived (D) | ~18 | url, is_free, is_open_source, is_web_based, oss_health_signal, entity IDs, alternative_resource_ids |
| LLM-authored (L) | ~14 | editorial_description, methodology_tags, software_subtype, learning_curve, use_case, limitations, quality_score |
| **Total software golden record fields** | **~87** | Second only to article in field count |

---

## 11. Source Coverage Heatmap

| Field Category | ProdWeb | AltTo | G2 | Capt | GitHub | bio.tools | SciCr | PyPI | CRAN | SRTool | AppStr |
|---------------|---------|-------|-----|------|--------|----------|-------|------|------|--------|--------|
| **Identity** | ●●● | ●●○ | ●●○ | ●○○ | ●●○ | ●●○ | ●●● | ●●○ | ●○○ | ●○○ | ●○○ |
| **Core metadata** | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | ●●○ |
| **Pricing** | ●●● | ●○○ | ●●○ | ●●● | — | ●○○ | — | — | — | ●○○ | ●●○ |
| **Platforms** | ●●● | ●●● | — | ●○○ | — | ●●○ | — | ●○○ | — | — | ●●○ |
| **License/OSS** | ●●○ | ●●○ | — | — | ●●● | ●●○ | — | ●●○ | ●●○ | — | — |
| **OSS health** | — | — | — | — | ●●● | — | — | ●○○ | ●○○ | — | — |
| **Reviews/ratings** | — | ●○○ | ●●● | ●●● | — | — | — | — | — | — | ●●● |
| **Features** | ●●● | — | ●●○ | ●●○ | — | ●●● | — | — | — | ●●● | — |
| **Alternatives** | — | ●●● | ●●○ | — | — | — | ●○○ | — | — | — | — |
| **Scientific metadata** | — | — | — | — | — | ●●● | ●●● | — | — | — | — |
| **Citations/RRID** | — | — | — | — | — | ●●○ | ●●● | — | — | — | — |

ProdWeb=Product Website, AltTo=AlternativeTo, Capt=Capterra, SciCr=SciCrunch, SRTool=SR Toolbox, AppStr=App Store
