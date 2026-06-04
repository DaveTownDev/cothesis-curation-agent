# Organisation — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Organisation.md (cothesis_shared_entity_schema.md §2.2, unified Organisation); Publisher entity RETIRED — absorbed here
COMPENDIUM_URL: /library/organisations/{slug}

## Purpose

Organisation is the single unified entity for all organisations that interact with the CoThesis professional training system. Rather than maintaining separate tables for specialty colleges, training organisations, regulatory bodies, publishers, funders, and research institutes, a single Organisation record carries a `types[]` array describing the roles that organisation plays. One row for NHMRC (types: ["funding_body", "research_institute"]); one row for Elsevier (types: ["publisher"]); one row for RANZCP (types: ["professional_body"]).

This design directly implements Design Principle 2 (type fields over separate tables) and replaces the following previously separate or proposed entities: Specialty College, Training Organisation, Domain Organisation, Publisher, Funding Organisation, Research Institute, Reporting Standard Body. The Publisher entity is explicitly RETIRED as of Task E.

Two reciprocal arrays are stored on Organisation per P5: `published_journal_codes[]` (for publisher-type pages listing their journals) and `hosted_conference_series_codes[]` (for organisation pages listing their conferences). `employed_person_codes[]` was dropped (OQ-011 resolved — use Person.current_employer_code index). Training-provider-specific fields are added as a role-conditional cluster (OQ-004 resolved).

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable identity key. UPPERCASE_ABBREV convention. e.g. "RANZCP", "AHPRA", "NHMRC", "ELSEVIER", "WILEY". Never changes once in production. Used as FK across Division, Discipline, Program, Requirement, Journal, Resource, PracticeSite, DataSource, ConferenceSeries. |
| `name` | string | yes | — | Full official name. e.g. "Royal Australian and New Zealand College of Psychiatrists". |
| `name_short` | string \| null | no | — | Abbreviated display name. e.g. "RANZCP". Renamed from `abbreviation` in shared schema for clarity. |
| `types` | string[] | yes | — | What roles this organisation plays. At least one value required. Enum: "professional_body" \| "regulatory_authority" \| "accreditation_body" \| "union" \| "peak_body" \| "funding_body" \| "research_institute" \| "publisher" \| "standards_body" \| "registry_operator" \| "university" \| "hospital" \| "college" \| "government" \| "ngo" \| "training_provider" \| "other". Note: "university" and "hospital" added to cover PracticeSite.university_codes[] and similar gaps identified in entity_Organisation.md §5. |
| `country_code` | string \| null | no | Country.code | Primary country of registration. ISO 3166-1 alpha-2. Null for truly international bodies. For multi-country orgs use the OrganisationCountry junction. |
| `website_url` | string \| null | no | — | Canonical website URL. Renamed from `website` in shared schema for field-naming consistency with other entities. |
| `description` | text \| null | no | — | 1–3 sentence description of the organisation's role and scope. |
| `ror_id` | string \| null | no | — | Research Organisation Registry ID. For institutions and research orgs. Source: ROR API. |
| `crossref_funder_id` | string \| null | no | — | CrossRef Funder Registry ID (10.13039/... DOI format). For funding_body-type orgs. Sole source: CrossRef. |
| `crossref_member_id` | string \| null | no | — | CrossRef Member ID. For publisher-type orgs. |
| `logo_url` | string \| null | no | — | Logo image URL for Compendium display. Source: OpenAlex Institutions → manual. |
| `regional_names` | object \| null | no | — | Open map `{ [country_code: string]: string \| null }`. Jurisdiction-variant display names. Null if not applicable. |
| `domain_code` | string \| null | no | Domain.code | FK to the professional domain this org primarily serves. Null for cross-domain orgs (e.g. NHMRC spans all health domains). |
| `published_journal_codes` | string[] | no | Journal.code | Reciprocal stored per P5. Journals where this organisation is the publisher (types includes "publisher"). Useful for publisher profile pages. Updated when Journal.publisher_code is set to this org's code. |
| `hosted_conference_series_codes` | string[] | no | ConferenceSeries.code | Reciprocal stored per P5. Conference series where this organisation is the organiser. Useful for organisation pages listing their events. Updated when ConferenceSeries.organiser_code is set to this org's code. |
| `employed_person_codes` | string[] \| null | no | Person.code | OQ-011 RESOLVED — DROPPED. See Notes. |

### Training-Provider Fields (role-conditional — populate only when `types[]` includes `training_provider`)

These fields are null for all Organisation records except those with `training_provider` in `types[]`. Other roles (publisher, hospital, employer) leave them null. Future role-specific field clusters follow the same pattern.

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `accreditation_body_code` | string \| null | no | Organisation.code (self-ref) | Who accredits this organisation (e.g. AMC for Australian medical colleges). Null when not accredited or not applicable. |
| `accreditation_status` | enum \| null | no | — | `accredited \| provisional \| under_review \| suspended \| not_accredited`. Null when Organisation is not a training_provider. |
| `accreditation_expiry_date` | date \| null | no | — | When accreditation lapses. Null for indefinite accreditation or N/A. |
| `curriculum_version` | string \| null | no | — | Free-text version label for the training body's current curriculum (e.g. "2024 Curriculum v3.1"). |
| `trainee_count_current` | integer \| null | no | — | Current enrolled trainee count if known. Used for capacity context. Not surfaced publicly. |
| `examination_schedule_url` | string \| null | no | — | URL to the public examination schedule if applicable. |
| `programs_offered_codes` | string[] \| null | no | Program.code | Programs this Organisation offers. Reciprocal of Program.training_organisation_code. |

## Page Mixin Fields

ATTACHED — Organisation pages surface at /library/organisations/{slug}

Note: Not all Organisation records generate Compendium pages. `has_page` controls which organisations are publicly visible. Typically `professional_body` and `publisher` types generate pages; `regulatory_authority`, `funding_body`, etc. may or may not based on content value.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually matches lowercase `name_short` or `code`. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. False for most operational-only orgs. |
| `is_active` | boolean | Whether the organisation page is currently live. |
| `phase` | integer | Rollout phase. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `primary_type` | `types[]` | First value in types array, or the most significant type for display. Used where a single label is needed in UI. |
| `is_publisher` | `types[]` | `types.includes("publisher")`. Convenience boolean for join filtering. |
| `is_funder` | `types[]` | `types.includes("funding_body")`. Convenience boolean. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Primary country | Organisation → Country | Country | `country_code` | Nullable single FK. |
| All countries | Organisation ↔ Country | Country | OrganisationCountry junction | Junction: `{ organisation_code, country_code, is_primary }`. M:N. |
| Domain | Organisation → Domain | Domain | `domain_code` | Nullable FK. |
| Governs discipline | Organisation ↔ Discipline | Discipline | DisciplineOrganisation junction | Junction: `{ discipline_code, organisation_code, country_code, is_primary }`. |
| Parent body of division | Organisation ↔ Division | Division | DivisionOrganisation junction | Junction: `{ division_code, organisation_code, is_primary }`. |
| Publishes journal | Organisation → Journal | Journal | `published_journal_codes[]` (reciprocal) / `Journal.publisher_code` (FK owner) | Reciprocal array stored on Organisation. FK owner is Journal. |
| Hosts conference series | Organisation → ConferenceSeries | ConferenceSeries | `hosted_conference_series_codes[]` (reciprocal) / `ConferenceSeries.organiser_code` (FK owner) | Reciprocal array stored on Organisation. |
| Funds resource | Organisation ↔ Resource | Resource | resource_organisation junction (role="funder") | Junction with role field. Replaces Funder entity's resource links. |
| Employs person | Organisation → Person | Person | DROPPED — use Person.current_employer_code index (OQ-011 resolved) | |
| Accredits (self-ref) | Organisation → Organisation | Organisation | `accreditation_body_code` | training_provider role only |
| Offers programs | Organisation → Program | Program | `programs_offered_codes[]` | training_provider role only; reciprocal of Program.training_organisation_code |
| Accredits program | Organisation → Program | Program | `Program.accreditation_body_code` | FK from Program back to Organisation. |
| Operates data source | Organisation → DataSource | DataSource | `DataSource.operator_code` | FK from DataSource back to Organisation. |
| Owns requirement | Organisation → Requirement | Requirement | `Requirement.owner_org_code` | FK from Requirement back to Organisation. |
| Affiliated with practice site | Organisation ↔ PracticeSite | PracticeSite | `PracticeSite.university_codes[]` | FK array on PracticeSite pointing to Organisation where types includes "university". |

## Notes

- **Publisher entity RETIRED:** The Publisher entity previously referenced in source files is fully absorbed into Organisation. Any organisation that publishes journals or resources carries `types: ["publisher"]`. The `crossref_member_id` field supports publisher-specific API lookups.
- **Funder entity status:** The Funder entity from `secondary_entity_reference.md` is separately maintained as a standalone entity (see Funder.canonical.md) because it surfaces on the Compendium with its own page and carries fields (e.g. `grants_database_url`, `funder_type`) that are distinct from the Organisation structure. The `funding_body` OrgType in Organisation handles internal cross-links; the Funder entity serves the Compendium page.
- **OQ-011 RESOLVED — `employed_person_codes[]` DROPPED:** Employment is one-directional — stored on `Person.current_employer_code`. Query "staff at this organisation" via Person table index. Per OQ-011 resolution.
- **OQ-004 RESOLVED — Training-provider fields:** 7 nullable fields added in the Training-Provider Fields cluster. Populated only when `types[]` includes `training_provider`. Validated by `_merge/validation/training_organisation_consistency.py`.
- **`types[]` enum additions:** "university", "hospital", "college", "government", "ngo", "training_provider" added to the shared-schema OrgType enum to close gaps identified in entity_Organisation.md §5 (PracticeSite.university_codes[] required a university type; government and NGO orgs appeared in source data without a type value).
- **`website_url` rename:** Shared schema uses `website`. Canonical renames to `website_url` for consistency with Journal, ConferenceSeries, Person, Funder, YouTubeChannel, PodcastShow, WebsiteBlog.
- **`name_short` rename:** Shared schema uses `abbreviation`. Canonical renames to `name_short` for clarity and consistency.
- **Seed data:** ~80–100 organisations across all types.
- **Refresh cycle:** Annually for most; quarterly for publishers (new journal acquisitions).
