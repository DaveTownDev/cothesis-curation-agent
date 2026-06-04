# ConferenceSeries — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Conference.md (cothesis_shared_entity_schema.md §4.9 series-level model + secondary_entity_reference.md Entity 8 series fields)
COMPENDIUM_URL: /library/conferences/{slug}

## Purpose

ConferenceSeries is the recurring meta-entity for an academic conference — the named event that happens repeatedly (annually, biennially, etc.). It holds the stable identity, discipline scope, organiser, and Compendium page. Specific occurrences (a particular year's event, with dates and location) are modelled as ConferenceInstance children.

This split resolves the core conflict identified in `entity_Conference.md`: the secondary reference modelled conference instances while `cothesis_shared_entity_schema.md` §4.9 modelled conference series. Both granularities are needed. The series has a Compendium page; individual instances do not.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. Uppercase preferred for well-known conferences. e.g. "RANZCP_CONGRESS", "COCHRANE_COLLOQUIUM", "APA_ANNUAL". |
| `name` | string | yes | — | Full series name. e.g. "RANZCP Annual Congress", "Cochrane Colloquium". |
| `acronym` | string \| null | no | — | Short abbreviation if commonly used. e.g. "ANZCTR", "ISTH". |
| `description` | text \| null | no | — | 1–3 sentence description of what the conference covers and who attends. |
| `discipline_codes` | string[] | no | ProfessionalDiscipline.code | FK array. Disciplines/specialties this conference primarily serves. |
| `organiser_code` | string \| null | no | Organisation.code | FK to the organising body. Null if not yet resolved. |
| `organiser_name_raw` | string \| null | no | — | Raw organiser name string. Preserved for resolution audit. |
| `website_url` | string \| null | no | — | Series homepage URL (may redirect to the current year's instance). |
| `frequency` | string \| null | no | — | Recurrence pattern. Enum: "annual" \| "biannual" \| "irregular". Source: manual curation. |
| `region` | string \| null | no | — | Geographic scope. Enum: "national" \| "international" \| "regional". |
| `is_active` | boolean | no | — | Whether the conference series is still running. Set false for discontinued series. |

## Page Mixin Fields

ATTACHED — ConferenceSeries pages surface at /library/conferences/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. |
| `is_active` | boolean | Whether the series page is currently live. Separate from the source-of-truth `is_active` above — page mixin `is_active` controls visibility; source-of-truth `is_active` records whether the real-world series is still running. In practice usually equal. |
| `phase` | integer | Rollout phase. |

Note: The Page Mixin `is_active` and the source-of-truth `is_active` are stored as one field. The single `is_active` serves both purposes.

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `instance_count` | ConferenceInstance records | Count of ConferenceInstance rows where `series_code` = this `code`. |
| `latest_instance_year` | ConferenceInstance records | MAX(year) from linked ConferenceInstance rows. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Organised by | ConferenceSeries → Organisation | Organisation | `organiser_code` | Nullable FK. |
| Scoped to | ConferenceSeries → ProfessionalDiscipline | ProfessionalDiscipline | `discipline_codes[]` | M:N via FK array. |
| Has instances | ConferenceSeries → ConferenceInstance | ConferenceInstance | `ConferenceInstance.series_code` | One-directional: instances carry `series_code`. No reciprocal list on Series. |
| Hosted by (reciprocal) | Organisation → ConferenceSeries | ConferenceSeries | `Organisation.hosted_conference_series_codes[]` | Reciprocal stored on Organisation per P5. Useful for organisation pages listing their conferences. |
| Resources presented at | Resource → ConferenceSeries | ConferenceSeries | `Resource.conference_series_code` | For workshop materials, posters, presentations linked to a series rather than a specific instance. |

## Notes

- **Split rationale:** The Conference entity in source files conflated two levels of abstraction. Series is the stable entity with a Compendium page. Instance is the transient, year-specific record with no Compendium page.
- **Supersedes:** The series-level aspects of entity_Conference.md §4.9.
- **Naming:** "ConferenceSeries" not "Conference" — the name makes the granularity explicit in the type system.
- **`is_active` dual use:** A single `is_active` field covers both the page mixin requirement and the operational status of the real-world series. If a series is discontinued, set `is_active: false` and `has_page: false`.
- **Estimated records:** 30–100 series.
- **Data sources:** Manual curation + conference website scrapes. No dedicated API for academic conference metadata.
