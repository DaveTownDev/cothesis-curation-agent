# ResourceSubtype.reporting_guideline — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: reporting_guideline
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A reporting guideline is a structured checklist or framework for transparent reporting of research — CONSORT, STROBE, PRISMA, etc. — including extensions, endorsing journals, and methodology coverage.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `acronym` | string | No | Guideline acronym e.g. `CONSORT`, `STROBE`, `PRISMA`, `AGREE`. Was: `guideline_acronym`. |
| `full_title` | string | No | Full guideline title. Was: `guideline_name`. Maps to Resource.title (canonical). |
| `checklist_url` | string (uri) | No | URL to the checklist document. |
| `explanation_elaboration_url` | string (uri) | No | URL to the E&E (explanation and elaboration) document. Was: `ee_url`. |
| `flow_diagram_url` | string (uri) | No | URL to the flow diagram template (where applicable). |
| `extension_codes` | string[] | No | Resource.code[] for guideline extensions (self-referential). e.g. CONSORT-AI, CONSORT-Harms. Was: `extensions`, `parent_guideline_id`. |
| `parent_guideline_code` | string | No | Resource.code of the parent guideline (if this is an extension). |
| `extension_count` | integer | No | Count of active extensions. Derived from extension_codes length. |
| `methodology_codes_covered` | string[] | No | FK to Methodology.code[]. Study designs/methodologies this guideline covers. Distinct from Resource.methodology_codes (which codes the resource itself). |
| `issuing_body_code` | string | No | FK to Organisation.code. Body that developed/maintains the guideline. Was: `development_group`, `issuing_body`, `institution_entity_id`. |
| `equator_url` | string (uri) | No | EQUATOR Network URL for this guideline. |
| `fairsharing_id` | string | No | FAIRsharing registry identifier. Cluster G. |
| `applicable_study_types` | string[] | No | Study types/designs this guideline applies to. Was: `study_types`, `domains`. |
| `guideline_scope` | string | No | AI-generated description of the guideline's scope and appropriate use. |
| `endorsing_journals` | string[] | No | Names or codes of journals that endorse this guideline. |
| `endorsing_journals_count` | integer | No | Count of endorsing journals. |
| `development_group` | string | No | Name of the development group/committee (if not captured by issuing_body_code). |
| `status` | string (enum) | No | `active` \| `superseded` \| `withdrawn`. Guideline status. Was: `reporting_guideline.status` (Cluster K). |
| `translations` | object[] | No | Available translations: `[{language_code, url, translator}]`. |
| `pmid` | string | No | PubMed ID of the primary reporting guideline publication. |
| `citation_count` | integer | No | Citation count of the primary publication. |
| `article_resource_code` | string | No | FK to Resource.code of the primary article describing/introducing the guideline. |

## Notes

- Reporting guidelines are unusual in that several "fields" are explicitly derived from a linked article record rather than stored locally (matrix §6.6). `pmid`, `citation_count`, and `is_open_access` may be sourced from the linked article via `article_resource_code`.
- `extension_codes` is self-referential (Resource.code[]) — supports the CONSORT → CONSORT-AI → CONSORT-Harms hierarchy.
- `methodology_codes_covered` is distinct from Resource.methodology_codes: the former describes what study designs the guideline covers; the latter codes the resource itself for discovery.
- Notable gap (matrix §6.5): no `thumbnail_url`/image field, no first-class `language_code` at top level (translations object captures language variants instead).
