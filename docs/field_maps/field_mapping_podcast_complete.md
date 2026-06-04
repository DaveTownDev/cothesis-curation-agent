# CoThesis Compendium — Complete Field Mapping & Merge Logic: `podcast`

**Type:** Podcasts
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `podcast_show` (container), `podcast_episode` (individual resource)

**Note:** The `podcast_show` subtype is both a resource AND a container entity (Podcast Show). Individual episode resources link to their parent show via `podcast_show_id`. The show entity is fully defined in `secondary_entity_reference.md`; this document covers both show-as-resource and episode golden record fields.

---

## 1. Architecture

### Podcast Episode Record

```
podcast_episode_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── episode_source_rss
  │     ├── episode_source_listen_notes
  │     ├── episode_source_podcast_index
  │     ├── episode_source_podchaser
  │     ├── episode_source_spotify
  │     ├── episode_source_whisper (local transcription)
  │     ├── episode_source_discovery
  │     └── episode_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── podcast_show_entity_id (link to Show entity)
  │     ├── host_person_ids[]
  │     ├── guest_person_ids[]
  │     └── content_platform_ids[] (Apple, Spotify — distribution)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

### Podcast Show Record (as resource)

```
podcast_show_master (golden record — also the Podcast Show entity)
  │
  ├── Source Sub-Records
  │     ├── show_source_rss
  │     ├── show_source_listen_notes
  │     ├── show_source_podcast_index
  │     ├── show_source_podchaser
  │     ├── show_source_itunes
  │     ├── show_source_spotify
  │     ├── show_source_scrape_website
  │     ├── show_source_discovery
  │     └── show_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── host_person_ids[]
  │     ├── content_platform_ids[] (distribution platforms)
  │     └── child_episode_resource_ids[]
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
| 1 | RSS feed | `rss` | T1 | N/A | Yes | Publisher-controlled authoritative source; most current episode data |
| 2 | Listen Notes API | `listen_notes` | T1 | 300 req/mo (free) | Freemium | Best podcast search engine; richest metadata and discovery |
| 3 | Podcast Index API | `podcast_index` | T1 | Auth-based (generous) | Yes (key) | 4M+ podcasts; open-source; decentralised metadata |
| 4 | Podchaser API | `podchaser` | T1 | 25K pts/mo (free) | Freemium | Unique: host/guest credits, reviews, demographics |
| 5 | iTunes Search API | `itunes` | T1 | ~20 req/min | Yes | Apple Podcasts metadata, artwork, ratings |
| 6 | Spotify Web API | `spotify` | T2 | Generous (OAuth) | Yes | Show/episode metadata, Spotify-exclusive shows |
| 7 | Show website | `scrape_website` | T2 | N/A (scrape) | Free | Host bios, guest lists, topic archives, show notes |
| 8 | Whisper (local) | `whisper` | T2 | CPU/GPU bound | Yes | Episode transcription |
| 9 | Discovery record | `discovery` | — | N/A | N/A | Agent-provided |

**Enrichment tier assignments:**

| Tier | Which Podcasts | Sources Called |
|------|---------------|---------------|
| Tier 1 (every show + episode) | All | RSS + Listen Notes + Podcast Index + AI assessment |
| Tier 2 (quality enrichment) | Shows with listen_score > 30 OR badged | + Podchaser + iTunes + Spotify + show website scrape |
| Tier 3 (featured episodes) | Manually flagged or high-value guests | + Whisper transcription |

---

## 3. Source Sub-Record Field Inventories

### 3.1 RSS Feed (`episode_source_rss` / `show_source_rss`)

**Lookup key:** RSS feed URL (discovered via Listen Notes, Podcast Index, or manual)
**Access:** Direct XML parsing of the RSS feed

#### Show-Level Fields (from RSS `<channel>` element)

| Field | XML Path | Data Type | Description |
|-------|----------|-----------|-------------|
| `rss_title` | `channel/title` | String | Show title |
| `rss_description` | `channel/description` | String | Show description (may contain HTML) |
| `rss_link` | `channel/link` | String | Show website URL |
| `rss_language` | `channel/language` | String | Language code (e.g., en-us) |
| `rss_copyright` | `channel/copyright` | String | Copyright notice |
| `rss_author` | `channel/itunes:author` | String | Show author/host |
| `rss_owner_name` | `channel/itunes:owner/itunes:name` | String | Feed owner name |
| `rss_owner_email` | `channel/itunes:owner/itunes:email` | String | Feed owner email |
| `rss_image_url` | `channel/itunes:image/@href` | String | Show artwork URL |
| `rss_categories` | `channel/itunes:category/@text` | Array[String] | iTunes categories (e.g., "Education", "Science") |
| `rss_subcategories` | `channel/itunes:category/itunes:category/@text` | Array[String] | iTunes subcategories |
| `rss_explicit` | `channel/itunes:explicit` | Boolean | Whether explicit content |
| `rss_type` | `channel/itunes:type` | String | `episodic` or `serial` |
| `rss_last_build_date` | `channel/lastBuildDate` | DateTime | When feed was last updated |
| `rss_generator` | `channel/generator` | String | Feed generator software |

#### Episode-Level Fields (from RSS `<item>` elements)

| Field | XML Path | Data Type | Description |
|-------|----------|-----------|-------------|
| `rss_episode_title` | `item/title` | String | Episode title |
| `rss_episode_description` | `item/description` | String | Episode description/show notes (may be HTML) |
| `rss_episode_content_encoded` | `item/content:encoded` | String | Extended show notes (richer HTML) |
| `rss_episode_summary` | `item/itunes:summary` | String | iTunes summary (plain text) |
| `rss_pub_date` | `item/pubDate` | DateTime | Publication date (RFC 2822) |
| `rss_audio_url` | `item/enclosure/@url` | String | Audio file URL |
| `rss_audio_type` | `item/enclosure/@type` | String | MIME type (audio/mpeg, audio/x-m4a, etc.) |
| `rss_audio_length` | `item/enclosure/@length` | Integer | File size in bytes |
| `rss_duration` | `item/itunes:duration` | String | Duration (HH:MM:SS or seconds) |
| `rss_episode_number` | `item/itunes:episode` | Integer | Episode number |
| `rss_season_number` | `item/itunes:season` | Integer | Season number |
| `rss_episode_type` | `item/itunes:episodeType` | String | `full`, `trailer`, `bonus` |
| `rss_guid` | `item/guid` | String | Globally unique identifier |
| `rss_link` | `item/link` | String | Episode web page URL |
| `rss_explicit` | `item/itunes:explicit` | Boolean | Episode-level explicit flag |
| `rss_episode_image` | `item/itunes:image/@href` | String | Episode-specific artwork (if different from show) |
| `rss_transcript_url` | `item/podcast:transcript/@url` | String | Transcript file URL (Podcasting 2.0 tag) |
| `rss_chapters_url` | `item/podcast:chapters/@url` | String | Chapter markers file URL (Podcasting 2.0) |

---

### 3.2 Listen Notes API (`show_source_listen_notes` / `episode_source_listen_notes`)

**Lookup key:** Listen Notes ID, or search by title/keyword
**API endpoint (show):** `GET https://listen-api.listennotes.com/api/v2/podcasts/{id}`
**API endpoint (episode):** `GET https://listen-api.listennotes.com/api/v2/episodes/{id}`

#### Show-Level Fields

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `listennotes_id` | `id` | String | Listen Notes show ID |
| `title` | `title` | String | Show title |
| `description` | `description` | Text | Show description (HTML) |
| `publisher` | `publisher` | String | Publisher/network |
| `image` | `image` | String | Artwork URL (high-res) |
| `thumbnail` | `thumbnail` | String | Artwork thumbnail |
| `website` | `website` | String | Show website URL |
| `language` | `language` | String | Language |
| `country` | `country` | String | Country of origin |
| `rss` | `rss` | String | RSS feed URL |
| `total_episodes` | `total_episodes` | Integer | Total episode count |
| `listen_score` | `listen_score` | Integer | Listen Notes popularity score (0–100) |
| `listen_score_global_rank` | `listen_score_global_rank` | String | Global rank percentile (e.g., "0.5%") |
| `genre_ids` | `genre_ids[]` | Array[Integer] | Genre IDs |
| `itunes_id` | `itunes_id` | Integer | Apple Podcasts ID |
| `explicit_content` | `explicit_content` | Boolean | Whether explicit |
| `latest_episode_id` | `latest_episode_id` | String | Most recent episode ID |
| `latest_pub_date_ms` | `latest_pub_date_ms` | Integer | Latest episode timestamp (ms) |
| `earliest_pub_date_ms` | `earliest_pub_date_ms` | Integer | Earliest episode timestamp (ms) |
| `update_frequency_hours` | `update_frequency_hours` | Integer | Average hours between episodes |
| `audio_length_sec` | `audio_length_sec` | Integer | Average episode length in seconds |
| `looking_for` | `looking_for` | Object | `{sponsors, guests, cohosts, cross_promotion}` — what the show is seeking |
| `is_claimed` | `is_claimed` | Boolean | Whether the publisher has claimed this listing |

#### Episode-Level Fields

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `listennotes_episode_id` | `id` | String | Listen Notes episode ID |
| `title` | `title` | String | Episode title |
| `description` | `description` | Text | Episode description (HTML) |
| `audio` | `audio` | String | Audio URL |
| `audio_length_sec` | `audio_length_sec` | Integer | Duration in seconds |
| `pub_date_ms` | `pub_date_ms` | Integer | Publication timestamp (ms) |
| `image` | `image` | String | Episode artwork |
| `thumbnail` | `thumbnail` | String | Episode thumbnail |
| `link` | `link` | String | Episode web page URL |
| `podcast` | `podcast` | Object | Parent show metadata (id, title, publisher, image) |
| `explicit_content` | `explicit_content` | Boolean | Whether explicit |
| `maybe_audio_invalid` | `maybe_audio_invalid` | Boolean | Whether audio URL may be broken |

---

### 3.3 Podcast Index API (`show_source_podcast_index` / `episode_source_podcast_index`)

**Lookup key:** Podcast Index ID, iTunes ID, or feed URL
**API endpoint (show):** `GET https://api.podcastindex.org/api/1.0/podcasts/byfeedurl?url={rss_url}`
**API endpoint (episodes):** `GET https://api.podcastindex.org/api/1.0/episodes/byfeedid?id={feedId}`

#### Show-Level Fields

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `podcast_index_id` | `feed.id` | Integer | Podcast Index feed ID |
| `title` | `feed.title` | String | Show title |
| `description` | `feed.description` | Text | Description |
| `url` | `feed.url` | String | RSS feed URL |
| `link` | `feed.link` | String | Show website |
| `author` | `feed.author` | String | Author |
| `owner_name` | `feed.ownerName` | String | Feed owner |
| `image` | `feed.image` | String | Artwork URL |
| `artwork` | `feed.artwork` | String | Higher-res artwork |
| `language` | `feed.language` | String | Language |
| `categories` | `feed.categories` | Object | Category ID → name mapping |
| `episode_count` | `feed.episodeCount` | Integer | Total episodes |
| `itunes_id` | `feed.itunesId` | Integer | Apple Podcasts ID |
| `dead` | `feed.dead` | Integer | 0 = active, 1 = dead feed |
| `last_update_time` | `feed.lastUpdateTime` | Integer | Unix timestamp of last update |
| `content_type` | `feed.contentType` | String | Audio MIME type |
| `trending_score` | `feed.trendScore` | Integer | Trending score |
| `funding_url` | `feed.funding.url` | String | Support/donation URL |
| `funding_message` | `feed.funding.message` | String | Funding message |
| `value` | `feed.value` | Object | Value-for-value (V4V) payment info |

#### Episode-Level Fields

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `episode_id` | `items[].id` | Integer | Podcast Index episode ID |
| `title` | `items[].title` | String | Episode title |
| `description` | `items[].description` | Text | Description |
| `date_published` | `items[].datePublished` | Integer | Unix timestamp |
| `enclosure_url` | `items[].enclosureUrl` | String | Audio URL |
| `enclosure_type` | `items[].enclosureType` | String | MIME type |
| `enclosure_length` | `items[].enclosureLength` | Integer | File size bytes |
| `duration` | `items[].duration` | Integer | Duration in seconds |
| `episode` | `items[].episode` | Integer | Episode number |
| `season` | `items[].season` | Integer | Season number |
| `image` | `items[].image` | String | Episode artwork |
| `link` | `items[].link` | String | Episode web page |
| `transcript_url` | `items[].transcriptUrl` | String | Transcript URL (if available) |
| `chapters_url` | `items[].chaptersUrl` | String | Chapter markers URL |
| `soundbite` | `items[].soundbites[]` | Array[Object] | Soundbite clips `{startTime, duration, title}` |
| `persons` | `items[].persons[]` | Array[Object] | People: `{name, role, group, href, img}` — Podcasting 2.0 |

---

### 3.4 Podchaser API (`show_source_podchaser` / `episode_source_podchaser`)

**Lookup key:** Podchaser ID, Apple Podcasts ID, or search
**API endpoint:** GraphQL at `https://api.podchaser.com/graphql`

#### Show-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `podchaser_id` | String | Podchaser podcast ID |
| `title` | String | Show title |
| `description` | Text | Description |
| `image_url` | String | Artwork |
| `rss_url` | String | RSS feed URL |
| `website_url` | String | Show website |
| `language` | String | Language |
| `total_episode_count` | Integer | Episode count |
| `rating` | Float | Podchaser average rating (1–5) |
| `rating_count` | Integer | Number of ratings |
| `review_count` | Integer | Number of text reviews |
| `apple_id` | Integer | Apple Podcasts ID |
| `spotify_id` | String | Spotify ID |
| `categories` | Array[Object] | Categories with IDs |
| `creators` | Array[Object] | Host/guest credits: `{id, name, type, role, episode_count}` |
| `demographics` | Object | Audience demographics (if available) |
| `status` | String | active, inactive, paused |

#### Episode-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `podchaser_episode_id` | String | Podchaser episode ID |
| `title` | String | Episode title |
| `description` | Text | Description |
| `air_date` | Date | Publication date |
| `length` | Integer | Duration in seconds |
| `audio_url` | String | Audio URL |
| `rating` | Float | Episode rating |
| `guests` | Array[Object] | Guest credits: `{id, name, role}` |

---

### 3.5 iTunes Search API (`show_source_itunes`)

**Lookup key:** iTunes ID, or search by term
**API endpoint:** `GET https://itunes.apple.com/lookup?id={itunesId}&entity=podcast`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `itunes_id` | `results[0].collectionId` | Integer | Apple Podcasts ID |
| `name` | `results[0].collectionName` | String | Show name |
| `artist_name` | `results[0].artistName` | String | Publisher/host |
| `artwork_url_30` | `results[0].artworkUrl30` | String | 30px artwork |
| `artwork_url_60` | `results[0].artworkUrl60` | String | 60px artwork |
| `artwork_url_100` | `results[0].artworkUrl100` | String | 100px artwork |
| `artwork_url_600` | `results[0].artworkUrl600` | String | 600px artwork (highest from iTunes) |
| `collection_url` | `results[0].collectionViewUrl` | String | Apple Podcasts URL |
| `feed_url` | `results[0].feedUrl` | String | RSS feed URL |
| `genre_names` | `results[0].genres[]` | Array[String] | Genre names |
| `genre_ids` | `results[0].genreIds[]` | Array[String] | Genre IDs |
| `track_count` | `results[0].trackCount` | Integer | Episode count |
| `release_date` | `results[0].releaseDate` | DateTime | Most recent release |
| `country` | `results[0].country` | String | Country |
| `primary_genre_name` | `results[0].primaryGenreName` | String | Primary genre |
| `content_advisory_rating` | `results[0].contentAdvisoryRating` | String | Clean or Explicit |

---

### 3.6 Spotify Web API (`show_source_spotify` / `episode_source_spotify`)

**Lookup key:** Spotify show/episode ID
**API endpoint (show):** `GET https://api.spotify.com/v1/shows/{id}`
**API endpoint (episode):** `GET https://api.spotify.com/v1/episodes/{id}`
**Auth:** OAuth 2.0 required

#### Show-Level Fields

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `spotify_id` | `id` | String | Spotify show ID |
| `name` | `name` | String | Show name |
| `description` | `description` | String | Description (plain text) |
| `html_description` | `html_description` | String | Description (HTML) |
| `total_episodes` | `total_episodes` | Integer | Episode count |
| `media_type` | `media_type` | String | `audio` or `video` |
| `images` | `images[]` | Array[Object] | Artwork `{url, width, height}` at multiple sizes |
| `languages` | `languages[]` | Array[String] | Languages |
| `explicit` | `explicit` | Boolean | Whether explicit |
| `publisher` | `publisher` | String | Publisher name |
| `external_url` | `external_urls.spotify` | String | Spotify URL |
| `is_externally_hosted` | `is_externally_hosted` | Boolean | Whether hosted outside Spotify |

#### Episode-Level Fields

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `spotify_episode_id` | `id` | String | Spotify episode ID |
| `name` | `name` | String | Episode name |
| `description` | `description` | String | Description |
| `html_description` | `html_description` | String | HTML description |
| `duration_ms` | `duration_ms` | Integer | Duration in milliseconds |
| `release_date` | `release_date` | String | Release date (YYYY-MM-DD) |
| `release_date_precision` | `release_date_precision` | String | `year`, `month`, or `day` |
| `images` | `images[]` | Array[Object] | Episode artwork |
| `language` | `language` | String | Language |
| `explicit` | `explicit` | Boolean | Whether explicit |
| `external_url` | `external_urls.spotify` | String | Spotify episode URL |
| `audio_preview_url` | `audio_preview_url` | String | 30-second preview URL |
| `is_playable` | `is_playable` | Boolean | Whether playable in user's market |

---

### 3.7 Show Website Scrape (`show_source_scrape_website`)

| Field | Type | Description |
|-------|------|-------------|
| `website_url` | String | Show website URL |
| `host_names` | Array[String] | Host names from about page |
| `host_bios` | Array[Text] | Host biographies |
| `host_credentials` | Array[String] | Host qualifications (MD, PhD, etc.) |
| `guest_archive` | Array[Object] | Guest list with episode links |
| `topic_archive` | Array[Object] | Topic/category archive |
| `show_notes_format` | String | How detailed are show notes (minimal, moderate, detailed, transcript) |
| `has_transcript_page` | Boolean | Whether website publishes transcripts |
| `sponsor_info` | Array[String] | Show sponsors (if relevant) |
| `contact_info` | Object | Contact email, social links |
| `social_links` | Object | `{twitter, instagram, linkedin, youtube, facebook}` |

---

### 3.8 Whisper Transcription (`episode_source_whisper`)

Same structure as video Whisper source.

| Field | Type | Description |
|-------|------|-------------|
| `whisper_transcript` | Text | Full transcription |
| `whisper_language` | String | Detected language |
| `whisper_model` | String | Model used |
| `whisper_word_count` | Integer | Word count |
| `whisper_confidence` | Float | Average confidence |
| `whisper_segments` | Array[Object] | Segments with timestamps |

---

### 3.9 Discovery Record

Same structure as previous types.

### 3.10 AI Assessment Records

#### Show AI Assessment (`show_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Overall show quality |
| `quality_dimensions` | Object | `{authority, currency, relevance, consistency, production_quality}` |
| `confidence` | Float (0–1) | AI confidence |
| `methodology_tags` | Array[String] | Primary methodology topics covered |
| `thesis_stages` | Array[String] | THESIS stages |
| `difficulty_level` | String | Typical content difficulty |
| `specialty_tags` | Array[String] | Medical specialty relevance |
| `editorial_description` | Text | Why this show is useful for trainees |
| `editorial_description_long` | Text | Extended description |
| `editorial_badges` | Array[String] | Max 3 |
| `relevant_episode_count` | Integer | How many episodes are relevant to research methodology |
| `primary_topics` | Array[String] | Main topics covered by the show |
| `host_expertise_assessment` | Text | AI assessment of host credibility |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

#### Episode AI Assessment (`episode_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Episode quality |
| `quality_dimensions` | Object | `{authority, currency, relevance, accuracy, pedagogy, production_quality}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | Episode-specific methodology tags (narrower than show) |
| `thesis_stages` | Array[String] | |
| `difficulty_level` | String | |
| `specialty_tags` | Array[String] | |
| `editorial_description` | Text | What this episode covers and why it's useful |
| `guest_expertise` | Text | AI assessment of guest credibility (if guest episode) |
| `key_topics_covered` | Array[String] | Main topics from description/transcript |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Secondary Entity Links

### 4.1 Person (Host/Guest)

**Relationships:**
- `podcast_show -[HOSTED_BY]-> person` (show-level host)
- `podcast_episode -[FEATURES_GUEST]-> person` (episode guest)

**Resolution:** Host names from RSS `itunes:author`, Listen Notes `publisher`, Podchaser `creators`, website scrape `host_names`. Guest names from Podchaser `guests`, episode description parsing, transcript intro parsing. Match to Person entity.

### 4.2 Podcast Show (Container Entity)

**Relationship:** `podcast_episode -[PART_OF]-> podcast_show`
**Cardinality:** Many-to-one
**Resolution:** RSS feed URL is the canonical show identifier; cross-match via Listen Notes ID, iTunes ID, Spotify ID.
**Entity defined in:** `secondary_entity_reference.md`

### 4.3 Content Platform (Distribution)

**Relationship:** `podcast_show -[AVAILABLE_ON]-> content_platform`
**Cardinality:** Many-to-many (a show is on Apple + Spotify + Google + etc.)
**Values:** Apple Podcasts, Spotify, YouTube Music, Amazon Music, Pocket Casts, Overcast

---

## 5. Golden Record Merge Rules — Podcast Show

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `rss_url` | String | V | Listen Notes → Podcast Index → iTunes → manual | Canonical show identifier. |
| `listen_notes_id` | String | V | Listen Notes | Single source. |
| `podcast_index_id` | Integer | V | Podcast Index | Single source. |
| `podchaser_id` | String | V | Podchaser | Single source. |
| `itunes_id` | Integer | V | Listen Notes → iTunes → Podcast Index | Cross-referenced. |
| `spotify_id` | String | V | Spotify lookup → Podchaser | |
| `apple_podcasts_url` | String | D | Derived | `https://podcasts.apple.com/podcast/id{itunes_id}` |
| `spotify_url` | String | D | Derived | `https://open.spotify.com/show/{spotify_id}` |
| `url` | String | D | Derived | Show website URL (from Listen Notes/RSS) → Apple Podcasts URL → Spotify URL. |

### 5.2 Show Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `name` | String | V | RSS `title` → Listen Notes → Podcast Index → iTunes → Spotify | RSS is publisher-controlled. |
| `description` | Text | V | RSS `description` → Listen Notes → Spotify `html_description` | RSS is canonical. Strip HTML for plain text version. |
| `description_plain` | Text | D | Derived | Strip HTML from `description`. |
| `publisher` | String | V | Listen Notes → RSS `itunes:author` → iTunes `artistName` → Spotify | Listen Notes often has cleaner publisher info. |
| `language` | String | V | RSS → Listen Notes → Spotify | Normalise to ISO 639-1. |
| `country` | String | V | Listen Notes → iTunes | |
| `explicit` | Boolean | V | RSS `itunes:explicit` → Listen Notes → Spotify | |
| `show_type` | String | V | RSS `itunes:type` | `episodic` or `serial`. |

### 5.3 Artwork

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `artwork_url` | String | V | iTunes `artworkUrl600` → Podcast Index `artwork` → Listen Notes `image` → RSS `itunes:image` → Spotify largest | iTunes provides highest resolution. |
| `artwork_url_small` | String | V | iTunes `artworkUrl100` → Listen Notes `thumbnail` | For card display. |

### 5.4 Metrics & Popularity

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `total_episodes` | Integer | V+max | Listen Notes (priority), max(LN, PI, iTunes, Spotify) | Store both. |
| `total_episodes_max_source` | String | D | Whichever provided max | |
| `listen_score` | Integer | V | Listen Notes | Sole source. 0–100 popularity score. |
| `listen_score_percentile` | String | V | Listen Notes `listen_score_global_rank` | E.g., "0.5%" = top 0.5% globally. |
| `podchaser_rating` | Float | V | Podchaser | Community rating (1–5). |
| `podchaser_rating_count` | Integer | V | Podchaser | |
| `podchaser_review_count` | Integer | V | Podchaser | |
| `update_frequency_hours` | Integer | V | Listen Notes | Average time between episodes. |
| `average_episode_length_sec` | Integer | V | Listen Notes `audio_length_sec` | |
| `trending_score` | Integer | V | Podcast Index | |

### 5.5 Categories & Classification

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `categories` | Array[String] | D | Merge RSS `itunes:category` + Listen Notes genres + Podcast Index categories + iTunes genres | Deduplicate, normalise. |
| `methodology_tags` | Array[String] | L | AI Assessment | 162-methodology taxonomy. |
| `thesis_stages` | Array[String] | L | AI Assessment | |
| `difficulty_level` | String | L | AI Assessment | |
| `specialty_tags` | Array[String] | L | AI Assessment | |
| `primary_topics` | Array[String] | L | AI Assessment | Main methodology topics. |

### 5.6 Host/Creator Information

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `hosts` | Array[String] | D | Merge Podchaser `creators` (role=host) + RSS `itunes:author` + scrape_website `host_names` | Deduplicate by name similarity. |
| `host_person_ids` | Array[String] | D | Entity resolution | Hosts matched to Person entities. |
| `host_credentials` | Array[String] | V | scrape_website | Only available from website scrape. |
| `social_links` | Object | V | scrape_website | `{twitter, instagram, linkedin, youtube}`. |

### 5.7 Status & Activity

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `is_active` | Boolean | D | Derived | Latest episode within 3 months. Derived from RSS or Listen Notes `latest_pub_date_ms`. |
| `is_dead` | Boolean | V | Podcast Index `dead` | Whether the RSS feed is dead/unreachable. |
| `latest_episode_date` | Date | D | Derived | From RSS last item `pubDate` or Listen Notes `latest_pub_date_ms`. |
| `earliest_episode_date` | Date | V | Listen Notes `earliest_pub_date_ms` | When the show started. |

### 5.8 LLM-Authored Show Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Name, description, host names, topics, listen score | Why this show is useful for trainees. |
| `editorial_description_long` | Text | L | All data + sample episode analysis | Extended description. |
| `relevant_episode_count` | Integer | L | AI analysis of episode titles | How many episodes are relevant. |
| `editorial_badges` | Array[String] | L | Quality, listen score, relevance | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `quality_dimensions` | Object | L | | `{authority, currency, relevance, consistency, production_quality}` |
| `host_expertise_assessment` | Text | L | Host names, credentials, Person entity data | Assessment of host authority. |

---

## 6. Golden Record Merge Rules — Podcast Episode

### 6.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `rss_guid` | String | V | RSS | Canonical episode identifier within the feed. |
| `listen_notes_episode_id` | String | V | Listen Notes | |
| `podcast_index_episode_id` | Integer | V | Podcast Index | |
| `podchaser_episode_id` | String | V | Podchaser | |
| `spotify_episode_id` | String | V | Spotify | |
| `url` | String | D | Derived | RSS `item/link` → episode web page URL → Apple Podcasts episode URL → Spotify URL. |
| `audio_url` | String | V | RSS `enclosure/@url` → Listen Notes `audio` → Podcast Index `enclosureUrl` | RSS is authoritative for audio URL. |

### 6.2 Episode Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `title` | String | V | RSS `title` → Listen Notes → Podcast Index → Podchaser → Spotify | RSS is publisher-controlled. |
| `description` | Text | V | RSS `content:encoded` → RSS `description` → Listen Notes → Spotify `html_description` | Prefer `content:encoded` (richer). Strip HTML for plain version. |
| `description_plain` | Text | D | Derived | Strip HTML. |
| `published_date` | Date | V | RSS `pubDate` → Listen Notes `pub_date_ms` → Podcast Index `datePublished` → Spotify `release_date` | RSS is authoritative. Normalise to ISO 8601. |
| `publication_year` | Integer | D | Derived | |
| `duration_seconds` | Integer | D | Derived | Parse RSS `itunes:duration` (HH:MM:SS → seconds). Or Listen Notes/Spotify/Podcast Index directly. |
| `duration_display` | String | D | Derived | Human-readable: "1h 23m" or "45 min". |
| `episode_number` | Integer | V | RSS `itunes:episode` → Podcast Index `episode` → Podchaser | |
| `season_number` | Integer | V | RSS `itunes:season` → Podcast Index `season` | |
| `episode_type` | String | V | RSS `itunes:episodeType` | `full`, `trailer`, `bonus`. |
| `explicit` | Boolean | V | RSS → Listen Notes → Spotify | |

### 6.3 Episode Artwork

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `episode_artwork_url` | String | V | RSS `itunes:image` → Podcast Index `image` → Listen Notes `image` | Episode-specific artwork. Falls back to show artwork if null. |
| `artwork_url` | String | D | Derived | `episode_artwork_url` if non-null, else parent show `artwork_url`. |

### 6.4 Show Context (Denormalised)

| Golden Field | Source | Notes |
|-------------|--------|-------|
| `show_name` | Parent show `name` | Denormalised for card display. |
| `show_publisher` | Parent show `publisher` | |
| `podcast_show_entity_id` | Parent show entity ID | Link to Podcast Show entity. |

### 6.5 Guests & People

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `guests` | Array[Object] | D | Podchaser `guests` + Podcast Index `persons` (role=guest) + AI extraction from description | Each: `{name, role, credentials}`. Deduplicate. |
| `guest_person_ids` | Array[String] | D | Entity resolution | Guest names → Person entities. |
| `host_person_ids` | Array[String] | D | Inherited from parent show | |

### 6.6 Transcript

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `transcript` | Text | V | RSS `podcast:transcript` (download) → Podcast Index `transcriptUrl` (download) → scrape_website (if published) → Whisper | Priority: publisher-provided > Whisper-generated. |
| `transcript_source` | String | D | Derived | `publisher`, `podcast_index`, `website`, `whisper`, `none`. |
| `transcript_word_count` | Integer | D | Derived | |
| `has_transcript` | Boolean | D | Derived | `true` if transcript is non-null. |

### 6.7 Chapter Markers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `chapters` | Array[Object] | V | RSS `podcast:chapters` (download) → Podcast Index `chaptersUrl` (download) | Each: `{startTime, title, img, url}`. Podcasting 2.0 standard. |
| `has_chapters` | Boolean | D | Derived | `true` if chapters array is non-empty. |

### 6.8 Episode Classification

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `methodology_tags` | Array[String] | L | AI Assessment | Episode-specific (narrower than show). |
| `thesis_stages` | Array[String] | L | AI Assessment | |
| `difficulty_level` | String | L | AI Assessment | |
| `specialty_tags` | Array[String] | L | AI Assessment | |
| `key_topics_covered` | Array[String] | L | AI Assessment | Main topics from description + transcript. |

### 6.9 LLM-Authored Episode Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Title, description, guests, show context, transcript | What this episode covers and why it's useful. |
| `editorial_badges` | Array[String] | L | Quality, guest authority, topic relevance | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `quality_dimensions` | Object | L | | `{authority, currency, relevance, accuracy, pedagogy, production_quality}` |
| `guest_expertise` | Text | L | Guest names, credentials, Person entity data | AI assessment of guest authority. |

---

## 7. Field Provenance & Versioning

Same structure as previous types.

---

## 8. Refresh Tiers

| Tier | Scope | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Show monitoring** | All tracked shows | Weekly | RSS feed poll for new episodes |
| **Show metadata** | Active shows | Monthly | Listen Notes, Podchaser, iTunes (metrics) |
| **Show metadata** | Inactive shows | Quarterly | RSS check (still alive?), Listen Notes |
| **Episode — Hot** | Published < 1 month | Weekly | (Initial enrichment period) |
| **Episode — Stable** | Published > 1 month | No refresh | Episode data is stable after publication |
| **Link check** | All episodes | Monthly | Audio URL validation |

**Key monitoring pattern:** RSS feed polled weekly per show. New episodes auto-assessed for methodology relevance; relevant ones ingested as `podcast_episode` resources. Irrelevant episodes are noted but not ingested.

---

## 9. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| New episodes | RSS feed | Most time-sensitive — weekly poll |
| Listen score | Listen Notes | Changes gradually; monthly sufficient |
| Podchaser ratings | Podchaser | Accumulate slowly |
| Show status (active/dead) | RSS / Podcast Index `dead` flag | Check monthly |
| Audio URL validity | Link checker | Audio hosting may change |
| Episode metadata | RSS | Stable after publication |
| Transcript availability | RSS / Podcast Index | May be added post-publication |

---

## 10. Field Summary

### Podcast Show (as resource)

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~20 | name, description, publisher, language, artwork, listen_score, podchaser_rating |
| Verbatim + max (V+max) | ~1 | total_episodes |
| Derived (D) | ~10 | url, apple_podcasts_url, spotify_url, is_active, categories (merged), hosts |
| LLM-authored (L) | ~8 | editorial_description, methodology_tags, relevant_episode_count, quality_score |
| **Total show golden record fields** | **~39** | |

### Podcast Episode

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~15 | title, description, audio_url, published_date, duration, episode_number, guests |
| Inherited from show (I) | ~3 | show_name, show_publisher, podcast_show_entity_id |
| Derived (D) | ~10 | url, duration_seconds, duration_display, description_plain, has_transcript, artwork |
| LLM-authored (L) | ~7 | editorial_description, methodology_tags, key_topics, quality_score, guest_expertise |
| **Total episode golden record fields** | **~35** | |

---

## 11. Source Coverage Heatmap

### Podcast Show

| Field Category | RSS | LN | PI | Podch | iTunes | Spotify | WebScr |
|---------------|-----|----|----|-------|--------|---------|--------|
| **Identifiers** | ●○○ | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | — |
| **Show metadata** | ●●● | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | ●●○ |
| **Artwork** | ●●○ | ●●○ | ●●○ | ●○○ | ●●● | ●●○ | — |
| **Metrics** | — | ●●● | ●○○ | ●●● | — | — | — |
| **Categories** | ●●○ | ●●○ | ●●○ | ●●○ | ●●○ | — | — |
| **Host/creator info** | ●○○ | ●○○ | — | ●●● | ●○○ | ●○○ | ●●● |
| **Activity status** | ●●● | ●●○ | ●●○ | ●○○ | — | — | — |

### Podcast Episode

| Field Category | RSS | LN | PI | Podch | Spotify | Whisper |
|---------------|-----|----|----|-------|---------|---------|
| **Episode metadata** | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | — |
| **Audio** | ●●● | ●●○ | ●●○ | ●○○ | ●○○ | — |
| **Guests/people** | — | — | ●●● | ●●● | — | — |
| **Transcript** | ●●○ | — | ●●○ | — | — | ●●● |
| **Chapter markers** | ●●○ | — | ●●○ | — | — | — |
| **Show notes** | ●●● | ●●○ | ●○○ | ●○○ | ●●○ | — |

RSS=RSS Feed, LN=Listen Notes, PI=Podcast Index, Podch=Podchaser, WebScr=Website Scrape
