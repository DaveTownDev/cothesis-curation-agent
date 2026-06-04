# ResourceSubtype.funding — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: funding
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A funding resource is a grant, fellowship, scholarship, or award opportunity relevant to research trainees — with funder, eligibility, amount, and application deadline metadata.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `funding_type` | string (enum) | No | `grant` \| `fellowship` \| `scholarship` \| `award` \| `bursary` \| `prize`. |
| `funder_code` | string | No | FK to Funder.code (or Organisation.code where types[] includes `funder`). Was: `funder_entity_id`, `funder_name` (Cluster L). Primary relationship on funding resources. |
| `amount_aud_min` | number | No | Minimum award amount in AUD. Was: `amount_min`. Cluster M. |
| `amount_aud_max` | number | No | Maximum award amount in AUD. Was: `amount_max`. |
| `stipend_amount` | number | No | Stipend amount (for fellowships). |
| `award_amount` | string | No | Textual award description when amount is not a simple range. |
| `currency` | string | No | ISO 4217 currency code for amount fields. Default `AUD`. |
| `eligibility_stage` | string[] | No | FK to ProfessionalStage.code[]. Who is eligible by career/training stage. Was: `career_stage`, `eligibility`. |
| `eligibility` | string | No | Full-text eligibility description. |
| `application_deadline` | string (date) | No | Application closing date. |
| `application_url` | string (uri) | No | Application portal URL. |
| `application_frequency` | string | No | How often applications are accepted e.g. `annual`, `rolling`, `biannual`. |
| `recurrence` | string (enum) | No | `annual` \| `biannual` \| `rolling` \| `one_off`. |
| `success_rate` | number | No | Historical success rate as a percentage (where published). |
| `typical_duration` | string | No | Typical grant/fellowship duration e.g. `12 months`, `3 years`. |
| `duration_years` | number | No | Duration in years (for multi-year fellowships). |
| `start_date` | string (date) | No | Grant/programme start date. Maps to Resource.publication_date for funding. |
| `end_date` | string (date) | No | Grant/programme end date. |
| `who_should_apply` | string | No | AI-authored guidance on who this funding suits. |
| `resulting_publication_count` | integer | No | Count of resulting publications (where tracked). |
| `resulting_publications` | string[] | No | DOIs or titles of publications resulting from this funding. |
| `research_categories` | string[] | No | Funder-defined research categories (distinct vocabulary from topic_tags). |
| `gtr_id` | string | No | Gateway to Research (UKRI) ID. Cluster G. |
| `nih_project_number` | string | No | NIH Reporter project number. Cluster G. |
| `dimensions_grant_id` | string | No | Dimensions.ai grant ID. Cluster G. |
| `cordis_id` | string | No | EU CORDIS project ID. Cluster G. |
| `agency_name` | string | No | Funding agency name (free-text, for agencies without a Funder entity yet). |
| `contact_email` | string (email) | No | Funding body contact email. |

## Notes

- Funding is one of the three subtypes with the most gaps (matrix §6.5): `language_code` is absent from funding schema (N/A), no `topic_tags`/`keywords` (gap — `research_categories` is a weaker substitute), no `thumbnail_url` (gap), no normalised `publication_year` (`start_date` is used instead).
- `funder_code` uses P4 code-based FK pattern. The Funder entity is the primary relationship on funding resources (unlike other subtypes where the institution is secondary).
- `eligibility_stage` links to ProfessionalStage.code[] — important for CoThesis trainee-stage filtering.
- `recurrence` is the structured enum; `application_frequency` is the free-text description.
