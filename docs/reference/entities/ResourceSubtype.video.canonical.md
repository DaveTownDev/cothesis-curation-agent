# ResourceSubtype.video — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: video
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A video is a recorded educational or reference video — YouTube, Vimeo, JoVE, or other platform — including individual videos and channel-level metadata.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `platform_code` | string | No | → ContentPlatform.code. Platform hosting the video e.g. `youtube`, `vimeo`, `jove`, `coursera`. |
| `channel_code` | string | No | → ContentChannel.code (YouTube channel or equivalent platform channel). Was: `youtube_channel_entity_id`, `podcast_show_entity_id` pattern. |
| `youtube_video_id` | string | No | YouTube video ID (for embed and API lookup). |
| `vimeo_id` | string | No | Vimeo video ID. |
| `duration_seconds` | integer | No | Video duration in seconds. Cluster E canonical for video. Was: `duration`, `duration_ms`, `duration_minutes`. |
| `duration_display` | string | No | Human-readable duration e.g. `12:34`. Derived from duration_seconds. |
| `view_count` | integer | No | Total view count (from platform API). |
| `like_count` | integer | No | Total like count. |
| `comment_count` | integer | No | Total comment count. |
| `total_video_count` | integer | No | For channel-level records: total videos in channel. |
| `total_view_count` | integer | No | For channel-level records: total channel views. |
| `subscriber_count` | integer | No | Channel subscriber count. |
| `channel_avatar_url` | string (uri) | No | Channel avatar/profile image. Cluster F. |
| `banner_url` | string (uri) | No | Channel banner image. Cluster F. |
| `transcript_available` | boolean | No | Whether a transcript is available. |
| `transcript_source` | string | No | Source of transcript e.g. `auto-generated`, `manual`, `third_party`. |
| `transcript_language` | string | No | ISO 639-1 language of transcript. |
| `captions_available` | boolean | No | Whether closed captions are available. |
| `presenter_person_ids` | string[] | No | → Person.code[] for presenters/speakers. |
| `guest_person_ids` | string[] | No | → Person.code[] for guests. |
| `video_categories` | string[] | No | Platform category tags (YouTube categories etc). Maps to topic_tags on Resource base. |
| `is_jove` | boolean | No | Whether this is a JoVE (Journal of Visualized Experiments) video — triggers article-style pipeline. |
| `jove_doi` | string | No | DOI for JoVE videos (which are also citable publications). |
| `software_resource_code` | string | No | → Resource.code of a software resource demonstrated in this video (cross-ref). |
| `conference_entity_id` | string | No | → Conference entity if this is a conference presentation recording. |
| `relevant_video_count` | integer | No | AI signal: number of relevant videos in the parent channel (for channel-level assessment). |
| `engagement_ratio` | number | No | Derived engagement ratio (likes/views). |

## Notes

- Video covers both individual videos and channel-level records. Channel-level fields (`total_video_count`, `total_view_count`, `subscriber_count`, `channel_avatar_url`, `banner_url`) are populated for channel-type resources.
- JoVE videos trigger the article-style pipeline in addition to video-style processing (`is_jove=true`).
- Cluster E duration: `duration_seconds` is canonical. `duration_display` is derived.
- `relevant_video_count` is an AIAssessment-generated signal; stored here on the resource as a denormalised subtype field.
