# ResourceSubtype.web_guide — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: web_guide
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A web guide is an online article, tutorial, reference page, or blog post that provides guidance on research methodology — covering individual pages and blog/site-level containers.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `site_name` | string | No | Name of the parent website or publication. |
| `parent_site_code` | string | No | FK to Resource.code of the parent blog/site resource (where the site itself is also a Resource). Was: `website_entity_id`. |
| `content_type` | string (enum) | No | `tutorial` \| `reference` \| `blog_post` \| `faq` \| `tool` \| `guide` \| `news` \| `wiki`. |
| `word_count` | integer | No | Article word count. |
| `reading_time_minutes` | integer | No | Estimated reading time in minutes. Derived from word_count (~200 wpm). Cluster E. |
| `post_frequency` | string | No | For blog/site-level resources: posting frequency e.g. `weekly`, `monthly`. |
| `post_count` | integer | No | For blog/site-level resources: total published post count. |
| `outbound_academic_links` | integer | No | Count of outbound links to academic sources. Derived. |
| `references_dois` | string[] | No | DOIs referenced in the article. Derived. |
| `wayback_url` | string (uri) | No | Wayback Machine / Internet Archive URL for archival. |
| `permacc_url` | string (uri) | No | Perma.cc archival URL. |
| `is_archived` | boolean | No | Whether the page is archived (no longer actively maintained). Cluster K. |
| `meta_description` | string | No | Page meta description from HTML (publisher-supplied, distinct from Resource.meta_description which is CoThesis-authored). |
| `og_image` | string (uri) | No | Open Graph image URL. Cluster F. |
| `featured_image_url` | string (uri) | No | Featured/hero image URL. Cluster F; maps to thumbnail_url on Resource base. |
| `favicon_url` | string (uri) | No | Site favicon URL. Cluster F. |
| `site_favicon` | string (uri) | No | Alias for favicon_url. |
| `operator_name` | string | No | Blog/site operator name (for blog_site resources). Cluster C/L. |
| `operator_person_id` | string | No | FK to Person.code of the individual operator. |
| `operator_institution_id` | string | No | FK to Organisation.code of the operating institution. |
| `primary_topics` | string[] | No | AI-assessed primary topics for the site/guide. |
| `credibility_assessment` | string | No | AI-generated credibility assessment of the source. |
| `access_type` | string | No | Web-guide-specific access classification (free/paywalled). Maps to Resource.access_type. |

## Notes

- Web guide covers both individual articles/pages and blog/site-level resources. Site-level fields (`post_frequency`, `post_count`, `operator_name`, `operator_person_id`) are populated for site-type resources.
- `meta_description` here is the publisher-supplied HTML meta tag — distinct from Resource.meta_description (which is CoThesis-authored SEO copy). Both are stored.
- `wayback_url` and `permacc_url` are important for link-rot resilience — web guides are the most likely subtype to go offline.
- `credibility_assessment` is AI-generated (tagged L in matrix) — stored on AIAssessment in principle, mirrored here as a web-guide-specific signal.
- Notable gap (matrix §6.5): no first-class `tags`/`keywords` at top level (topic_tags on Resource base covers this).
