# ResourceSubtype.dataset — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: dataset
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A dataset is a structured collection of data — clinical, epidemiological, genomic, survey, or administrative — with data format, access, coverage, and repository metadata.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `data_format` | string[] | No | File format(s) e.g. `["CSV", "JSON", "STATA", "SPSS", "NetCDF"]`. Was: `file_formats`, `formats`. |
| `record_count` | integer | No | Number of records/observations. Was: `temporal_coverage` includes this; stored separately. |
| `variable_count` | integer | No | Number of variables/columns. |
| `date_range_start` | string (date) | No | Start of temporal coverage. Was: `temporal_coverage.start`. |
| `date_range_end` | string (date) | No | End of temporal coverage. Was: `temporal_coverage.end`. |
| `data_access` | string (enum) | No | `open` \| `credentialed` \| `restricted` \| `request`. Was: `access_type` / `access_requirements` on dataset. |
| `repository_url` | string (uri) | No | URL to the data repository (PhysioNet, Kaggle, Zenodo, etc.). |
| `data_doi` | string | No | DOI for the dataset itself (Zenodo DOI, DataCite DOI). Distinct from any linked publication DOI. |
| `api_url` | string (uri) | No | API endpoint for programmatic access. |
| `api_available` | boolean | No | Whether programmatic API access is available. |
| `download_url` | string (uri) | No | Direct download URL (open datasets). |
| `data_dictionary_url` | string (uri) | No | URL to data dictionary or codebook. |
| `geographic_scope` | string | No | Geographic coverage description e.g. `Australia`, `Global`, `Multi-national`. |
| `geographic_coverage` | string[] | No | Country codes or region names covered. |
| `file_count` | integer | No | Number of files in the dataset. |
| `file_size` | string | No | Total dataset size e.g. `2.3 GB`. |
| `related_publication_dois` | string[] | No | DOIs of publications using or describing this dataset. |
| `kaggle_usability_score` | number | No | Kaggle usability score (Kaggle datasets). |
| `openalex_id` | string | No | OpenAlex record ID (if dataset is also indexed there). |
| `zenodo_doi` | string | No | Zenodo-specific DOI (if hosted on Zenodo). |
| `figshare_id` | string | No | Figshare item ID. |
| `fairsharing_id` | string | No | FAIRsharing registry identifier. |
| `download_count` | integer | No | Total download count. |
| `view_count` | integer | No | Total view count in repository. |
| `source_article_code` | string | No | → Resource.code of the primary article describing this dataset. |
| `access_summary` | string | No | AI-generated summary of access requirements and process. |

## Notes

- `data_access` is the canonical field name (was: `access_type` or `access_requirements` on dataset subtype — Cluster K). This is distinct from Resource.access_type which covers the general access model.
- `date_range_start` / `date_range_end` replace the nested `temporal_coverage` object from the matrix for simpler querying.
- `data_doi` is distinct from Resource.doi (which may point to a linked publication). Datasets have their own citable DOIs.
- Figshare/Zenodo hosting is noted in matrix §6.6 as "same as visual_reference" for some sources — field shapes are shared.
