# ResourceSubtype.article — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: article
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
An article is a peer-reviewed journal article, preprint, or conference paper — the primary academic literature subtype, with rich bibliographic metadata and citation tracking.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `journal_code` | string | No | → Journal.code. Auto-resolved via DOI lookup. Promoted to Resource base for articles; repeated here for clarity. |
| `volume` | string | No | Journal volume number. |
| `issue` | string | No | Journal issue number. |
| `pages` | string | No | Page range e.g. `123-145` or article number e.g. `e1001234`. Was: `page_count`/`pages` in matrix. |
| `peer_reviewed` | boolean | No | Whether article has undergone formal peer review. |
| `pmid` | string | No | PubMed ID. |
| `pmc_id` | string | No | PubMed Central ID (PMC). Was: `pmcid`. |
| `openalex_id` | string | No | OpenAlex record ID. |
| `preprint_server` | string | No | Preprint server name e.g. `medRxiv`, `bioRxiv`, `SSRN`. Null for published articles. |
| `preprint_id` | string | No | ID in the preprint server (e.g. medRxiv DOI suffix). |
| `retracted` | boolean | No | Whether the article has been retracted. Default false. |
| `retraction_note` | string | No | Explanation of retraction. Required if retracted=true. |
| `is_retracted` | boolean | No | Alias for retracted (matrix Cluster K). Canonical: `retracted`. |
| `altmetric_score` | number | No | Altmetric attention score. |
| `citation_count` | integer | No | Total citation count from OpenAlex/CrossRef. |
| `fwci` | number | No | Field-Weighted Citation Impact. |
| `rcr` | number | No | Relative Citation Ratio (NIH iCite). |
| `mesh_terms` | string[] | No | MeSH controlled vocabulary terms (from PubMed). |
| `author_keywords` | string[] | No | Author-supplied keywords (distinct from editorial topic_tags). |
| `abstract` | string | No | Article abstract (publisher-supplied). Maps to Resource.description; surfaced separately for article display. |
| `ebm_level` | string | No | Evidence-based medicine evidence level e.g. `1a`, `2b`, `RCT`, `systematic_review`. Feeds quality_dimensions.ebm_level. |
| `study_type` | string | No | Study design type e.g. `RCT`, `cohort`, `case_control`, `systematic_review`, `meta_analysis`. |
| `journal_impact_factor` | number | No | Journal Impact Factor at time of publication. Denormalised from Journal entity. |
| `is_erratum` | boolean | No | Whether this is a correction/erratum. |
| `linked_erratum_doi` | string | No | DOI of the associated erratum or corrected article. |

## Notes

- `article` is the most field-rich subtype (~93 total fields including inherited base). The field_mapping_article_complete.md file is v2.0 consolidated (the gold standard file per matrix §6.6).
- `retracted` and `is_retracted` are aliases (Cluster K); canonical name is `retracted`.
- `abstract` maps to the publisher-supplied Cluster B description field — stored on Resource.description for articles.
- `ebm_level` feeds `quality_dimensions.ebm_level` in AIAssessment (article-only dimension).
- Preprint articles: `preprint_server` and `preprint_id` are populated; `journal_code`, `volume`, `issue`, `pages` may be null until published.
