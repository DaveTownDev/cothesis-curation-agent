# CoThesis Compendium — Complete Field Mapping & Merge Logic: `video`

**Type:** Videos
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `video_tutorial`, `video_lecture`, `video_explainer`, `video_software_demo`, `video_channel`, `video_interview`

**Note:** The `video_channel` subtype is both a resource AND a container entity (YouTube Channel). Individual video resources link to their parent channel via `youtube_channel_id`. The channel entity is fully defined in `secondary_entity_reference.md`; this document covers the channel-as-resource golden record fields.

---

## 1. Architecture

### Individual Video Record

```
video_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── video_source_youtube_api
  │     ├── video_source_youtube_transcript
  │     ├── video_source_whisper (local transcription)
  │     ├── video_source_vimeo (if Vimeo-hosted)
  │     ├── video_source_jove (if JoVE video)
  │     ├── video_source_scrape_platform (non-YouTube/Vimeo platforms)
  │     ├── video_source_discovery
  │     └── video_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (creator, presenter, guest)
  │     ├── youtube_channel_entity_id (link to Channel entity)
  │     ├── content_platform_id (YouTube, Vimeo, institutional)
  │     ├── institution_entity_id (for institutional lectures)
  │     └── software_resource_id (cross-ref for software_demo subtype)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

### Video Channel Record (as resource)

```
video_channel_master (golden record — also the YouTube Channel entity)
  │
  ├── Source Sub-Records
  │     ├── channel_source_youtube_api (channel endpoint)
  │     ├── channel_source_youtube_rss
  │     ├── channel_source_discovery
  │     └── channel_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_id (channel creator)
  │     ├── content_platform_id (always YouTube for now)
  │     └── child_video_resource_ids[] (videos from this channel in directory)
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
| 1 | YouTube Data API v3 | `youtube_api` | T1 | 10K units/day (~100-200 practical req/day) | Yes (API key) | Authoritative for all YouTube-hosted video metadata |
| 2 | youtube-transcript-api | `yt_transcript` | T1 | Generous (Python library) | Yes | Best source for caption/transcript text |
| 3 | JoVE | `jove` | T1 | N/A (scrape) | Paid (institutional) | Authoritative for peer-reviewed scientific video protocols |
| 4 | Whisper (local) | `whisper` | T1 | CPU/GPU bound | Yes (local model) | Fallback transcription when captions unavailable |
| 5 | Vimeo API | `vimeo` | T2 | Varies by plan | Yes (basic) | For Vimeo-hosted academic videos |
| 6 | Platform scrape | `scrape_platform` | T2 | N/A | Free | For institutional platforms (Panopto, Kaltura, NIH VideoCast) |
| 7 | Discovery record | `discovery` | — | N/A | N/A | Agent-provided |

**Enrichment tier assignments:**

| Enrichment Tier | Which Videos | Sources Called |
|----------------|-------------|---------------|
| Tier 1 (every video) | All YouTube videos | YouTube API (video endpoint) + youtube-transcript-api + AI assessment |
| Tier 2 (quality enrichment) | Videos with > 10K views OR badged | + Whisper (if no captions) |
| Tier 3 (non-YouTube) | Vimeo, institutional, JoVE | Vimeo API / JoVE scrape / platform scrape as applicable |

---

## 3. Source Sub-Record Field Inventories

### 3.1 YouTube Data API v3 — Video Endpoint (`video_source_youtube_api`)

**Lookup key:** YouTube video ID (extracted from URL)
**API endpoint:** `GET https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics,topicDetails,status&id={videoId}&key={key}`
**Quota cost:** 1 unit for `id` filter; parts cost: snippet=0, contentDetails=2, statistics=2, topicDetails=2, status=2 → ~7-9 units per video

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `video_id` | `items[0].id` | String | YouTube video ID |
| `title` | `items[0].snippet.title` | String | Video title |
| `description` | `items[0].snippet.description` | String | Video description (full text, up to 5000 chars) |
| `channel_id` | `items[0].snippet.channelId` | String | Channel ID |
| `channel_title` | `items[0].snippet.channelTitle` | String | Channel name |
| `published_at` | `items[0].snippet.publishedAt` | DateTime | Upload date (ISO 8601) |
| `tags` | `items[0].snippet.tags[]` | Array[String] | Video tags (set by uploader) |
| `category_id` | `items[0].snippet.categoryId` | String | YouTube category ID (27 = Education) |
| `default_language` | `items[0].snippet.defaultLanguage` | String | Language of video metadata |
| `default_audio_language` | `items[0].snippet.defaultAudioLanguage` | String | Language of audio |
| `thumbnail_default` | `items[0].snippet.thumbnails.default.url` | String | Thumbnail 120×90 |
| `thumbnail_medium` | `items[0].snippet.thumbnails.medium.url` | String | Thumbnail 320×180 |
| `thumbnail_high` | `items[0].snippet.thumbnails.high.url` | String | Thumbnail 480×360 |
| `thumbnail_standard` | `items[0].snippet.thumbnails.standard.url` | String | Thumbnail 640×480 |
| `thumbnail_maxres` | `items[0].snippet.thumbnails.maxres.url` | String | Thumbnail 1280×720 |
| `live_broadcast_content` | `items[0].snippet.liveBroadcastContent` | String | none, live, upcoming |
| `duration` | `items[0].contentDetails.duration` | String | ISO 8601 duration (e.g., PT1H23M45S) |
| `dimension` | `items[0].contentDetails.dimension` | String | 2d or 3d |
| `definition` | `items[0].contentDetails.definition` | String | hd or sd |
| `caption` | `items[0].contentDetails.caption` | String | "true" or "false" — whether captions available |
| `licensed_content` | `items[0].contentDetails.licensedContent` | Boolean | Whether content is licensed |
| `projection` | `items[0].contentDetails.projection` | String | rectangular or 360 |
| `view_count` | `items[0].statistics.viewCount` | String (Integer) | Number of views |
| `like_count` | `items[0].statistics.likeCount` | String (Integer) | Number of likes |
| `dislike_count` | `items[0].statistics.dislikeCount` | String (Integer) | Dislikes (may be hidden) |
| `favorite_count` | `items[0].statistics.favoriteCount` | String (Integer) | Favourites |
| `comment_count` | `items[0].statistics.commentCount` | String (Integer) | Number of comments |
| `topic_categories` | `items[0].topicDetails.topicCategories[]` | Array[String] | Wikipedia URLs for topics (e.g., "https://en.wikipedia.org/wiki/Statistics") |
| `upload_status` | `items[0].status.uploadStatus` | String | processed, failed, etc. |
| `privacy_status` | `items[0].status.privacyStatus` | String | public, unlisted, private |
| `license` | `items[0].status.license` | String | youtube or creativeCommon |
| `embeddable` | `items[0].status.embeddable` | Boolean | Whether embeddable |
| `made_for_kids` | `items[0].status.madeForKids` | Boolean | |

---

### 3.2 YouTube Data API v3 — Channel Endpoint (`channel_source_youtube_api`)

**Lookup key:** Channel ID
**API endpoint:** `GET https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails,statistics,topicDetails,brandingSettings&id={channelId}&key={key}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `channel_id` | `items[0].id` | String | Channel ID |
| `title` | `items[0].snippet.title` | String | Channel name |
| `description` | `items[0].snippet.description` | String | Channel description |
| `custom_url` | `items[0].snippet.customUrl` | String | Custom URL (e.g., @StatQuest) |
| `published_at` | `items[0].snippet.publishedAt` | DateTime | Channel creation date |
| `country` | `items[0].snippet.country` | String | Channel country |
| `thumbnail_default` | `items[0].snippet.thumbnails.default.url` | String | Channel avatar (88×88) |
| `thumbnail_medium` | `items[0].snippet.thumbnails.medium.url` | String | Avatar 240×240 |
| `thumbnail_high` | `items[0].snippet.thumbnails.high.url` | String | Avatar 800×800 |
| `banner_url` | `items[0].brandingSettings.image.bannerExternalUrl` | String | Channel banner image |
| `uploads_playlist_id` | `items[0].contentDetails.relatedPlaylists.uploads` | String | Playlist ID for all uploads |
| `view_count` | `items[0].statistics.viewCount` | String (Integer) | Total channel views |
| `subscriber_count` | `items[0].statistics.subscriberCount` | String (Integer) | Subscribers (may be hidden) |
| `hidden_subscriber_count` | `items[0].statistics.hiddenSubscriberCount` | Boolean | Whether sub count is hidden |
| `video_count` | `items[0].statistics.videoCount` | String (Integer) | Total videos |
| `topic_categories` | `items[0].topicDetails.topicCategories[]` | Array[String] | Wikipedia topic URLs |
| `keywords` | `items[0].brandingSettings.channel.keywords` | String | Channel keywords (space-separated) |
| `unsubscribed_trailer` | `items[0].brandingSettings.channel.unsubscribedTrailer` | String | Featured video ID for non-subscribers |

---

### 3.3 YouTube Transcript (`video_source_youtube_transcript`)

**Lookup key:** YouTube video ID
**Library:** `youtube-transcript-api` (Python)
**Access:** `YouTubeTranscriptApi.get_transcript(video_id)`

| Field | Type | Description |
|-------|------|-------------|
| `transcript_text` | Text | Full transcript as continuous text (assembled from segments) |
| `transcript_segments` | Array[Object] | Individual segments: `{text, start, duration}` |
| `transcript_language` | String | Language of transcript |
| `is_auto_generated` | Boolean | Whether auto-generated (vs manually created) |
| `available_languages` | Array[String] | All available transcript languages |
| `transcript_word_count` | Integer | Word count of full transcript |

**Priority:** Manual captions > auto-generated captions. The library can detect which type is available via `YouTubeTranscriptApi.list_transcripts(video_id)`.

---

### 3.4 Whisper Local Transcription (`video_source_whisper`)

**Triggered:** Only when youtube-transcript-api returns no transcript (no captions available)
**Tool:** OpenAI Whisper (local via Ollama or standalone)

| Field | Type | Description |
|-------|------|-------------|
| `whisper_transcript` | Text | Full transcription |
| `whisper_language` | String | Detected language |
| `whisper_model` | String | Model used (tiny, base, small, medium, large) |
| `whisper_word_count` | Integer | Word count |
| `whisper_confidence` | Float | Average confidence score |
| `whisper_segments` | Array[Object] | Segments with timestamps: `{text, start, end}` |

---

### 3.5 Vimeo API (`video_source_vimeo`)

**Lookup key:** Vimeo video ID (from URL)
**API endpoint:** `GET https://api.vimeo.com/videos/{video_id}` (OAuth required)

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `vimeo_id` | `uri` | String | Vimeo video URI |
| `title` | `name` | String | Video title |
| `description` | `description` | String | Description |
| `duration` | `duration` | Integer | Duration in seconds |
| `width` | `width` | Integer | Video width |
| `height` | `height` | Integer | Video height |
| `language` | `language` | String | Language |
| `created_time` | `created_time` | DateTime | Upload date |
| `modified_time` | `modified_time` | DateTime | Last modified |
| `privacy` | `privacy.view` | String | anybody, nobody, password, etc. |
| `license` | `license` | String | CC license if applicable |
| `embed_html` | `embed.html` | String | Embed code |
| `stats_plays` | `stats.plays` | Integer | Play count |
| `tags` | `tags[].name` | Array[String] | Tags |
| `categories` | `categories[].name` | Array[String] | Categories |
| `pictures` | `pictures.sizes[]` | Array[Object] | Thumbnail URLs at various sizes |
| `user_name` | `user.name` | String | Uploader name |
| `user_uri` | `user.uri` | String | Uploader profile URI |
| `download` | `download[]` | Array[Object] | Download links (if allowed) |
| `has_text_tracks` | `has_text_tracks` | Boolean | Whether captions available |
| `text_tracks` | `text_tracks[].uri` | Array[Object] | Caption track URIs with languages |

---

### 3.6 JoVE (`video_source_jove`)

**Lookup key:** JoVE article/video ID or DOI
**Source:** Scrape from jove.com (PubMed-indexed — can also get PMID)
**Note:** Full video access requires institutional subscription; metadata is scrapeable

| Field | Type | Description |
|-------|------|-------------|
| `jove_id` | String | JoVE video/article ID |
| `doi` | String | DOI (JoVE assigns DOIs) |
| `pmid` | String | PubMed ID (JoVE is indexed in PubMed) |
| `title` | String | Video title |
| `abstract` | Text | Video abstract/protocol description |
| `authors` | Array[Object] | Authors with affiliations |
| `section` | String | JoVE section (Biology, Medicine, Chemistry, etc.) |
| `published_date` | Date | Publication date |
| `protocol_steps` | Array[String] | Written protocol steps accompanying the video |
| `materials_list` | Array[Object] | Materials/reagents used (for lab protocols) |
| `keywords` | Array[String] | Keywords |
| `duration_minutes` | Integer | Video length |
| `thumbnail_url` | String | Video thumbnail |
| `jove_url` | String | JoVE page URL |
| `is_open_access` | Boolean | Whether freely accessible |
| `citation` | String | Formatted citation |

**Why JoVE is T1:** JoVE videos are peer-reviewed, PubMed-indexed scientific video protocols. They can be enriched with PubMed and CrossRef data using the same pipeline as articles (via DOI/PMID). This crossover with the article enrichment pipeline is a significant advantage.

---

### 3.7 Platform Scrape (`video_source_scrape_platform`)

**For:** Institutional platforms (NIH VideoCast, university Panopto/Kaltura instances, conference recordings)

| Field | Type | Description |
|-------|------|-------------|
| `platform_name` | String | Platform name (e.g., "NIH VideoCast") |
| `platform_url` | String | Video page URL |
| `title` | String | Video title |
| `description` | Text | Description |
| `presenter` | String | Presenter name |
| `presenter_credentials` | String | Presenter qualifications (if shown) |
| `date` | Date | Recording/upload date |
| `duration` | String | Duration (various formats) |
| `event_name` | String | Event/seminar/workshop name (if applicable) |
| `thumbnail_url` | String | Thumbnail |
| `has_captions` | Boolean | Whether captions available |
| `download_url` | String | Download link (if available) |
| `institution` | String | Hosting institution |

---

### 3.8 Discovery Record (`video_source_discovery`)

Same structure as article/book discovery record.

| Field | Type | Description |
|-------|------|-------------|
| `discovered_url` | String | URL where video was found |
| `discovered_at` | DateTime | When discovered |
| `discovered_by` | String | Agent name or "manual" |
| `discovery_source_name` | String | Source website/database name |
| `discovery_source_url` | String | URL of discovery page |
| `discovery_context` | Text | How the source described this video |
| `agent_assigned_type` | String | Resource type from 46-type list |
| `agent_description` | Text | Agent-written description |
| `agent_methodology_relevance` | Text | Methodology relevance assessment |
| `agent_access_type` | String | free, freemium, paid, subscription, institutional |

---

### 3.9 AI Assessment Record (`video_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Overall quality |
| `quality_dimensions` | Object | `{authority, currency, relevance, accuracy, pedagogy, production_quality}` — note extra dimension for video |
| `confidence` | Float (0–1) | AI confidence |
| `methodology_tags` | Array[String] | From 162-methodology taxonomy |
| `thesis_stages` | Array[String] | THESIS stage tags |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | Medical specialty relevance |
| `subtype_classification` | String | video_tutorial, video_lecture, video_explainer, video_software_demo, video_interview |
| `editorial_description` | Text | Original 1–2 sentence description |
| `editorial_description_long` | Text | Extended 3–5 sentence description |
| `editorial_badges` | Array[String] | Recommended badges (max 3) |
| `software_demonstrated` | String | For software_demo subtype: which software tool is shown |
| `guest_names` | Array[String] | For interview subtype: extracted guest names |
| `key_topics_covered` | Array[String] | Main topics identified from transcript analysis |
| `assessed_at` | DateTime | Assessment timestamp |
| `model_used` | String | AI model identifier |
| `requires_human_review` | Boolean | Below confidence threshold |

**Note:** Video AI assessment is uniquely enhanced by transcript availability. When a transcript exists, the AI can perform much deeper content analysis (topic extraction, methodology identification, difficulty assessment) than from title+description alone.

---

## 4. Secondary Entity Links

### 4.1 Person (Creator/Presenter/Guest)

**Relationships:**
- `video -[CREATED_BY]-> person` (channel owner/video creator)
- `video -[PRESENTED_BY]-> person` (on-screen presenter, may differ from channel owner)
- `video -[FEATURES_GUEST]-> person` (for video_interview subtype)

**Resolution:** Extract names from video description, channel info, and transcript (intro sections). Match to Person entity via name + field/credentials.

**Cardinality:** One-to-many (a video may have multiple presenters/guests)

### 4.2 YouTube Channel (Container Entity)

**Relationship:** `video -[PART_OF]-> youtube_channel`
**Cardinality:** Many-to-one (many videos belong to one channel)
**Resolution:** `channel_id` from YouTube API video response directly links to channel.
**Entity defined in:** `secondary_entity_reference.md`

### 4.3 Content Platform

**Relationship:** `video -[HOSTED_ON]-> content_platform`
**Cardinality:** Many-to-one
**Values:** YouTube, Vimeo, NIH VideoCast, Panopto, Kaltura, JoVE, institutional

### 4.4 Institution

**Relationship:** `video -[PRODUCED_BY]-> institution`
**Cardinality:** Many-to-one (optional — for institutional lecture recordings)
**Resolution:** Via institution name in video description or channel info → ROR match

### 4.5 Software (Cross-Reference)

**Relationship:** `video -[DEMONSTRATES]-> software`
**Cardinality:** Many-to-one (for software_demo subtype only)
**Resolution:** AI classification identifies which software is being demonstrated → match to software resource record

---

## 5. Golden Record Merge Rules — Individual Video

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `youtube_video_id` | String | V | YouTube API | Single source. Null for non-YouTube videos. |
| `vimeo_id` | String | V | Vimeo API | Single source. Null for non-Vimeo. |
| `jove_id` | String | V | JoVE scrape | Single source. |
| `doi` | String | V | JoVE → CrossRef (for JoVE videos with DOIs) | JoVE videos have DOIs; most YouTube videos do not. |
| `pmid` | String | V | PubMed (for JoVE videos) | JoVE is PubMed-indexed. |
| `url` | String | D | Derived | `https://www.youtube.com/watch?v={video_id}` for YouTube; Vimeo/JoVE/platform URL otherwise. |
| `embed_url` | String | D | Derived | `https://www.youtube.com/embed/{video_id}` for YouTube; Vimeo `embed.html`; platform embed if available. |

### 5.2 Content Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `title` | String | V | YouTube API → Vimeo → JoVE → scrape_platform → Discovery | First non-null. |
| `description` | Text | V | YouTube API `description` → Vimeo `description` → JoVE `abstract` → scrape_platform | Full description text. |
| `duration_seconds` | Integer | D | Derived | Parse YouTube ISO 8601 duration (PT1H23M45S → 4985). Vimeo provides seconds directly. JoVE: `duration_minutes * 60`. |
| `duration_display` | String | D | Derived | Human-readable: "1h 23m 45s" or "23:45". |
| `language` | String | V | YouTube `defaultAudioLanguage` → Vimeo `language` → transcript detection | ISO 639-1. |
| `published_date` | Date | V | YouTube `publishedAt` → Vimeo `created_time` → JoVE `published_date` → scrape_platform | Normalise to ISO 8601 date. |
| `publication_year` | Integer | D | Derived from `published_date` | |
| `tags` | Array[String] | V | YouTube `tags` → Vimeo `tags` | Uploader-assigned tags. |
| `license` | String | V | YouTube `status.license` → Vimeo `license` → JoVE (CC status) | `youtube` = standard YouTube license; `creativeCommon` = CC-BY. |
| `is_creative_commons` | Boolean | D | Derived | `true` if `license` is any CC variant. |

### 5.3 Engagement Metrics

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `view_count` | Integer | V | YouTube `viewCount` → Vimeo `stats.plays` | Parse from string to integer. |
| `like_count` | Integer | V | YouTube `likeCount` | YouTube only. |
| `comment_count` | Integer | V | YouTube `commentCount` | YouTube only. |
| `engagement_ratio` | Float | D | Derived | `(like_count + comment_count) / view_count`. Measure of audience engagement quality. |

### 5.4 Visual Assets

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `thumbnail_url` | String | V | YouTube `maxres` → YouTube `high` → Vimeo largest → JoVE → scrape_platform | Highest resolution available. |
| `thumbnail_small` | String | V | YouTube `medium` → Vimeo smallest | For card display. |
| `definition` | String | V | YouTube `contentDetails.definition` | `hd` or `sd`. |
| `is_embeddable` | Boolean | V | YouTube `status.embeddable` → Vimeo `privacy` (if "anybody") | Whether we can embed the video. |

### 5.5 Transcript

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `transcript` | Text | V | youtube-transcript-api (manual captions) → youtube-transcript-api (auto captions) → Whisper → JoVE `protocol_steps` | **Priority: manual captions > auto captions > Whisper transcription.** |
| `transcript_source` | String | D | Derived | `manual_captions`, `auto_captions`, `whisper`, `jove_protocol`, `none`. |
| `transcript_language` | String | V | youtube-transcript-api → Whisper detection | |
| `transcript_word_count` | Integer | D | Derived | Word count of transcript text. |
| `has_transcript` | Boolean | D | Derived | `true` if transcript is non-null. |
| `available_transcript_languages` | Array[String] | V | youtube-transcript-api `list_transcripts()` | All languages with available transcripts. |

### 5.6 Channel Information (Denormalised)

These are denormalised from the parent YouTube Channel entity for display convenience:

| Golden Field | Type | Cat | Source | Merge Rule |
|-------------|------|-----|--------|------------|
| `channel_name` | String | V | YouTube API `channelTitle` | Denormalised for card display. |
| `channel_id` | String | V | YouTube API `channelId` | For entity linking. |
| `youtube_channel_entity_id` | String | D | Entity resolution | Link to YouTube Channel entity. |

### 5.7 Classification & Typing

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `video_subtype` | String | L | AI Assessment | video_tutorial, video_lecture, video_explainer, video_software_demo, video_interview. |
| `methodology_tags` | Array[String] | L | AI Assessment | From 162-methodology taxonomy. Based on title + description + transcript. |
| `thesis_stages` | Array[String] | L | AI Assessment | THESIS stage tags. |
| `difficulty_level` | String | L | AI Assessment | beginner, intermediate, advanced. |
| `specialty_tags` | Array[String] | L | AI Assessment | Medical specialty relevance. |
| `key_topics_covered` | Array[String] | L | AI Assessment | Main topics from transcript analysis. |
| `youtube_topic_categories` | Array[String] | V | YouTube `topicDetails.topicCategories` | Wikipedia topic URLs — provides rough topic signal. |
| `youtube_category_id` | String | V | YouTube `categoryId` | YouTube category (27 = Education). |

### 5.8 LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Generation Notes |
|-------------|------|-----|--------------|-----------------|
| `editorial_description` | Text (1–2 sentences) | L | Title, description, channel, transcript (first 500 words), methodology tags | Original. Written for trainees. E.g., "A step-by-step walkthrough of running a thematic analysis in NVivo 14, from initial coding to theme development, by the StatQuest team." |
| `editorial_description_long` | Text (3–5 sentences) | L | All source data including transcript analysis | Extended description for detail page. |
| `video_subtype` | String | L | Title, description, transcript content | Classification of video type. |
| `software_demonstrated` | String | L | For software_demo: AI identifies which tool | Cross-reference to software resource. |
| `guest_names` | Array[String] | L | For interview: AI extracts guest names from description/transcript intro | For entity resolution. |
| `editorial_badges` | Array[String] | L | Quality, views, engagement, channel authority | Max 3. AI recommends, human confirms. |
| `quality_score` | Float (0–1) | L | All source data | Multi-dimensional: authority, currency, relevance, accuracy, pedagogy, production_quality. |
| `quality_dimensions` | Object | L | All source data | `{authority, currency, relevance, accuracy, pedagogy, production_quality}`. |

### 5.9 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `creator_person_id` | String | D | Channel owner matched to Person entity. |
| `presenter_person_ids` | Array[String] | D | Extracted from description/transcript → Person entity match. |
| `guest_person_ids` | Array[String] | D | For interviews: `guest_names` → Person entity match. |
| `youtube_channel_entity_id` | String | D | `channel_id` → YouTube Channel entity. |
| `content_platform_id` | String | D | YouTube/Vimeo/institutional platform → Content Platform entity. |
| `institution_entity_id` | String | D | For institutional lectures → Institution entity via ROR. |
| `software_resource_id` | String | D | For software_demo → Software resource record via `software_demonstrated` name match. |

### 5.10 Subtype-Specific Fields

| Field | Applies To | Source | Description |
|-------|-----------|--------|-------------|
| `software_demonstrated` | `video_software_demo` | L (AI Assessment) | Name of software being demonstrated |
| `software_resource_id` | `video_software_demo` | D (entity resolution) | Link to software resource record |
| `guest_names` | `video_interview` | L (AI Assessment) | Names of interview guests |
| `guest_person_ids` | `video_interview` | D (entity resolution) | Links to Person entities |
| `event_name` | `video_lecture` | V (YouTube description / scrape_platform) | Conference/seminar/workshop name |
| `protocol_steps` | JoVE videos | V (JoVE scrape) | Written protocol steps |
| `materials_list` | JoVE videos | V (JoVE scrape) | Materials/reagents used |
| `jove_section` | JoVE videos | V (JoVE scrape) | JoVE section (Biology, Medicine, etc.) |

---

## 6. Golden Record Merge Rules — Video Channel (as resource)

When the `video_channel` subtype is created as a resource in the directory, it draws from the YouTube Channel entity plus AI assessment.

### 6.1 Channel Fields

| Golden Field | Type | Cat | Source | Merge Rule |
|-------------|------|-----|--------|------------|
| `youtube_channel_id` | String | V | YouTube API | |
| `channel_name` | String | V | YouTube API `title` | |
| `channel_description` | String | V | YouTube API `description` | Publisher description — not editorial. |
| `channel_custom_url` | String | V | YouTube API `customUrl` | e.g., @StatQuest |
| `channel_created_date` | Date | V | YouTube API `publishedAt` | |
| `channel_country` | String | V | YouTube API `country` | |
| `subscriber_count` | Integer | V | YouTube API `subscriberCount` | May be hidden. |
| `total_video_count` | Integer | V | YouTube API `videoCount` | All videos, not just relevant ones. |
| `total_view_count` | Integer | V | YouTube API `viewCount` | All-time channel views. |
| `channel_avatar_url` | String | V | YouTube API `thumbnails.high.url` | |
| `channel_banner_url` | String | V | YouTube API `bannerExternalUrl` | |
| `channel_keywords` | Array[String] | D | Derived | Parse space-separated `brandingSettings.channel.keywords`. |
| `uploads_playlist_id` | String | V | YouTube API | For enumerating all videos. |
| `rss_feed_url` | String | D | Derived | `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}` |
| `url` | String | D | Derived | `https://www.youtube.com/channel/{channel_id}` or custom URL. |

### 6.2 Channel LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Channel name, description, sample video titles, topics | Why this channel is useful for trainees. |
| `editorial_description_long` | Text | L | All channel data + video sample analysis | Extended description. |
| `relevant_video_count` | Integer | L | AI analysis of video titles/descriptions | How many videos are relevant to research methodology (vs other content). |
| `primary_topics` | Array[String] | L | AI analysis | Main methodology topics covered by this channel. |
| `methodology_tags` | Array[String] | L | AI Assessment | 162-methodology taxonomy. |
| `difficulty_level` | String | L | AI Assessment | Typical content difficulty. |
| `editorial_badges` | Array[String] | L | Quality, subscribers, relevance | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `is_active` | Boolean | D | Derived | Last upload within 6 months (from RSS or playlist check). |
| `creator_person_id` | String | D | Entity resolution | Channel creator → Person entity. |

---

## 7. JoVE Crossover with Article Pipeline

JoVE videos are peer-reviewed and PubMed-indexed. When a JoVE video is discovered, it can be enriched using BOTH the video pipeline AND the article pipeline:

| Source | From Video Pipeline | From Article Pipeline |
|--------|--------------------|-----------------------|
| JoVE scrape | Title, abstract, protocol steps, materials, authors, section, thumbnail | — |
| YouTube API | (if also on YouTube) Video metadata, views, captions | — |
| PubMed | — | PMID, MeSH terms, publication types, structured abstract |
| CrossRef | — | DOI, citation count, references |
| OpenAlex | — | Citation analytics, FWCI, author-institution linking |
| NIH iCite | — | RCR, APT score (if PubMed-indexed) |

**Merge approach:** The JoVE resource golden record is type `video` but carries additional article-derived fields in a `jove_article_enrichment` sub-object. This provides citation metrics and MeSH terms that normal YouTube videos don't have.

---

## 8. Field Provenance & Versioning

Same structure as article and book types.

---

## 9. Refresh Tiers

| Tier | Videos | Frequency | Sources Refreshed |
|------|--------|-----------|-------------------|
| **Hot** | Published < 3 months ago, OR view_count > 100K, OR flagged | Weekly | YouTube API (stats), link check |
| **Warm** | Published 3 months – 2 years, OR view_count > 10K | Monthly | YouTube API (stats), link check |
| **Cold** | Published > 2 years, view_count < 10K | Quarterly | YouTube API (stats — check if deleted/privated), link check |
| **Archive** | Published > 5 years, view_count < 1K, not badged | Biannually | Link check only (detect deleted videos) |

**Channel refresh:** Monthly for active channels (new uploads via RSS). Quarterly subscriber/view count update.

**Monitoring:**
- YouTube RSS feed per channel: polled weekly for new uploads
- Playlist endpoint: enumerate full upload list monthly (RSS only shows last 15)
- Link check: detect deleted/privated videos (YouTube returns 404 or different privacy status)

---

## 10. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| View/like/comment counts | YouTube API | Change continuously for new videos; stabilise over time |
| Subscriber count | YouTube API (channel) | Changes gradually |
| Video deletion/privacy | YouTube API status check | Critical — deleted videos must be flagged |
| Transcript | youtube-transcript-api | Stable after initial creation; captions may be added later |
| JoVE article metrics | PubMed/CrossRef/OpenAlex | Same as article refresh cycle |
| Channel activity | YouTube RSS | Weekly poll for new uploads |

---

## 11. Field Summary

### Individual Video

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim with priority (V) | ~30 | title, description, duration, view_count, like_count, thumbnail, tags, license |
| Derived / computed (D) | ~12 | url, embed_url, duration_seconds, engagement_ratio, has_transcript, entity IDs |
| LLM-authored (L) | ~10 | editorial_description, methodology_tags, thesis_stages, video_subtype, quality_score |
| **Total video golden record fields** | **~52** | |

### Video Channel (as resource)

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~15 | channel_name, description, subscriber_count, video_count, avatar, banner |
| Derived (D) | ~5 | rss_feed_url, url, is_active, channel_keywords |
| LLM-authored (L) | ~8 | editorial_description, relevant_video_count, primary_topics, methodology_tags |
| **Total channel golden record fields** | **~28** | |

---

## 12. Source Coverage Heatmap — Video

| Field Category | YouTube API | YT Transcript | Whisper | Vimeo | JoVE | Platform Scrape |
|---------------|------------|--------------|---------|-------|------|----------------|
| **Identifiers** | ●●● | — | — | ●●○ | ●●○ | ●○○ |
| **Content metadata** | ●●● | — | — | ●●● | ●●● | ●●○ |
| **Engagement** | ●●● | — | — | ●○○ | — | — |
| **Visual assets** | ●●● | — | — | ●●○ | ●○○ | ●○○ |
| **Transcript** | — | ●●● | ●●○ | ●○○ | ●●○ | — |
| **Channel/creator** | ●●● | — | — | ●○○ | ●●○ | ●○○ |
| **Topics/categories** | ●●○ | — | — | ●○○ | ●●○ | — |
| **License** | ●●○ | — | — | ●●○ | ●○○ | — |
| **Scientific metadata** | — | — | — | — | ●●● | — |

**Note:** JoVE is the only video source that provides scientific metadata (DOI, PMID, MeSH terms, protocol steps). For JoVE videos, the article enrichment pipeline supplements the video pipeline.
