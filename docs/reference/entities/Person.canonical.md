# Person — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: entity_Person.md (secondary_entity_reference.md Entity 1)
COMPENDIUM_URL: /library/people/{slug}

## Purpose

Person is the shared entity for individual humans who are linked to CoThesis resources — as authors, editors, instructors, hosts, creators, or other roles. A single Person record is created when first encountered during resource enrichment and linked to all subsequent resources from that individual, enabling cross-resource author pages and citation network queries.

Person is distinct from three other person-related concepts in the system: User (the authentication/account entity), UserProfile (the trainee-preference and career-stage entity), and Supervisor (a clinical supervision relationship entity). Person represents a real-world individual in the research literature and content ecosystem, not a platform account holder.

Person was not modelled in `cothesis_shared_entity_schema.md` (which handled authorship via institution-level junctions only). This canonical definition promotes Person to a first-class shared entity with a Compendium page.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. Convention: `{family_name}-{given_initial}` lowercased and hyphenated, with collision suffix. e.g. "smith-j", "jones-r-2". Generated at first entity resolution; never changes. |
| `name_full` | string | yes | — | Canonical display name. Source priority: ORCID (self-declared) → OpenAlex → Semantic Scholar. Renamed from `canonical_name` in source for clarity. |
| `name_given` | string \| null | no | — | Given name(s). Source priority: ORCID → OpenAlex → S2. Renamed from `given_name`. |
| `name_family` | string \| null | no | — | Surname. Source priority: ORCID → OpenAlex → S2. Renamed from `family_name`. |
| `orcid` | string \| null | no | — | ORCID iD (e.g. "0000-0002-1825-0097"). ORCID API is authoritative. The primary deduplication key. |
| `email` | string \| null | no | — | Public contact email only. Sourced from institutional page scrape if publicly listed. NEVER sourced from private communications or inferred. |
| `affiliation_codes` | string[] | no | Organisation.code | FK array to current and known affiliations. Resolved from ORCID employments + OpenAlex last_known_institutions via ROR match. Replaces `institution_entity_id` + `all_affiliations` in source. |
| `affiliation_history` | — | — | — | **OQ-008 PROMOTED** — this embedded array has been promoted to the `PersonAffiliation` canonical entity. Not stored on Person. Query PersonAffiliation.person_code for full affiliation history. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK array. Research disciplines/specialties this person works in. Source: OpenAlex topics → ORCID keywords. |
| `website_url` | string \| null | no | — | Primary personal or institutional profile URL. |
| `bio` | text \| null | no | — | Free-text biographical summary. Source priority: ORCID biography → institutional page scrape. Renamed from `biography`. |
| `credentials` | string \| null | no | — | Qualifications string (e.g. "MBBS PhD FRANZCP"). Source: institutional page scrape only — no API provides this. |
| `profile_image_url` | string \| null | no | — | Headshot image URL. Source: institutional page → ORCID researcher_urls. |
| `h_index` | integer \| null | no | — | Best available h-index. Source priority: OpenAlex (primary), max across OpenAlex / Semantic Scholar / Google Scholar. |
| `citation_count` | integer \| null | no | — | Total citation count. Source priority: OpenAlex (primary), max across sources. |
| `works_count` | integer \| null | no | — | Total published works count. Source priority: OpenAlex → S2 → ORCID. |
| `research_topics` | string[] \| null | no | — | Raw research topic labels from APIs. Source priority: OpenAlex topics → ORCID keywords. Preserved for display; not FK-normalised. |
| `is_active` | boolean | no | — | Derived — see Derived Fields. |

## Page Mixin Fields

ATTACHED — Person pages surface at /library/people/{slug}

Note: Not every Person record generates a Compendium page. `has_page` is set true only for key figures with sufficient content value (multiple resources, substantial bio). Most authors will have `has_page: false`.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually matches `code`. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). Sourced from `bio` excerpt if not separately authored. |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. False for most authors. |
| `is_active` | boolean | Whether the person page is currently live. |
| `phase` | integer | Rollout phase. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `is_active` | ORCID `updated-date`, OpenAlex `counts_by_year` | True if ORCID record updated within last 2 years OR OpenAlex shows works in last 2 years. |
| `primary_affiliation_code` | PersonAffiliation records | Most recent PersonAffiliation where `is_current = true`, ordered by start_year desc. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Affiliated with (current) | Person → Organisation | Organisation | `affiliation_codes[]` | M:N via FK array. Current/recent affiliations. |
| Affiliation history | Person → PersonAffiliation | PersonAffiliation | PersonAffiliation.person_code | one→many. Full historical record promoted from embedded array (OQ-008). |
| Scoped to | Person → ProfessionalDiscipline | ProfessionalDiscipline | `discipline_codes[]` | M:N via FK array. |
| Authors/creates resources | Resource → Person | Person | `Resource.person_codes[]` (role-typed) | One-directional from Resource. Person carries no reciprocal resource list — query via Resource.person_codes[]. `works_count` is the count proxy. |
| Creates channel | YouTubeChannel → Person | Person | `YouTubeChannel.creator_person_code` | One-directional from YouTubeChannel. |
| Hosts podcast | PodcastShow → Person | Person | `PodcastShow.host_person_codes[]` | One-directional from PodcastShow. |
| Operates website | WebsiteBlog → Person | Person | `WebsiteBlog.operator_person_code` | One-directional from WebsiteBlog. |
| Employed by | Organisation → Person | Person | *(OQ-011 resolved: Organisation.employed_person_codes[] DROPPED)* | No reciprocal FK array stored on Organisation. Employment is tracked via PersonAffiliation (pipeline) or SupervisionRelationship (platform). |

## Notes

- **Distinct from User:** Person is a real-world research-community individual. User is a CoThesis platform account. A platform user who is also a researcher may have both a User record and a Person record, but they are not the same entity and are not automatically linked.
- **Distinct from Supervisor:** Supervisor (clinical) is a separate entity in the CoThesis platform layer, representing a training supervision relationship. A clinician may be both a Person (in the Compendium) and a Supervisor (in the platform), but these are separate records.
- **`affiliation_codes[]` replaces `institution_entity_id`:** The source file used a single `institution_entity_id` (current institution only) plus a separate `all_affiliations` array. The canonical merges these: `affiliation_codes[]` is the normalised FK array for current and recent affiliations; `affiliation_history` preserves the full pipeline data.
- **No reciprocal resource list on Person:** The `works_count` field provides a count. Resource-level queries use `Resource.person_codes[]` with an index. This is intentional — storing a `resource_ids[]` array on Person would be unbounded for prolific authors.
- **Entity resolution:** (1) ORCID exact match, (2) OpenAlex ID exact match, (3) family name + first initial + institution fuzzy match, (4) family name + co-author network overlap. Match confidence is logged.
- **Refresh cycle:** Quarterly for active researchers; annually for others.
- **Estimated records:** Hundreds to thousands, growing with resource imports.
- **Data sources:** ORCID (self-declared identity), OpenAlex Authors (bibliometrics), Semantic Scholar, Google Scholar via SerpAPI, institutional page scrapes.
