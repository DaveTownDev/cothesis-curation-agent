# Journal — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Journal.md (merge of secondary_entity_reference.md Entity 5 + cothesis_shared_entity_schema.md §4.6)
COMPENDIUM_URL: /library/journals/{slug}

## Purpose

Journal is the container entity for academic periodicals. It enables CoThesis resources (articles, preprints, reporting guidelines) to link to a normalised journal record rather than embedding publisher and open-access metadata in every resource row. One journal record serves all resources published in that journal.

The canonical definition merges the import-pipeline-oriented golden record from `secondary_entity_reference.md` (rich API source fields) with the Compendium-page-oriented schema from `cothesis_shared_entity_schema.md` §4.6 (code-based identity, discipline FKs, page mixin). The merge resolves all documented conflicts in favour of the Task E decisions: slug-based `code` as identity key; `issn` + `eissn` + `issn_l` retained for full ISSN coverage; both OA booleans and a derived `oa_status` enum; rich Sherpa object plus a derived colour; `impact_proxy` not `impact_factor`; both `discipline_codes[]` FK and `raw_subjects[]` for pipeline data preservation; `publisher_code` → Organisation (Publisher entity retired).

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. Lowercase, hyphenated. e.g. "lancet", "nejm", "jama", "bmj". Generated from ISSN-L slug on first import; never changes. |
| `title` | string | yes | — | Journal display name. Source priority: OpenAlex → CrossRef → DOAJ. Canonical name for Compendium display. |
| `issn` | string \| null | no | — | Print ISSN (e.g. "0140-6736"). Format: XXXX-XXXX. Null if print edition does not exist. |
| `eissn` | string \| null | no | — | Electronic ISSN. Null if not assigned. |
| `issn_l` | string \| null | no | — | Linking ISSN — the single ISSN designated as the cross-format link point (OpenAlex sole source). Used as the slug seed for `code`. |
| `publisher_code` | string \| null | no | Organisation.code | FK to the publishing Organisation (where `types` includes "publisher"). Null if publisher not yet resolved. Replaces `publisher_entity_id` in legacy model. Publisher entity RETIRED — absorbed into Organisation. |
| `publisher_name_raw` | string \| null | no | — | Raw publisher name string from API (OpenAlex → CrossRef → DOAJ). Preserved for audit and resolution. Not the FK. |
| `website_url` | string \| null | no | — | Journal homepage. Renamed from `homepage_url` (secondary ref). |
| `is_open_access` | boolean | no | — | True if journal is fully open access (DOAJ presence = gold OA, else OpenAlex `is_oa` flag). Source: DOAJ → OpenAlex. |
| `is_hybrid_oa` | boolean | no | — | True if journal offers OA publishing option alongside subscription content. Source: OpenAlex. |
| `is_diamond_oa` | boolean | no | — | True if OA with no APC (author pays nothing). Source: DOAJ. |
| `apc_usd` | number \| null | no | — | Article Processing Charge in USD. Source: DOAJ → OpenAlex. Null if not applicable or unknown. |
| `sherpa_romeo` | object \| null | no | — | Full Sherpa Romeo self-archiving policy object. Sole source: Sherpa Romeo API. Shape: `{ pre_print_archiving: string\|null, post_print_archiving: string\|null, publisher_pdf_archiving: string\|null, conditions: string[] }`. Null if not yet retrieved. |
| `impact_proxy` | number \| null | no | — | Best available impact metric proxy. NOT the trademarked Journal Impact Factor. Source priority: Scopus CiteScore → OpenAlex 2yr_mean_citedness. Null if neither available. |
| `impact_proxy_source` | string \| null | no | — | Which source provided `impact_proxy`. Values: "scopus_citescore" \| "openalex_2yr" \| null. |
| `sjr` | number \| null | no | — | SCImago Journal Rank. Scopus sole source. (Source file uses `sjr`; §4.6 has `sjr_score` — canonical uses `sjr` for pipeline consistency.) |
| `h_index` | integer \| null | no | — | Journal h-index. Source: OpenAlex. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK array to professional disciplines. Curated from OpenAlex topics → Scopus subject areas → DOAJ LCC. The structured discipline link used for Compendium filtering. |
| `raw_subjects` | string[] | no | — | Raw subject strings from source APIs (OpenAlex topics, Scopus classifications, DOAJ LCC). Preserved for pipeline audit and future re-mapping. NOT used for Compendium filtering. |
| `index_codes` | string[] | no | — | Indexing databases. Free-text array. Common values: "MEDLINE", "EMBASE", "SCOPUS", "DOAJ", "PUBMED_CENTRAL", "CINAHL". |
| `language_code` | string \| null | no | — | Primary publication language. ISO 639-1 (e.g. "en", "fr"). Source: DOAJ → CrossRef. |
| `country_code` | string \| null | no | Country.code | Country of publication. ISO 3166-1 alpha-2. Source: DOAJ → CrossRef. |
| `scope_summary` | string \| null | no | — | Short editorially written scope summary (1–2 sentences). Distinct from `aims_and_scope` (full text). |
| `aims_and_scope` | text \| null | no | — | Full aims-and-scope text from journal website or DOAJ. |
| `acceptance_rate` | number \| null | no | — | Published acceptance rate as a decimal (e.g. 0.12 for 12%). Source: journal website scrape / manual. |
| `peer_review_type` | string \| null | no | — | Peer review model. Source: DOAJ. Examples: "double_blind", "single_blind", "open", "editorial". |
| `is_predatory_flagged` | boolean | no | — | True if flagged by Beall's List or equivalent predatory-journal watchlist. Default false. |
| `is_retraction_watch_flagged` | boolean | no | — | True if journal appears in Retraction Watch database with notable retraction history. Default false. |
| `is_in_doaj` | boolean | no | — | True if journal is listed in DOAJ. Useful for OA verification independent of OpenAlex. |
| `metadata_quality` | object \| null | no | — | CrossRef metadata coverage scores object. Sole source: CrossRef. Shape: `{ has_abstract: number, has_references: number, has_orcid: number }` (coverage ratios 0–1). Null if not retrieved. |

## Page Mixin Fields

ATTACHED — Journal pages surface at /library/journals/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Matches `code` in most cases (e.g. "lancet"). |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). Sourced from `scope_summary` if not separately authored. |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name for tiles/nav. |
| `has_page` | boolean | Whether a Compendium page is generated for this journal. |
| `is_active` | boolean | Whether the journal page is currently live. |
| `phase` | integer | Rollout phase (1 = launch, 2 = post-launch, 3 = later). |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `oa_status` | `is_open_access`, `is_hybrid_oa`, `is_diamond_oa` | Enum: "open" (is_open_access = true, is_hybrid_oa = false) \| "diamond" (is_diamond_oa = true) \| "hybrid" (is_hybrid_oa = true) \| "subscription" (all false) \| "unknown" (no OA data). Diamond is a subtype of open; check is_diamond_oa first. |
| `sherpa_romeo_colour` | `sherpa_romeo` | Derived from Sherpa Romeo archiving policy. Enum: "green" (pre- or post-print allowed without embargo) \| "yellow" (post-print only, may have embargo) \| "blue" (publisher PDF allowed) \| "white" (no archiving permitted) \| "unknown" (sherpa_romeo is null). |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Published by | Journal → Organisation | Organisation | `publisher_code` | Organisation.types includes "publisher". One publisher per journal record. |
| Scoped to | Journal → ProfessionalDiscipline | ProfessionalDiscipline | `discipline_codes[]` | M:N via FK array. |
| Published in (resources) | Resource → Journal | Journal | `Resource.journal_code` | One-directional from Resource. Journal carries no reciprocal resource list — query via Resource.journal_code index. |
| Country | Journal → Country | Country | `country_code` | Nullable FK. |
| Organised in | Organisation → Journal | Journal | `Organisation.published_journal_codes[]` | Reciprocal stored on Organisation per P5 decision. Useful for publisher pages listing their journals. |

## Notes

- **Merge decision — identity key:** Secondary reference used no `code` field and resolved journals by ISSN. Canonical uses slug-based `code` (§4.6 convention) seeded from `issn_l` slug. Example codes: "lancet", "nejm", "jama", "bmj", "cochrane-db-syst-rev".
- **Merge decision — ISSN modelling:** Both `issn` (print) and `eissn` (electronic) from §4.6 are retained, plus `issn_l` (linking ISSN) from the secondary reference. All three fields coexist.
- **Merge decision — OA fields:** Secondary reference `is_oa` renamed `is_open_access` for clarity. `is_hybrid_oa` and `is_diamond_oa` added as additional boolean flags. `oa_status` enum is derived. `is_in_doaj` retained from secondary reference.
- **Merge decision — impact:** `impact_proxy` + `impact_proxy_source` from secondary reference retained (not `impact_factor` from §4.6, which used the trademarked term). `sjr` retained alongside `impact_proxy`.
- **Merge decision — self-archiving:** Full `sherpa_romeo` object retained (secondary reference form). `sherpa_romeo_colour` is a derived field, not a source-of-truth field.
- **Merge decision — subjects:** Both `discipline_codes[]` (FK, §4.6 form) and `raw_subjects[]` (pipeline preservation, secondary reference form) coexist.
- **Merge decision — publisher:** `publisher_code` → Organisation.code. Publisher entity RETIRED. `publisher_name_raw` preserved for resolution audit.
- **Fields dropped:** `metadata_quality` is retained as a nullable object (pipeline value), not promoted to a primary display field. `works_count` (OpenAlex) not promoted — query Resource table instead.
- **Refresh cycle:** Annually. Journal metrics and policies change infrequently.
- **Estimated records:** 200–500.
