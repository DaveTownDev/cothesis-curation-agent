# ResourceSubtype.podcast — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: podcast
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A podcast is an audio series or individual episode — show-level metadata (feed, publisher, hosts) and episode-level metadata (air date, duration, guests) are both captured.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `show_code` | string | No | → PodcastShow.code. Parent show for episode-level resources. |
| `podcast_show_entity_id` | string | No | UUID FK to podcast show entity (legacy; use show_code per P4). |
| `episode_number` | integer | No | Episode number within the series. |
| `season_number` | integer | No | Season number. Null if not season-structured. |
| `duration_seconds` | integer | No | Episode duration in seconds. Cluster E canonical for podcast. Was: `length`, `audio_length_sec`, `enclosure_length`. |
| `duration_display` | string | No | Human-readable duration e.g. `45:12`. Derived from duration_seconds. |
| `transcript_url` | string (uri) | No | URL to episode transcript. |
| `transcript_available` | boolean | No | Whether transcript exists. Derived from transcript_url being non-null, or explicit flag. |
| `air_date` | string (date) | No | Original air/publish date. Cluster D; maps to Resource.publication_date. |
| `rss_guid` | string | No | RSS GUID for the episode (unique in feed). |
| `podcast_index_id` | string | No | Podcast Index database ID. |
| `listen_notes_id` | string | No | Listen Notes ID. |
| `spotify_id` | string | No | Spotify episode/show ID. |
| `podchaser_id` | string | No | Podchaser episode/show ID. |
| `listen_score` | number | No | Listen Notes listen score (show-level metric). |
| `listen_score_percentile` | number | No | Listen Notes percentile ranking. |
| `podchaser_rating` | number | No | Podchaser average rating. |
| `trending_score` | number | No | Trending score from podcast analytics. |
| `total_episodes` | integer | No | For show-level resources: total episode count. |
| `host_person_ids` | string[] | No | → Person.code[] for hosts. |
| `guest_person_ids` | string[] | No | → Person.code[] for guests in this episode. |
| `has_chapters` | boolean | No | Whether episode has chapter markers. |
| `chapters` | object[] | No | Chapter markers: `[{time_seconds, title}]`. |
| `social_links` | object | No | Social media links for the show: `{twitter, instagram, facebook, ...}`. |
| `artwork_url` | string (uri) | No | Show/episode artwork. Cluster F; maps to thumbnail_url on Resource base. |
| `is_dead` | boolean | No | Whether the podcast show is no longer active. Cluster K. |
| `primary_topics` | string[] | No | AI-assessed primary topics for the show/episode. |
| `relevant_episode_count` | integer | No | AI signal: number of relevant episodes in the show. |
| `host_expertise_assessment` | string | No | AI assessment of host expertise level. |

## Notes

- Podcast covers both show-level and episode-level records. Show-level fields (`total_episodes`, `host_person_ids`, `listen_score`, `artwork_url`, `social_links`, `is_dead`) are populated for show-type resources. Episode-level fields (`episode_number`, `season_number`, `air_date`, `rss_guid`) for episode-type resources.
- `duration_seconds` is the canonical Cluster E name for podcast; legacy aliases (`length`, `audio_length_sec`, `enclosure_length`, `duration_ms`) are not stored.
- `transcript_url` is more precise than `transcript_available` boolean — if transcript_url is populated, transcript is available.
