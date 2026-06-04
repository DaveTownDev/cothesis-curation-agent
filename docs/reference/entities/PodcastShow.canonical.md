# PodcastShow — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_PodcastShow.md (secondary_entity_reference.md Entity 10)
COMPENDIUM_URL: /library/podcasts/{slug}

## Purpose

PodcastShow is the container entity for podcast series that publish content relevant to CoThesis trainees. A single PodcastShow row holds the stable show identity, platform links, and editorial assessment. Individual podcast episode resources link to their parent show via `podcast_show_code`. This avoids embedding show metadata in every episode resource record and enables show-level Compendium pages that list all relevant episodes.

PodcastShow was not modelled in `cothesis_shared_entity_schema.md`. This canonical definition promotes it to a first-class shared entity with a Compendium page, following the same content-container pattern as YouTubeChannel.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. Convention: show name slug, lowercased and hyphenated. e.g. "evidence-based-medicine", "cochrane-podcast", "plenary-session". Generated at first import. Source file had no `code` — this field is added to fill the gap identified in entity_PodcastShow.md §5. |
| `title` | string | yes | — | Show name. Source priority: RSS (publisher-controlled and authoritative) → Listen Notes → iTunes → Spotify. Renamed from `name` in source to align with podcast industry convention ("show title"). |
| `description` | text \| null | no | — | Show description. Source priority: RSS → Listen Notes → Spotify. |
| `publisher_name` | string \| null | no | — | Publisher or network name (free-text). Source priority: Listen Notes → RSS → iTunes. Free-text — podcast networks are generally not resolved to Organisation rows. |
| `rss_url` | string \| null | no | — | RSS feed URL. Source priority: Listen Notes → iTunes → manual. Used for episode monitoring and ingestion. |
| `website_url` | string \| null | no | — | Show website. Source priority: Listen Notes → show website scrape. |
| `artwork_url` | string \| null | no | — | Show artwork URL (highest resolution available). Source priority: iTunes `artworkUrl600` → Spotify → Listen Notes → RSS. |
| `language_code` | string \| null | no | — | Primary language. ISO 639-1 (e.g. "en"). Source priority: RSS → Listen Notes → Spotify. Renamed from `language` for naming consistency. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK array. Disciplines/specialties this show primarily covers. From AI assessment. |
| `platform_urls` | object | no | — | Platform-specific URLs. Shape: `{ spotify: string\|null, apple: string\|null, google: string\|null, rss: string\|null }`. `rss` duplicates `rss_url` for convenience. `apple` is derived from `itunes_id` if set. `spotify` is derived from `spotify_id` if set. |
| `itunes_id` | integer \| null | no | — | Apple Podcasts ID. Source priority: Listen Notes → iTunes lookup. Used to derive `platform_urls.apple`. |
| `spotify_id` | string \| null | no | — | Spotify show ID. Source: Spotify API. Used to derive `platform_urls.spotify`. |
| `episode_count` | integer \| null | no | — | Total episode count. Source priority: Listen Notes (priority, `total_episodes` field) → max across all sources. Renamed from `total_episodes`. |
| `listen_score` | integer \| null | no | — | Listen Notes popularity score (0–100). Sole source: Listen Notes. Null if not available. |
| `update_frequency_hours` | integer \| null | no | — | Average update frequency in hours. Source: Listen Notes `update_frequency_hours`. Renamed from `update_frequency` (source dropped "_hours" ambiguously). |
| `host_person_codes` | string[] | no | Person.code | FK array to Person entities for show hosts. Resolved from RSS author + show website scrape. Renamed from `host_person_ids` per P4. |
| `relevant_episode_count` | integer \| null | no | — | AI assessment — estimated count of episodes relevant to research methodology for trainees. LLM-authored field. |
| `editorial_description` | text \| null | no | — | AI-authored editorial description of why this show is useful for trainees. LLM-authored field. Distinct from the raw `description`. |
| `primary_topics` | string[] \| null | no | — | AI assessment — main methodology or research topics covered by the show. LLM-authored field. |
| `last_published_at` | date \| null | no | — | Date of the most recent episode. Source: RSS feed last-entry date. Used to derive `is_active`. |
| `is_active` | boolean | no | — | Derived — see Derived Fields. |

## Page Mixin Fields

ATTACHED — PodcastShow pages surface at /library/podcasts/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually matches `code`. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). Sourced from `editorial_description` if set, else `description` excerpt. |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. |
| `is_active` | boolean | Whether the show page is currently live. |
| `phase` | integer | Rollout phase. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `is_active` | `last_published_at` | True if `last_published_at` is within the last 3 months. |
| `platform_urls.apple` | `itunes_id` | `https://podcasts.apple.com/podcast/id{itunes_id}` if `itunes_id` is set. |
| `platform_urls.spotify` | `spotify_id` | `https://open.spotify.com/show/{spotify_id}` if `spotify_id` is set. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Contains episodes | Resource (podcast) → PodcastShow | PodcastShow | `Resource.podcast_show_code` | One-directional from Resource. Show carries no reciprocal episode list — query via Resource.podcast_show_code index. `episode_count` is the count proxy. |
| Hosted by | PodcastShow → Person | Person | `host_person_codes[]` | FK array. One-directional. Person has no reciprocal show list. |
| Scoped to | PodcastShow → ProfessionalDiscipline | ProfessionalDiscipline | `discipline_codes[]` | M:N via FK array. |

## Notes

- **`code` added:** Source file had no primary key field — an identified gap. The canonical adds `code` as the CoThesis slug-based identity key, consistent with all other entities.
- **`title` rename:** Source uses `name`. Renamed to `title` to match podcast industry convention (shows have titles, not names) and to avoid ambiguity in shared queries.
- **`update_frequency_hours` rename:** Source uses `update_frequency` (dropping "_hours"). Canonical restores the unit suffix to remove type ambiguity.
- **`language_code` rename:** Source uses `language` (raw string). Renamed to `language_code` to signal ISO 639-1 format and align with Country.default_language and Journal.language_code field naming.
- **`host_person_codes[]` rename:** Source uses `host_person_ids`. Renamed per P4 (code-based FKs).
- **`episode_count` rename:** Source uses `total_episodes`. Renamed for consistency with `video_count` (YouTubeChannel) naming pattern.
- **Multi-platform design:** A single show spans multiple platforms (Apple, Spotify, RSS). `platform_urls` object handles this without a `content_platform_code` FK.
- **ContentPlatform relationship not modelled:** The show-to-platform relationship is implicit via `platform_urls`. A single-FK `content_platform_code` would not represent multi-platform shows accurately.
- **Monitoring:** RSS feeds polled weekly for new episodes; new episodes assessed for relevance and ingested as `podcast_episode` resources.
- **Refresh cycle:** Monthly for active shows; quarterly for inactive.
- **Estimated records:** 30–60 shows.
