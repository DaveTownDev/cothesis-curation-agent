# ResourceSubtype.software — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: software
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A software resource is a standalone application, tool, or library relevant to research methodology — including statistical packages, reference managers, systematic review tools, data collection apps, and analysis platforms.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `platform` | string | No | Primary platform description e.g. `Windows/Mac/Web`, `Web-only`, `R package`. |
| `operating_systems` | string[] | No | Supported OS list e.g. `["Windows", "macOS", "Linux"]`. Was: `platforms`. |
| `interface_type` | string (enum) | No | `GUI` \| `CLI` \| `API` \| `mixed`. |
| `primary_methodology_use` | string | No | Primary research methodology this tool supports e.g. `systematic_review`, `statistical_analysis`, `qualitative_coding`. |
| `skill_level_required` | string (enum) | No | `beginner` \| `intermediate` \| `advanced`. Subtype-specific (distinct from Resource.difficulty_level — that is AI-assessed; this is the tool's own stated requirement). |
| `learning_curve` | string (enum) | No | `low` \| `medium` \| `high`. AI-assessed (Cluster L). |
| `open_source` | boolean | No | Whether the software is open source. Was: `is_open_source`. |
| `github_url` | string (uri) | No | GitHub repository URL. |
| `github_stars` | integer | No | GitHub star count (freshness metric). |
| `github_forks` | integer | No | GitHub fork count. |
| `github_contributors` | integer | No | GitHub contributor count. |
| `oss_health_signal` | string (enum) | No | Open-source project health: `active` \| `maintained` \| `stale` \| `archived`. Derived from GitHub activity. |
| `documentation_url` | string (uri) | No | URL to official documentation. |
| `pypi_name` | string | No | PyPI package name (Python packages). |
| `cran_name` | string | No | CRAN package name (R packages). |
| `rrid` | string | No | Research Resource Identifier (e.g. `RRID:SCR_001622`). |
| `rrid_publication_mentions` | integer | No | Count of publications citing this RRID (proxy for usage). |
| `alternatives` | string[] | No | Alternative tool names or resource_codes. Was: `alternative_resource_ids`. |
| `integrations` | string[] | No | Tools/systems this software integrates with. |
| `features` | string[] | No | Key feature list. |
| `comparable_tools` | string[] | No | AI-assessed comparable tools. |
| `key_limitations` | string[] | No | AI-assessed key limitations. |
| `pricing_model` | string | No | Pricing model description e.g. `freemium`, `subscription`, `one-time`. Cluster M. |
| `pricing_tiers` | object[] | No | Structured pricing tiers: `[{name, price, currency, period, features[]}]`. |
| `starting_price` | number | No | Starting/lowest price point. |
| `price_currency` | string | No | ISO 4217 currency code for price fields. |
| `has_free_tier` | boolean | No | Whether a free tier or trial is available. |
| `app_store_price` | string | No | App store pricing string. |
| `g2_rating` | number | No | G2 crowd average rating. |
| `capterra_rating` | number | No | Capterra average rating. |
| `app_store_rating` | number | No | App store average rating. |
| `bio_tools_id` | string | No | bio.tools registry identifier (bioinformatics tools). |
| `edam_topics` | string[] | No | EDAM ontology topic terms (bio.tools). |
| `edam_operations` | string[] | No | EDAM ontology operation terms (bio.tools). |
| `maturity` | string | No | Software maturity level (bio.tools: `Emerging`, `Mature`, `Legacy`). |
| `has_api` | boolean | No | Whether the software exposes an API. |
| `favicon_url` | string (uri) | No | Software/tool favicon. Cluster F. |
| `screenshot_urls` | string[] | No | Product screenshot URLs. Cluster F. |
| `logo_url` | string (uri) | No | Software logo URL. Cluster F; canonical thumbnail_url is the standardised form. |
| `developer_name` | string | No | Developer or company name (free-text). |
| `developer_url` | string (uri) | No | Developer website URL. |
| `developer_person_id` | string | No | → Person.code for individual developer. |

## Notes

- Software is the second-largest subtype by field count (~87 total including inherited). field_mapping_software_complete.md covers 14 sub-subtypes with a per-subtype source applicability matrix.
- `open_source` is the canonical name (was: `is_open_source` in matrix). Boolean.
- `skill_level_required` is the tool's stated requirement; `difficulty_level` on AIAssessment is the AI's independent assessment of how hard it is to use — these can differ.
- `learning_curve` is classified LLM-authored in the matrix (Cluster L) — stored here as a subtype field but note it originates from AI assessment pipeline and should be treated accordingly.
- Cluster G identifiers (`rrid`, `pypi_name`, `cran_name`, `bio_tools_id`) provide cross-registry lookup capability.
