# YouTubeChannel — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_YouTubeChannel.md (secondary_entity_reference.md Entity 9)
COMPENDIUM_URL: /library/channels/{slug}

## Purpose

YouTubeChannel is the container entity for YouTube channels that publish content relevant to CoThesis trainees. Rather than embedding channel metadata in every video resource record, a single YouTubeChannel row holds the stable channel identity and statistics. Individual video resources link to their parent channel via `youtube_channel_code`.

YouTubeChannel was not modelled in `cothesis_shared_entity_schema.md`. This canonical definition promotes it to a first-class shared entity with a Compendium page, following the same content-container pattern as PodcastShow.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. Convention: channel name slug, lowercased and hyphenated. e.g. "statquest", "cochrane", "nhmrc". Generated from `channel_name` on first import. |
| `channel_name` | string | yes | — | Channel display name. Source: YouTube Data API v3 `snippet.title`. Renamed from `title` in source for disambiguation with resource title fields. |
| `channel_id` | string | yes | — | YouTube platform channel ID (e.g. "UCxxxxxx"). Immutable platform identifier. Used as the API lookup key. Not the CoThesis identity key (that is `code`). |
| `handle` | string \| null | no | — | YouTube @handle (e.g. "@StatQuest"). Source: YouTube API `snippet.customUrl`. Nullable — not all channels have claimed a handle. |
| `description` | text \| null | no | — | Channel description. Source: YouTube API `snippet.description`. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK array. Disciplines/specialties this channel primarily covers. Sourced from AI assessment of channel description and video topics. |
| `subscriber_count` | integer \| null | no | — | Subscriber count. Source: YouTube API `statistics.subscriberCount`. May be null if the channel has hidden this value. |
| `video_count` | integer \| null | no | — | Total uploaded videos. Source: YouTube API `statistics.videoCount`. |
| `view_count` | integer \| null | no | — | Total channel views. Source: YouTube API `statistics.viewCount`. |
| `channel_url` | string | yes | — | Canonical channel URL. Derived: `https://www.youtube.com/channel/{channel_id}` or `https://www.youtube.com/{handle}` if handle is set. |
| `rss_feed_url` | string | no | — | RSS feed URL. Derived: `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}`. Used for new upload monitoring. |
| `uploads_playlist_id` | string \| null | no | — | YouTube playlist ID for all uploads. Source: YouTube API `contentDetails.relatedPlaylists.uploads`. Used by the ingest pipeline. |
| `creator_person_code` | string \| null | no | Person.code | FK to the Person entity for the channel creator/host, if the channel is run by an individual. Resolved via entity resolution. Renamed from `creator_person_id`. |
| `country_code` | string \| null | no | Country.code | Country associated with the channel. Source: YouTube API `snippet.country`. |
| `published_at` | date \| null | no | — | Channel creation date. Source: YouTube API `snippet.publishedAt`. |
| `relevant_video_count` | integer \| null | no | — | AI assessment — estimated count of videos on this channel relevant to research methodology for trainees. LLM-authored field. |
| `editorial_description` | text \| null | no | — | AI-authored editorial description of why this channel is useful for trainees. LLM-authored field. Distinct from the raw `description`. |
| `primary_topics` | string[] \| null | no | — | AI assessment — main methodology or research topics covered by the channel. LLM-authored field. |
| `is_active` | boolean | no | — | Derived — see Derived Fields. |

## Page Mixin Fields

ATTACHED — YouTubeChannel pages surface at /library/channels/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually matches `code`. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). Sourced from `editorial_description` if set, else `description` excerpt. |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. |
| `is_active` | boolean | Whether the channel page is currently live. |
| `phase` | integer | Rollout phase. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `is_active` | most recent video resource date | True if a video resource linked to this channel was published within the last 6 months. Alternatively derived from YouTube RSS feed last-entry date. |
| `channel_url` | `channel_id`, `handle` | `https://www.youtube.com/{handle}` if handle set, else `https://www.youtube.com/channel/{channel_id}`. |
| `rss_feed_url` | `channel_id` | `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}`. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Contains videos | Resource (video) → YouTubeChannel | YouTubeChannel | `Resource.youtube_channel_code` | One-directional from Resource. Channel carries no reciprocal resource list — query via Resource.youtube_channel_code index. `video_count` is the count proxy. |
| Created by | YouTubeChannel → Person | Person | `creator_person_code` | Nullable FK. One-directional. Person has no reciprocal channel list. |
| Scoped to | YouTubeChannel → ProfessionalDiscipline | ProfessionalDiscipline | `discipline_codes[]` | M:N via FK array. |
| Country | YouTubeChannel → Country | Country | `country_code` | Nullable FK. |

## Notes

- **`code` as identity key:** Source file was keyed on `channel_id` (the platform's own ID). Canonical adds a CoThesis `code` slug as the primary identity key, consistent with all other entities. `channel_id` is retained as the API lookup key and deduplication anchor.
- **`channel_name` rename:** Source uses `title`. Renamed to `channel_name` to avoid collision with resource `title` fields in shared queries.
- **`creator_person_code` rename:** Source uses `creator_person_id`. Renamed to follow P4 (code-based FKs).
- **`rss_feed_url` promoted:** Source treated this as a derived field noted inline. Canonical promotes it to an explicit field (still derived, but named).
- **ContentPlatform relationship not modelled:** YouTube is itself a ContentPlatform entity, but YouTubeChannel does not carry a `content_platform_code` FK. The platform relationship is implicit. This is intentional — all channels in this entity are YouTube channels by definition.
- **`subscriber_count` null handling:** The YouTube API may return null if the channel owner has hidden subscriber counts. The field accepts null explicitly.
- **Monitoring:** YouTube RSS feed polled weekly for new uploads; new videos auto-assessed for relevance and ingested as `video` resources.
- **Refresh cycle:** Monthly for active channels; quarterly for inactive.
- **Estimated records:** 50–100 channels.
