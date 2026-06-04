# ResourceSubtype.research_database — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: dataset
SUBTYPE_KEY: research_database
SOURCE: Authored — OQ-005 resolution. Distinct from `dataset` (which covers downloadable collected/published data); research_database covers queryable literature search systems and clinical trial registries.
VERSION: v1.0.0 (added; canonical subtype count bumps from 61 → 62; taxonomy v2.1 → v2.2)

## Purpose

A research_database is a queryable search interface for literature, trials, or structured clinical knowledge — NOT a downloadable data file. Examples: PubMed (MEDLINE), Embase, CINAHL, Cochrane Library, ClinicalTrials.gov, PROSPERO, PsycINFO.

Distinct from `dataset` subtype:
- `dataset` = data you download and analyse (records, variables, CSVs, formats)
- `research_database` = a system you query to find literature, trials, or guidelines

Distinct from `software` subtype:
- `software` = tools you install or run
- `research_database` = a knowledge base you search (may have an API, but the primary value is the curated content, not the tool)

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `query_interface_type` | enum | No | `search_form \| api \| both` — how the database is accessed |
| `access_tier` | enum | No | `open \| registered \| institutional \| paid` — access requirements |
| `api_documentation_url` | string | No | URL to API documentation if available |
| `record_count_approximate` | integer | No | Approximate number of indexed records/citations |
| `data_dictionary_url` | string | No | URL to field/index documentation (e.g. MEDLINE field tags) |
| `update_frequency` | enum | No | `daily \| weekly \| monthly \| quarterly \| irregular` — how often the database is updated |
| `coverage_start_year` | integer | No | Earliest year of indexed content |
| `primary_content_type` | enum | No | `literature \| trials \| systematic_reviews \| guidelines \| protocols \| mixed` |
| `indexing_criteria_url` | string | No | URL to the database's indexing criteria or scope notes |
| `search_filter_support` | string[] | No | Supported search filter types (e.g. `["date_range", "study_type", "publication_type", "mesh_terms"]`) |
| `mesh_indexed` | boolean | No | Whether records are MeSH-indexed (relevant for systematic review search strategy) |
| `login_required` | boolean | No | Whether a free account is required to access (separate from access_tier) |

## Notes

- `access_tier` is the canonical field name. Distinguishes open (PubMed), registered (PROSPERO submission), institutional (Embase), and paid (CINAHL standalone) access.
- `mesh_indexed` is specifically relevant to systematic review methodology: MEDLINE is MeSH-indexed; Embase uses Emtree; others use free-text or title/abstract only. This affects search strategy design.
- `primary_content_type = trials` → ClinicalTrials.gov, ANZCTR, ISRCTN, EUCTR
- `primary_content_type = systematic_reviews` → Cochrane Library, PROSPERO (protocols), DARE
- `primary_content_type = literature` → PubMed/MEDLINE, Embase, CINAHL, PsycINFO, Scopus, Web of Science

## Taxonomy Note

This subtype was added in taxonomy v2.2 (OQ-005 resolution). Canonical subtype count: 62.
The parent `dataset` ResourceType (type 12) now has 4 subtypes: research_dataset, teaching_dataset, open_data_portal, research_database.
