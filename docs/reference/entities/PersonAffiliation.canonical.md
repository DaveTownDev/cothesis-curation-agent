# PersonAffiliation — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
VERSION: unified-schema v1.0 (OQ-008 nested shape promotion)
SOURCE: Promoted from Person.affiliation_history[] embedded array
NOTE: No Compendium page — affiliation history is pipeline-managed data, not editorial content.

---

## Purpose

PersonAffiliation records a single historical or current institutional affiliation for a Person — one row per (person, organisation, tenure period). It allows independent querying of affiliation history across the system ("who has worked at Organisation X?", "what institutions have produced authors on this topic?").

Previously embedded as `Person.affiliation_history[]`. Promoted to a standalone entity (OQ-008) because:
- Contains a FK to Organisation.code (nullable for unresolved affiliations)
- Lifecycle-managed: individual records have start/end years and are updated independently by the enrichment pipeline
- Cross-entity queryable: valuable for institution-level analytics

**Data source:** Merged from ORCID employments + OpenAlex institution affiliations. Some records have unresolved organisations (`organisation_code = null`) where the raw name could not be matched to an Organisation record.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `id` | uuid | yes | — | Surrogate PK |
| `person_code` | string | yes | Person.code | The person whose affiliation this is |
| `organisation_code` | string | null | Organisation.code | FK to resolved Organisation. Null when the institution name could not be matched to a known Organisation (see `organisation_name_raw`). |
| `organisation_name_raw` | string | yes | — | Raw institution name as returned by ORCID/OpenAlex. Always populated, even when `organisation_code` is resolved. Used for pipeline audit and deduplication. |
| `start_year` | integer | null | — | Year the affiliation began. Null when not recorded in source API. |
| `end_year` | integer | null | — | Year the affiliation ended. Null when ongoing or unknown. |
| `is_current` | boolean | yes | — | True when this is an active (ongoing) affiliation. Derived at pipeline time from end_year being null + recency signal. |
| `affiliation_source` | enum | null | — | `orcid \| openalex \| semantic_scholar \| manual` — which API/source provided this record |
| `confidence_score` | number | null | — | 0.0–1.0 pipeline confidence that the ROR/organisation match is correct. Null for manually entered records. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — pipeline-managed data, never surfaced on Compendium.

---

## Derived Fields

None. `Person.primary_affiliation_code` is derived from the most recent PersonAffiliation where `is_current = true`.

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| person_code | many→one | Person | person_code | Required |
| organisation_code | many→one | Organisation | organisation_code | Nullable |

---

## Integrity Notes

- `organisation_name_raw` is always required — even when `organisation_code` is resolved — for pipeline audit.
- Multiple current affiliations per person are valid (a person may hold concurrent appointments).
- The enrichment pipeline refreshes records quarterly for active researchers; annually otherwise.

---

## Migration Note

`Person.canonical.md` should be updated: `affiliation_history[]` removed from SoT fields; `affiliation_codes[]` (current FK array) retained; Relationships table gains `one→many` to PersonAffiliation. `Person.primary_affiliation_code` derived field notes updated to reference PersonAffiliation.

---

## Open Questions

None.
