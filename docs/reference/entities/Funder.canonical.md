# Funder — Canonical Entity

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Funder.md (secondary_entity_reference.md Entity 6); Organisation.canonical.md (for relationship to funding_body OrgType)
COMPENDIUM_URL: /library/funders/{slug}

## Purpose

Funder is the Compendium-facing entity for research funding bodies — government agencies, charitable foundations, industry funders, and international bodies that provide grants and fellowships relevant to CoThesis trainees. It exists alongside (not instead of) the Organisation entity.

The structural relationship between Funder and Organisation requires explicit statement: Funder is a separate canonical entity because it surfaces on the Compendium with its own page and carries fields that are distinct from the general Organisation schema (e.g. `grants_database_url`, `funder_type` enum, `crossref_funder_doi`). Organisation rows with `types: ["funding_body"]` are the *operational* representation used for resource-level linking (the `resource_organisation` junction). A Funder entity row represents the *Compendium-page* representation — richer, curated, and publicly surfaced. For major funders (NHMRC, NIH, Wellcome), both an Organisation row and a Funder row may coexist, linked by `organisation_code`.

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | Immutable slug-based identity key. UPPERCASE_ABBREV convention. e.g. "NHMRC", "ARC", "NIH", "WELLCOME", "MRC". |
| `name` | string | yes | — | Full official name. e.g. "National Health and Medical Research Council". Source priority: CrossRef → OpenAlex. |
| `name_short` | string \| null | no | — | Abbreviation for display. e.g. "NHMRC". |
| `funder_type` | string | yes | — | Category of funder. Enum: "government" \| "charity" \| "industry" \| "international" \| "institutional". |
| `country_code` | string \| null | no | Country.code | Country of registration. ISO 3166-1 alpha-2. Null for international bodies (e.g. WHO, EU Horizon). |
| `website_url` | string \| null | no | — | Funder's homepage. Source: OpenAlex → CrossRef → funder website. |
| `description` | text \| null | no | — | 1–3 sentence description of the funder's mission and what they fund. Source: OpenAlex → funder website scrape. |
| `grants_database_url` | string \| null | no | — | URL to the funder's public grants search / funding opportunities portal. e.g. NHMRC Grants Portal. Manually curated. |
| `ror_id` | string \| null | no | — | Research Organisation Registry ID. Source: ROR. Nullable — not all funders have ROR records. Used for cross-linking to Institution/Organisation records. |
| `crossref_funder_doi` | string \| null | no | — | CrossRef Funder Registry DOI (10.13039/... format). Sole source: CrossRef. This is the primary deduplication key for funder matching in resource metadata. Renamed from `funder_doi` in source for clarity. |
| `organisation_code` | string \| null | no | Organisation.code | FK to the corresponding Organisation row if one exists (for major funders that also appear in Organisation as funding_body). Nullable — not all Funder records will have a matching Organisation row. |

## Page Mixin Fields

ATTACHED — Funder pages surface at /library/funders/{slug}

| Field | Type | Notes |
|---|---|---|
| `slug` | string | Immutable once published. Usually matches lowercase `code`. |
| `page_title` | string | SEO `<title>` tag. |
| `meta_description` | string | ≤160 chars. |
| `short_description` | string | Card/listing text (1–2 sentences). |
| `seo_keywords` | string[] | Additional search terms. |
| `icon` | string \| null | Lucide icon name. |
| `has_page` | boolean | Whether a Compendium page is generated. |
| `is_active` | boolean | Whether the funder page is currently live. |
| `phase` | integer | Rollout phase. |

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `funded_resource_count` | Resource records | Count of Resource rows linked to this funder via the resource_funder junction or `Resource.funder_codes[]`. Approximation — full count requires Resource table query. |

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| Located in | Funder → Country | Country | `country_code` | Nullable FK. |
| Corresponds to organisation | Funder → Organisation | Organisation | `organisation_code` | Nullable FK. For major funders that also appear as Organisation rows. |
| Funds resources | Resource → Funder | Funder | `Resource.funder_codes[]` | One-directional from Resource. Funder carries no reciprocal resource list. Query via Resource.funder_codes[] index. |

## Notes

- **Funder vs Organisation `funding_body` type:** These two representations serve different purposes. `Organisation.types: ["funding_body"]` is the operational FK target for resource-level funding attribution (the `resource_organisation` junction). The Funder entity is the Compendium-page representation with richer content. Both may exist for the same real-world funder; `organisation_code` links them.
- **`crossref_funder_doi` rename:** Source file uses `funder_doi`. Canonical renames to `crossref_funder_doi` to make the source explicit — this is a CrossRef-namespace DOI, not a generic DOI.
- **`works_funded_count` dropped:** The source golden record included `works_funded_count` from OpenAlex. This is derived from the Resource table and should not be stored as a source-of-truth field. Replaced by the derived `funded_resource_count`.
- **`institution_entity_id` cross-link replaced:** Source file carried `institution_entity_id` as a cross-link to the Institution entity when the funder also had a ROR ID. Canonical replaces this with `organisation_code` → Organisation (which absorbs Institution/Organisation conflicts) and `ror_id` for the raw ROR identifier.
- **Refresh cycle:** Annually. Estimated 50–100 records.
- **Data sources:** CrossRef Funder Registry (primary — funder DOI, name); OpenAlex Funders (country, homepage, description); ROR (cross-linking); funder website scrape (grants_database_url, description).
