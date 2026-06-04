# ResourceSubtype.template — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: template
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A template is a reusable document, form, or structured file that researchers can download and adapt — data extraction forms, ethics applications, GANTT charts, data management plans, etc.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `template_format` | string (enum) | No | `docx` \| `xlsx` \| `pdf` \| `pptx` \| `csv` \| `other`. Primary file format. Was: `file_formats`, `formats`. |
| `template_url` | string (uri) | No | Direct URL to download or access the template. |
| `download_url` | string (uri) | No | Alias for template_url / alternative download endpoint. |
| `methodology_codes_applicable` | string[] | No | FK to Methodology.code[]. Methodologies this template is designed for. Distinct from Resource.methodology_codes. |
| `stage_codes_applicable` | string[] | No | FK to Stage.code[]. THESIS stages this template is most useful for. Distinct from Resource.stage_codes. |
| `issuing_body_code` | string | No | FK to Organisation.code. Organisation that issued/developed the template. Was: `issuing_body`, `institution_entity_id`. |
| `is_peer_reviewed` | boolean | No | Whether the template has been peer-reviewed (e.g. protocols.io templates). |
| `sections` | string[] | No | Major sections in the template (for preview/display). |
| `applicable_study_types` | string[] | No | Study types/designs this template is appropriate for. |
| `jurisdiction` | string | No | Regulatory/ethical jurisdiction this template is designed for e.g. `Australia`, `EU`. |
| `aligned_guideline_code` | string | No | FK to Resource.code of the reporting guideline this template is aligned with (e.g. a CONSORT checklist template). |
| `version_date` | string (date) | No | Version/update date. Cluster D. Maps to Resource.publication_date. |
| `translations` | object[] | No | Available translations: `[{language_code, url}]`. |
| `github_url` | string (uri) | No | GitHub repository (for templates maintained as code). |
| `github_stars` | integer | No | GitHub star count. |
| `protocols_io_url` | string (uri) | No | protocols.io URL (for protocol templates). |
| `nct_id` | string | No | ClinicalTrials.gov ID (for trial-related templates). Cluster G. |
| `fork_count` | integer | No | Fork count (protocols.io or GitHub). |

## Notes

- Template is one of the three sparsest subtypes (matrix §6.6, ~36 total fields). The most significant gap is the complete absence of any topic/tag/keyword field in the golden record merge rules — `topic_tags` from Resource base addresses this, but the subtype file itself had no such field.
- `methodology_codes_applicable` and `stage_codes_applicable` describe what the template is for (intended use); Resource.methodology_codes and Resource.stage_codes describe how the template is indexed for discovery — both sets are needed.
- `aligned_guideline_code` creates a cross-reference to reporting_guideline resources (e.g. a PRISMA checklist template links to the PRISMA reporting guideline resource).
- Notable gap (matrix §6.5): no `thumbnail_url`/preview image, no `publication_year` normalisation (use `version_date`).
