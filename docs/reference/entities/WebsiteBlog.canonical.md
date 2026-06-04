# WebsiteBlog — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_WebsiteBlog.md (secondary_entity_reference.md Entity 11)
COMPENDIUM_URL: /library/sites/{slug}

## Purpose

WebsiteBlog is the container entity for curated websites and blogs that publish content relevant to CoThesis trainees — statistics blogs, academic methodology sites, professional organisation news sites, and similar web-based resources. A single WebsiteBlog row holds the stable site identity and editorial assessment. Individual `web_article` resources link to their parent site via `website_blog_code`.

WebsiteBlog serves a dual function noted in the source: the `blog_site` resource subtype and the WebsiteBlog entity represent the same real-world object. The entity exists so multiple `web_article` resources from the same site can be grouped and so the Compendium can surface a "See all articles from this site" page. This dual-nature design is preserved intentionally.

WebsiteBlog was not modelled in `cothesis_shared_entity_schema.md`. This canonical definition promotes it to a first-class shared entity with a Compendium page.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. Convention: site name slug, lowercased and hyphenated. e.g. "statistics-by-jim", "cochrane-community", "stats-and-r". Replaces the system-generated `website_id` from the source file. |
| `name` | string | yes | — | Site name. Source: site title / about page scrape. e.g. "Statistics by Jim". |
| `url` | string | yes | — | Homepage URL. Source: manual / scrape. The canonical URL for the site. |
| `description` | text \| null | no | — | What the site covers. Source: about page / meta description scrape. |
| `site_type` | string | yes | — | Category of website. Enum: "academic_blog" \| "professional_organisation_site" \| "news_site" \| "reference_site" \| "tool_site" \| "other". Manually curated. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK array. Disciplines/specialties this site primarily covers. From AI assessment. |
| `publisher_code` | string \| null | no | Organisation.code | FK to the Organisation that runs this site, if the operator is an organisation. Nullable. Renames and replaces `operator_institution_id` from source. |
| `operator_person_code` | string \| null | no | Person.code | FK to the Person who runs this site, if the operator is an individual. Nullable. Renames `operator_person_id` from source per P4. |
| `operator_name_raw` | string \| null | no | — | Raw operator name string from scrape. Preserved for resolution audit; not displayed directly. Replaces source `operator_name`. |
| `rss_url` | string \| null | no | — | RSS feed URL. Null if site has no feed. Used for new content monitoring. |
| `favicon_url` | string \| null | no | — | Site favicon URL. Source: Favicon API. Used for display in listings. |
| `first_seen` | date \| null | no | — | Earliest known snapshot date. Source: Wayback Machine API. |
| `topics` | string[] \| null | no | — | AI assessment — main topics covered by the site. LLM-authored field. Raw topic labels (not FK-normalised). |
| `editorial_description` | text \| null | no | — | AI-authored editorial description of why this site is worth following. LLM-authored field. |
| `is_active` | boolean | no | — | Derived — see Derived Fields. |

## Page Mixin Fields

ATTACHED — WebsiteBlog pages surface at /library/sites/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually matches `code`. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). Sourced from `editorial_description` if set, else `description` excerpt. |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. |
| `is_active` | boolean | Whether the site page is currently live. |
| `phase` | integer | Rollout phase. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `is_active` | RSS feed last-entry date, or ChangeDetection.io last-change date | True if new content has appeared on the site within the last 6 months. |
| `post_frequency` | RSS feed timestamps | Derived from inter-publication intervals. Enum: "daily" \| "weekly" \| "monthly" \| "irregular" \| "inactive". |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Publishes web articles | Resource (web_guide) → WebsiteBlog | WebsiteBlog | `Resource.website_blog_code` | One-directional from Resource. Site carries no reciprocal article list — query via Resource.website_blog_code index. |
| Operated by (person) | WebsiteBlog → Person | Person | `operator_person_code` | Nullable FK. One-directional. |
| Operated by (organisation) | WebsiteBlog → Organisation | Organisation | `publisher_code` | Nullable FK. One-directional. Renames `operator_institution_id`; target is now Organisation (not Institution). |
| Scoped to | WebsiteBlog → ProfessionalDiscipline | ProfessionalDiscipline | `discipline_codes[]` | M:N via FK array. |

## Notes

- **`code` replaces `website_id`:** Source file used a system-generated `website_id`. Canonical replaces with a human-readable slug-based `code`, consistent with all other entities.
- **`publisher_code` rename:** Source uses `operator_institution_id` → Institution. Canonical renames to `publisher_code` → Organisation.code, resolving the Institution-vs-Organisation naming conflict. The field is nullable — not all sites are run by organisations.
- **`operator_person_code` rename:** Source uses `operator_person_id`. Renamed per P4 (code-based FKs).
- **`operator_name_raw` rename:** Source uses `operator_name` (free-text, may resolve to either person or organisation). Canonical renames to `operator_name_raw` and adds `_raw` suffix to signal it is a pre-resolution string, not a display field.
- **Dual entity/resource nature:** The `blog_site` resource subtype and the WebsiteBlog entity are the same real-world object. This dual-nature design is preserved. When a new blog site is catalogued, both a WebsiteBlog entity record and a `blog_site` resource record are created and linked.
- **Operator ambiguity resolved:** Source `operator_name` could resolve to either Person (`operator_person_id`) or Institution (`operator_institution_id`) without a flag indicating which. Canonical separates these into two distinct nullable FKs (`operator_person_code`, `publisher_code`). Only one should be non-null for a given record; both null is valid if the operator is not identified.
- **Monitoring:** RSS feeds (where available) polled weekly; sites without RSS monitored via ChangeDetection.io.
- **Refresh cycle:** Quarterly for active sites; annually for inactive.
- **Estimated records:** Under 100 sites.
- **Data sources:** Website scrape (name, description, operator); RSS feed (post frequency, last published); Wayback Machine API (first_seen); Favicon API (favicon_url); manual curation (site_type, editorial_description).
