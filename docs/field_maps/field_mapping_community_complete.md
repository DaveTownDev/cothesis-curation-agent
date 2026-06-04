# CoThesis Compendium — Complete Field Mapping & Merge Logic: `community`

**Type:** Communities & Networks
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `online_community`, `professional_network`, `institutional_research_service`, `mailing_list_newsletter`

---

## 1. Architecture

```
community_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── community_source_reddit (API — for subreddits)
  │     ├── community_source_stackexchange (API — for SE sites)
  │     ├── community_source_scrape (website scrape for societies, services, newsletters)
  │     ├── community_source_discovery
  │     └── community_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── content_platform_id (Reddit, Stack Exchange, Substack, etc.)
  │     ├── person_entity_ids[] (moderators/leaders — rare)
  │     └── institution_entity_id (for institutional_research_service)
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
| 1 | Reddit API | `reddit` | T1 | Free (OAuth) | Subreddit metadata, subscriber counts, activity |
| 2 | Stack Exchange API | `stackexchange` | T1 | Free | Site metadata, question counts, tags |
| 3 | Website scrape | `scrape` | T1 | Free | Societies, university services, newsletters |
| 4 | Discovery | `discovery` | — | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Reddit API (`community_source_reddit`)

**Lookup key:** Subreddit name
**API endpoint:** `GET https://oauth.reddit.com/r/{subreddit}/about`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `subreddit_name` | `data.display_name` | String | Subreddit name (e.g., "statistics") |
| `title` | `data.title` | String | Subreddit title |
| `description` | `data.public_description` | String | Public description |
| `description_html` | `data.description_html` | String | Full sidebar description (HTML) |
| `subscribers` | `data.subscribers` | Integer | Subscriber count |
| `active_users` | `data.accounts_active` | Integer | Users online now |
| `created_utc` | `data.created_utc` | Float | Creation timestamp |
| `subreddit_type` | `data.subreddit_type` | String | public, restricted, private |
| `over18` | `data.over18` | Boolean | NSFW flag |
| `url` | `data.url` | String | Subreddit path |
| `icon_img` | `data.icon_img` | String | Community icon |
| `banner_img` | `data.banner_img` | String | Banner image |
| `wiki_enabled` | `data.wiki_enabled` | Boolean | Whether wiki exists |

---

### 3.2 Stack Exchange API (`community_source_stackexchange`)

**Lookup key:** Site name (e.g., "stats" for Cross Validated)
**API endpoint:** `GET https://api.stackexchange.com/2.3/info?site={site}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `site_name` | `items[0].site.name` | String | Site name |
| `site_url` | `items[0].site.site_url` | String | Site URL |
| `api_site_parameter` | `items[0].site.api_site_parameter` | String | API parameter name |
| `logo_url` | `items[0].site.logo_url` | String | Site logo |
| `icon_url` | `items[0].site.icon_url` | String | Site icon |
| `high_resolution_icon` | `items[0].site.high_resolution_icon_url` | String | High-res icon |
| `total_questions` | `items[0].total_questions` | Integer | Total questions |
| `total_answers` | `items[0].total_answers` | Integer | Total answers |
| `total_users` | `items[0].total_users` | Integer | Total registered users |
| `questions_per_minute` | `items[0].questions_per_minute` | Float | Activity rate |
| `answers_per_minute` | `items[0].answers_per_minute` | Float | Answer rate |
| `site_state` | `items[0].site.site_state` | String | normal, closed_beta, open_beta, linked_meta |
| `site_type` | `items[0].site.site_type` | String | main_site, meta_site |
| `launch_date` | `items[0].site.launch_date` | Integer | Unix timestamp |
| `audience` | `items[0].site.audience` | String | Audience description |

---

### 3.3 Website Scrape (`community_source_scrape`)

**For:** Professional societies, university research offices, newsletters

| Field | Type | Description |
|-------|------|-------------|
| `url` | String | Community/service website URL |
| `name` | String | Organisation/community/service name |
| `description` | Text | Description from about page |
| `type` | String | Society, research office, newsletter, forum |
| `membership_type` | String | open, application, institutional, paid |
| `membership_cost` | Float | Annual membership cost (if paid) |
| `member_count` | Integer | Member count (if shown) |
| `geographic_scope` | String | local, national, international |
| `affiliated_institution` | String | University/hospital name (for institutional services) |
| `services_offered` | Array[String] | For research services: statistical consulting, ethics support, etc. |
| `eligibility` | Text | Who can access this service/community |
| `contact_email` | String | Contact email |
| `contact_url` | String | Contact page |
| `social_links` | Object | `{twitter, linkedin, facebook}` |
| `newsletter_frequency` | String | For newsletters: daily, weekly, monthly |
| `newsletter_subscribe_url` | String | Subscription URL |
| `rss_url` | String | RSS feed URL (if available) |
| `logo_url` | String | Logo |
| `last_activity_date` | Date | Most recent visible activity |

---

### 3.4 AI Assessment (`community_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{activity, relevance, expertise_level, accessibility, responsiveness}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | |
| `thesis_stages` | Array[String] | |
| `difficulty_level` | String | |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | |
| `editorial_description` | Text | What this community offers and why it's useful |
| `editorial_description_long` | Text | Extended |
| `editorial_badges` | Array[String] | Max 3 |
| `is_active` | Boolean | Whether community shows recent activity |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Golden Record Merge Rules

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `url` | String | V | Reddit (subreddit URL) → Stack Exchange → scrape → discovery | |
| `name` | String | V | Reddit `title` → SE `site_name` → scrape → discovery | |
| `description` | Text | V | Reddit `public_description` → SE `audience` → scrape | |
| `platform_name` | String | D | Derived | Reddit, Stack Exchange, Substack, LinkedIn, or website name. |
| `member_count` | Integer | V | Reddit `subscribers` → SE `total_users` → scrape | |
| `activity_metric` | Object | D | Derived | `{subscribers, questions_per_day, active_users}` — platform-specific. |
| `is_active` | Boolean | D | Derived | Recent activity (Reddit: posts within 7 days; SE: questions within 30 days; scrape: content within 6 months). |
| `geographic_scope` | String | V | scrape | |
| `membership_type` | String | V | scrape | open, application, paid, institutional. |
| `services_offered` | Array[String] | V | scrape | For institutional services. |
| `eligibility` | Text | V | scrape | Who can access. |
| `icon_url` | String | V | Reddit `icon_img` → SE `icon_url` → scrape `logo_url` | |
| `newsletter_frequency` | String | V | scrape | For mailing_list_newsletter. |
| `newsletter_subscribe_url` | String | V | scrape | |
| `editorial_description` | Text | L | AI Assessment | |
| `editorial_description_long` | Text | L | AI Assessment | |
| `methodology_tags` | Array[String] | L | AI Assessment | |
| `thesis_stages` | Array[String] | L | AI Assessment | |
| `difficulty_level` | String | L | AI Assessment | |
| `editorial_badges` | Array[String] | L | AI Assessment | Max 3. |
| `quality_score` | Float (0–1) | L | AI Assessment | |
| `quality_dimensions` | Object | L | | `{activity, relevance, expertise_level, accessibility, responsiveness}` |
| `subtype_classification` | String | L | AI Assessment | |
| `content_platform_id` | String | D | Entity resolution | → Content Platform entity. |
| `institution_entity_id` | String | D | Entity resolution | For institutional services → Institution. |
| `person_entity_ids` | Array[String] | D | Entity resolution | Moderators/leaders if identifiable. |

---

## 5. Refresh & Field Summary

**Refresh:** Quarterly for Reddit/SE (subscriber/question counts); biannually for societies/services; monthly RSS check for newsletters.

| Category | Count |
|----------|-------|
| Verbatim (V) | ~15 |
| Derived (D) | ~6 |
| LLM-authored (L) | ~8 |
| **Total** | **~29** |
