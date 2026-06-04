# CoThesis Compendium — Complete Field Mapping & Merge Logic: `web_guide`

**Type:** Guides & Articles (Web Content)
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `methodology_guide`, `web_article`, `blog_site`, `programme_requirements`, `tweetorial`, `worked_example`

**Note:** `blog_site` is both a resource AND the Website/Blog container entity. Individual `web_article` resources link to their parent `blog_site` via `website_entity_id`. The Website/Blog entity is defined in `secondary_entity_reference.md`.

---

## 1. Architecture

### Individual Web Content Record

```
web_guide_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── web_source_scrape (Scrapy — primary content extraction)
  │     ├── web_source_wayback (Wayback Machine API)
  │     ├── web_source_rss (for blog_site subtype monitoring)
  │     ├── web_source_threadreader (for tweetorial subtype)
  │     ├── web_source_permacc (archival snapshot)
  │     ├── web_source_discovery
  │     └── web_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_id (author)
  │     ├── institution_entity_id (for methodology_guide, programme_requirements)
  │     ├── website_entity_id (parent blog/website — for web_article)
  │     └── medical_college_name (for programme_requirements — string, not entity)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

### Blog Site Record (as resource + entity)

```
blog_site_master (golden record — also the Website/Blog entity)
  │
  ├── Source Sub-Records
  │     ├── blog_source_scrape (about page, archive, author info)
  │     ├── blog_source_rss (feed metadata, post frequency)
  │     ├── blog_source_wayback (first archived date)
  │     ├── blog_source_favicon (site icon)
  │     ├── blog_source_discovery
  │     └── blog_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── operator_person_id (for individual blogs)
  │     ├── operator_institution_id (for institutional blogs)
  │     └── child_article_resource_ids[] (web_article resources from this blog)
  │
  └── Monitoring
        └── RSS feed / ChangeDetection.io
```

---

## 2. Source Trust Ranking

| Rank | Source | Code | Tier | Rate Limit | Free? | Rationale |
|------|--------|------|------|-----------|-------|-----------|
| 1 | Web scrape (Scrapy) | `scrape` | T1 | Self-managed | Free | Primary content extraction |
| 2 | RSS feed | `rss` | T1 | N/A | Free | New post monitoring for blogs |
| 3 | Wayback Machine | `wayback` | T1 | Generous | Free | Publication date estimation, archival |
| 4 | Google Favicon API | `favicon` | T1 | Generous | Free | Site icons |
| 5 | ThreadReaderApp | `threadreader` | T2 | N/A (scrape) | Free | Tweetorial unrolling |
| 6 | ChangeDetection.io | `changedetect` | T1 | Self-hosted | Free | Monitoring non-RSS sites |
| 7 | Perma.cc | `permacc` | T2 | 10/mo (individual) | Free (institutional) | Permanent archival snapshots |
| 8 | Discovery | `discovery` | — | N/A | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Web Scrape (`web_source_scrape`)

**Tool:** Scrapy + Playwright (for JavaScript-rendered pages)

| Field | Type | Description |
|-------|------|-------------|
| `url` | String | Page URL |
| `final_url` | String | URL after redirects |
| `title` | String | Page title (from `<title>` or `<h1>`) |
| `meta_description` | String | Meta description tag |
| `meta_author` | String | Meta author tag |
| `author_byline` | String | Author name extracted from byline/article markup |
| `author_bio` | Text | Author bio if on same page |
| `author_credentials` | String | Credentials in byline (MD, PhD, etc.) |
| `publication_date` | Date | Date from meta tags, schema.org, or byline |
| `last_modified_date` | Date | Last modified from HTTP headers or meta |
| `word_count` | Integer | Body text word count |
| `reading_time_minutes` | Integer | Estimated reading time |
| `content_html` | Text | Full article body HTML |
| `content_text` | Text | Cleaned plain text of article body |
| `headings` | Array[Object] | `{level, text}` — heading hierarchy |
| `images` | Array[Object] | `{src, alt, caption}` |
| `outbound_links` | Array[Object] | `{url, anchor_text, is_academic}` — links to other resources |
| `internal_links` | Array[Object] | `{url, anchor_text}` — links within same site |
| `schema_org` | Object | Parsed JSON-LD/schema.org structured data (if present) |
| `og_title` | String | OpenGraph title |
| `og_description` | String | OpenGraph description |
| `og_image` | String | OpenGraph image URL |
| `og_type` | String | OpenGraph type (article, website) |
| `og_site_name` | String | Site name from OpenGraph |
| `canonical_url` | String | Canonical URL from `<link rel="canonical">` |
| `language` | String | Page language from `<html lang>` |
| `site_name` | String | Website/blog name |
| `site_favicon` | String | Favicon URL |
| `has_comments` | Boolean | Whether comments section exists |
| `comment_count` | Integer | Number of comments (if extractable) |
| `categories` | Array[String] | Article categories/tags from page |
| `breadcrumb` | Array[String] | Breadcrumb trail |
| `http_status` | Integer | HTTP response status code |
| `last_checked` | DateTime | When last scraped |

---

### 3.2 Wayback Machine (`web_source_wayback`)

**API endpoint:** `GET https://archive.org/wayback/available?url={url}`
**CDX API:** `GET https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=1&sort=oldest`

| Field | Type | Description |
|-------|------|-------------|
| `first_snapshot_date` | Date | Earliest Wayback Machine snapshot (proxy for publication date) |
| `latest_snapshot_date` | Date | Most recent snapshot |
| `snapshot_count` | Integer | Total number of snapshots |
| `first_snapshot_url` | String | URL to earliest snapshot |
| `latest_snapshot_url` | String | URL to latest snapshot |
| `is_archived` | Boolean | Whether at least one snapshot exists |

---

### 3.3 RSS Feed (`web_source_rss` / `blog_source_rss`)

For blog_site monitoring and metadata.

| Field | Type | Description |
|-------|------|-------------|
| `rss_url` | String | RSS feed URL |
| `rss_title` | String | Feed title |
| `rss_description` | String | Feed description |
| `rss_language` | String | Feed language |
| `rss_last_build_date` | DateTime | Feed last updated |
| `rss_post_count` | Integer | Number of items in feed |
| `rss_latest_post_date` | Date | Most recent post date |
| `rss_post_frequency` | String | `daily`, `weekly`, `monthly`, `irregular` (derived from item dates) |
| `rss_categories` | Array[String] | Feed categories |

---

### 3.4 ThreadReaderApp (`web_source_threadreader`)

**For:** `tweetorial` subtype
**Source:** threadreaderapp.com (scrape of unrolled thread)

| Field | Type | Description |
|-------|------|-------------|
| `threadreader_url` | String | ThreadReaderApp URL |
| `original_thread_url` | String | Original Twitter/X thread URL |
| `thread_author` | String | Twitter handle and display name |
| `thread_date` | Date | Thread posting date |
| `tweet_count` | Integer | Number of tweets in thread |
| `thread_text` | Text | Full unrolled text |
| `thread_images` | Array[String] | Image URLs from thread |
| `thread_word_count` | Integer | Word count |

---

### 3.5 AI Assessment (`web_ai_assessment` / `blog_ai_assessment`)

#### Individual Content Assessment

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{authority, currency, accuracy, clarity, depth, credibility}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | 162-methodology taxonomy |
| `thesis_stages` | Array[String] | THESIS stages |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | One of 6 subtypes |
| `editorial_description` | Text | 1–2 sentences |
| `editorial_description_long` | Text | Extended |
| `editorial_badges` | Array[String] | Max 3 |
| `credibility_assessment` | Text | AI assessment of author/source credibility |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

#### Blog Site Assessment

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `editorial_description` | Text | Why this blog is worth following |
| `editorial_description_long` | Text | Extended |
| `primary_topics` | Array[String] | Main methodology topics |
| `methodology_tags` | Array[String] | |
| `post_quality_consistency` | String | `high`, `medium`, `variable` |
| `is_active` | Boolean | New content in last 6 months |

---

## 4. Secondary Entity Links

### 4.1 Person (Author)
**Relationship:** `web_guide -[AUTHORED_BY]-> person`
**Resolution:** Author name from scrape byline + credentials → Person entity match

### 4.2 Institution
**Relationship:** `web_guide -[PUBLISHED_BY]-> institution`
**For:** `methodology_guide` (e.g., Cochrane Handbook chapters, university methodology pages), `programme_requirements` (medical college pages)
**Resolution:** Site name / organisation → ROR match

### 4.3 Website/Blog (Container)
**Relationship:** `web_article -[PUBLISHED_ON]-> website_blog`
**For:** `web_article` subtype linking to parent `blog_site`
**Resolution:** Extract domain from URL → match to Website/Blog entity

---

## 5. Golden Record Merge Rules

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `url` | String | V | scrape `canonical_url` → scrape `final_url` → discovery URL | Prefer canonical URL. |
| `wayback_url` | String | V | Wayback Machine `latest_snapshot_url` | Archival backup URL. |
| `permacc_url` | String | V | Perma.cc | Permanent archived snapshot. |

### 5.2 Content Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `title` | String | V | scrape `title` → scrape `og_title` → discovery | |
| `description` | Text | V | scrape `meta_description` → scrape `og_description` | Short description. |
| `author_name` | String | V | scrape `author_byline` → scrape `meta_author` → scrape `schema_org` → discovery | |
| `author_credentials` | String | V | scrape `author_credentials` | |
| `publication_date` | Date | V | scrape `publication_date` → scrape `schema_org.datePublished` → wayback `first_snapshot_date` | Wayback as fallback estimate. |
| `last_modified` | Date | V | scrape `last_modified_date` → scrape `schema_org.dateModified` | |
| `publication_year` | Integer | D | Derived from `publication_date` | |
| `word_count` | Integer | V | scrape `word_count` | |
| `reading_time_minutes` | Integer | D | Derived | `word_count / 250`. |
| `language` | String | V | scrape `language` → rss `rss_language` | ISO 639-1. |
| `site_name` | String | V | scrape `og_site_name` → scrape `site_name` | Parent website name. |
| `content_text` | Text | V | scrape | Full article text (for AI assessment input). |
| `featured_image_url` | String | V | scrape `og_image` → scrape first image | |
| `favicon_url` | String | V | favicon API → scrape `site_favicon` | |
| `categories` | Array[String] | V | scrape `categories` | Article categories/tags from page. |

### 5.3 Link Analysis

| Golden Field | Type | Cat | Source | Merge Rule |
|-------------|------|-----|--------|------------|
| `outbound_academic_links` | Array[Object] | D | Derived from scrape `outbound_links` | Filter to academic URLs (DOIs, PubMed, university domains). |
| `outbound_link_count` | Integer | D | Derived | Total outbound links. |
| `academic_link_count` | Integer | D | Derived | Count of academic outbound links. |
| `references_dois` | Array[String] | D | Derived | DOIs extracted from outbound links. |

### 5.4 Archival & Preservation

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `is_archived` | Boolean | D | Derived | `true` if wayback or permacc snapshot exists. |
| `first_seen_date` | Date | V | wayback `first_snapshot_date` | Earliest known existence. |
| `archive_url` | String | D | Derived | permacc URL (if available) → wayback latest snapshot URL. |

### 5.5 Blog Site Fields (for blog_site subtype)

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `blog_name` | String | V | scrape `site_name` → rss `rss_title` | |
| `blog_url` | String | V | scrape | Homepage URL. |
| `blog_description` | Text | V | scrape (about page) → rss `rss_description` | |
| `operator_name` | String | V | scrape (about page) | Person or organisation running the blog. |
| `rss_url` | String | V | RSS discovery → manual | |
| `is_active` | Boolean | D | Derived | New content in last 6 months (from RSS or scrape). |
| `post_frequency` | String | V | rss (derived from item dates) | `daily`, `weekly`, `monthly`, `irregular`, `inactive`. |
| `topics` | Array[String] | V | rss `rss_categories` → scrape categories | |
| `child_article_count` | Integer | D | Derived | How many web_article resources from this blog are in the directory. |

### 5.6 Programme Requirements Fields (for programme_requirements subtype)

| Golden Field | Type | Cat | Source | Description |
|-------------|------|-----|--------|-------------|
| `college_name` | String | V | scrape | Medical college name (e.g., RANZCP, RACP, RCPA) |
| `programme_name` | String | V | scrape | Specific training programme |
| `research_requirements` | Text | V | scrape | Summary of research requirements |
| `eligible_study_types` | Array[String] | V | scrape | What study types count |
| `minimum_requirements` | Text | V | scrape | Minimum research output required |
| `deadlines` | Array[Object] | V | scrape | `{deadline_name, date, notes}` |
| `contact_url` | String | V | scrape | Contact page for research requirements |

### 5.7 Tweetorial Fields (for tweetorial subtype)

| Golden Field | Type | Cat | Source | Description |
|-------------|------|-----|--------|-------------|
| `thread_author_handle` | String | V | threadreader | Twitter/X handle |
| `tweet_count` | Integer | V | threadreader | Number of tweets |
| `original_thread_url` | String | V | threadreader | Original Twitter/X URL |

### 5.8 LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Title, content_text (first 1000 words), author, site | Original description. |
| `editorial_description_long` | Text | L | All data | Extended. |
| `methodology_tags` | Array[String] | L | AI Assessment | |
| `thesis_stages` | Array[String] | L | AI Assessment | |
| `difficulty_level` | String | L | AI Assessment | |
| `specialty_tags` | Array[String] | L | AI Assessment | |
| `credibility_assessment` | Text | L | Author credentials, site authority, references | AI assessment of source credibility. |
| `editorial_badges` | Array[String] | L | Quality, credibility, author authority | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `quality_dimensions` | Object | L | | `{authority, currency, accuracy, clarity, depth, credibility}` |
| `subtype_classification` | String | L | AI Assessment | One of 6 subtypes. |

### 5.9 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `author_person_id` | String | D | Author name + credentials → Person entity. |
| `institution_entity_id` | String | D | For institutional content → Institution via ROR. |
| `website_entity_id` | String | D | Domain → Website/Blog entity. |

---

## 6. Refresh Tiers

| Tier | Scope | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Blog monitoring** | All tracked blog_site resources | Weekly | RSS feed poll for new posts |
| **Non-RSS monitoring** | Institutional guides without RSS | Monthly | ChangeDetection.io |
| **Content check** | All web content | Quarterly | Link check (HTTP status), content change detection |
| **Archive** | Stable institutional guides | Biannually | Link check, Wayback snapshot |

**Highest link rot risk type.** Web content disappears more frequently than any other resource type. Wayback/Perma.cc archival is critical.

---

## 7. Field Summary

### Individual Web Content

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~22 | title, author, publication_date, word_count, content_text, categories, favicon |
| Derived (D) | ~10 | url, reading_time, publication_year, outbound analysis, archive_url, entity IDs |
| LLM-authored (L) | ~10 | editorial_description, credibility_assessment, methodology_tags, quality_score |
| **Total web_guide golden record fields** | **~42** | |

### Blog Site (as resource)

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~8 | blog_name, blog_url, description, operator, rss_url, post_frequency |
| Derived (D) | ~4 | is_active, child_article_count, entity IDs |
| LLM-authored (L) | ~6 | editorial_description, primary_topics, methodology_tags |
| **Total blog_site golden record fields** | **~18** | |
