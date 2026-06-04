# ConferenceInstance — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Conference.md (secondary_entity_reference.md Entity 8 instance-level fields)
COMPENDIUM_URL: NOT SURFACED — private/internal record; no Compendium page

## Purpose

ConferenceInstance is the year-specific occurrence of a conference series — a particular event with real-world dates, a location, a website, and submission deadlines. It is a child record of ConferenceSeries and carries all the instance-level data that the series record does not.

ConferenceInstances are not surfaced on the Compendium. They exist to support resource linking (a workshop resource was presented at RANZCP Congress 2024), deadline tracking, and proceedings indexing. Compendium users navigate to the ConferenceSeries page; internal users and the pipeline reference ConferenceInstance for specifics.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based key. Convention: `{SERIES_CODE}_{YEAR}`. e.g. "RANZCP_CONGRESS_2025", "COCHRANE_COLLOQUIUM_2024". |
| `series_code` | string | yes | ConferenceSeries.code | FK to the parent ConferenceSeries. Required — every instance belongs to a series. |
| `year` | integer | yes | — | Calendar year of the event. e.g. 2025. |
| `name_full` | string | no | — | Full display name for this instance. e.g. "RANZCP Annual Congress 2025". If null, derived as `{ConferenceSeries.name} {year}`. |
| `start_date` | date \| null | no | — | Opening date. ISO 8601 (YYYY-MM-DD). Null before announced. |
| `end_date` | date \| null | no | — | Closing date. ISO 8601. |
| `location_city` | string \| null | no | — | City where the event is held. e.g. "Melbourne". Null for virtual events. |
| `location_country_code` | string \| null | no | Country.code | ISO 3166-1 alpha-2. Null for virtual events. |
| `format` | string \| null | no | — | Delivery format. Enum: "in_person" \| "hybrid" \| "virtual". |
| `website_url` | string \| null | no | — | URL for this specific year's event (may differ from series URL). |
| `submission_deadline` | date \| null | no | — | Abstract/paper submission deadline. ISO 8601. |
| `abstract_deadline` | date \| null | no | — | Abstract-only submission deadline if separate from full-paper deadline. ISO 8601. |
| `proceedings_url` | string \| null | no | — | Link to published proceedings (Zenodo community, conference site archive, etc.). |
| `is_active` | boolean | no | — | Whether this instance record is current/visible in internal tooling. Set false for very old instances with no linked resources. |

## Page Mixin Fields

NOT ATTACHED — ConferenceInstance records do not generate Compendium pages.

Reason: Individual conference instances are ephemeral, year-specific records. The Compendium page belongs to the ConferenceSeries. Surfacing 20 instance pages for a long-running annual conference would fragment the UX and dilute SEO value.

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `name_full` | `series_code` (→ ConferenceSeries.name) + `year` | If `name_full` is null, derive as `"{ConferenceSeries.name} {year}"`. |
| `duration_days` | `start_date`, `end_date` | `end_date - start_date + 1` (inclusive). Null if either date is null. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Belongs to | ConferenceInstance → ConferenceSeries | ConferenceSeries | `series_code` | Required FK. Many instances to one series. |
| Held in | ConferenceInstance → Country | Country | `location_country_code` | Nullable FK. |
| Resources presented at | Resource → ConferenceInstance | ConferenceInstance | `Resource.conference_instance_code` | Resources (workshop materials, posters, presentations) link to the specific instance. One-directional from Resource. |

## Notes

- **No Page Mixin:** Instance records are internal. Compendium links for a conference go to the ConferenceSeries page, which may list upcoming/recent instances from its derived fields.
- **`code` convention:** Series code + underscore + year. If a series runs two events in one year (rare), append a suffix: "SERIES_CODE_2024_A", "SERIES_CODE_2024_B".
- **Supersedes:** The instance-level aspects of entity_Conference.md (secondary_entity_reference.md Entity 8).
- **Resource FK note:** Resources use `conference_instance_code` to link to a specific occurrence. If only the series is known (not the specific year), resources may instead carry `conference_series_code` on the series entity.
- **Data sources:** Conference website scrape, Zenodo communities API (for proceedings), manual curation.
- **Estimated records:** 100–300 instances (3–5 years of history across 30–100 series).
