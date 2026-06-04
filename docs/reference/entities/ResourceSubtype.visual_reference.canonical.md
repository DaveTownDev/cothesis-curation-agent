# ResourceSubtype.visual_reference — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: visual_reference
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A visual reference is an infographic, diagram, slide deck, poster, or figure that communicates research concepts visually — designed for quick comprehension, teaching, or reference.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `visual_type` | string (enum) | No | `infographic` \| `diagram` \| `slide_deck` \| `poster` \| `figure` \| `flowchart` \| `table` \| `illustration`. |
| `file_format` | string | No | Primary file format e.g. `PNG`, `PDF`, `PPTX`, `SVG`. Was: `file_formats`, `formats`. |
| `resolution` | string | No | Image resolution e.g. `1920x1080`, `300dpi`. |
| `dimensions` | string | No | Physical dimensions (for print-designed materials) e.g. `A0`, `A4 landscape`. |
| `is_embargoed` | boolean | No | Whether the visual is under embargo. Cluster K. |
| `embargo_end_date` | string (date) | No | Embargo lift date. |
| `view_count` | integer | No | Total views in repository. |
| `download_count` | integer | No | Total downloads. |
| `like_count` | integer | No | Likes/endorsements. |
| `share_count` | integer | No | Share count (Figshare). |
| `figshare_id` | string | No | Figshare item ID. Cluster G. |
| `zenodo_doi` | string | No | Zenodo-specific DOI. Cluster G. |
| `f1000_id` | string | No | F1000Research figure ID. Cluster G. |
| `openalex_id` | string | No | OpenAlex record ID. |
| `creator_names` | string[] | No | Creator/artist names (free-text). Cluster C; maps to Resource.authors. |
| `creator_person_ids` | string[] | No | FK to Person.code[] for creators. |
| `conference_entity_id` | string | No | FK to Conference entity if this is a conference poster. |
| `source_article_code` | string | No | FK to Resource.code of the article this figure/poster is from or associated with. |
| `article_resource_id` | string | No | UUID of the associated article resource (legacy; use source_article_code per P4). |

## Notes

- Visual reference is one of the three sparsest subtypes (~37 total fields including inherited).
- Notable gaps (matrix §6.5): no `language_code` at top level (gap — most visuals are in English but multilingual visuals exist), no `is_open_access` flag (gap — most are CC BY but flag is absent), no normalised `publication_year`.
- Cluster F: `thumbnail_url` on Resource base is the canonical image field; for visual references, the thumbnail IS effectively a preview of the primary content.
- `source_article_code` enables the cross-reference between a visual (e.g. a CONSORT diagram) and its source publication.
