# CoThesis Compendium — Complete Field Mapping & Merge Logic: `reporting_guideline`

**Type:** Reporting Guidelines & Checklists
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `primary_guideline`, `guideline_extension`, `critical_appraisal_tool`

**Note:** Most reporting guidelines ARE journal articles (e.g., the CONSORT Statement is a published paper in BMJ/Annals). The guideline resource record links to its corresponding article record for citation metrics, but maintains its own golden record focused on practical use (checklist URL, E&E document, translations, endorsed-by journals). A guideline extension links to its parent primary guideline via cross-reference.

---

## 1. Architecture

```
reporting_guideline_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── guideline_source_equator (scrape)
  │     ├── guideline_source_fairsharing (API)
  │     ├── guideline_source_companion_website (scrape)
  │     ├── guideline_source_pubmed (via linked article)
  │     ├── guideline_source_crossref (via linked article DOI)
  │     ├── guideline_source_openalex (via linked article)
  │     ├── guideline_source_casp (scrape — for critical_appraisal_tool)
  │     ├── guideline_source_jbi (scrape — for critical_appraisal_tool)
  │     ├── guideline_source_cochrane (scrape — for RoB tools)
  │     ├── guideline_source_discovery
  │     └── guideline_ai_assessment
  │
  ├── Article Cross-Link
  │     └── article_resource_id (link to article record for the guideline publication)
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (guideline authors / development group)
  │     ├── journal_entity_id (where published)
  │     ├── institution_entity_ids[] (endorsing organisations)
  │     └── parent_guideline_id (for extensions)
  │
  ├── Cross-References
  │     ├── parent_guideline_id (extension → primary guideline)
  │     ├── template_resource_ids[] (linked checklists/templates)
  │     └── article_resource_id (the guideline paper itself)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

---

## 2. Source Trust Ranking

| Rank | Source | Code | Tier | Rate Limit | Free? | Rationale |
|------|--------|------|------|-----------|-------|-----------|
| 1 | EQUATOR Network | `equator` | T1 | N/A (scrape) | Free | Definitive registry for health research reporting guidelines |
| 2 | FAIRsharing | `fairsharing` | T1 | Unspecified | Free | Relational links between guidelines, journals, funders, databases |
| 3 | Companion website | `companion_site` | T1 | N/A (scrape) | Free | E&E documents, checklists, translations, flow diagrams |
| 4 | PubMed | `pubmed` | T1 | 10 req/sec | Yes | Article-level metadata for the guideline publication |
| 5 | CrossRef | `crossref` | T1 | 50 req/sec | Yes | DOI, citations, references |
| 6 | OpenAlex | `openalex` | T1 | 100K/day | Yes | Citation analytics, OA status |
| 7 | CASP | `casp` | T1 | N/A (scrape) | Free | Critical appraisal tools (for that subtype) |
| 8 | JBI | `jbi` | T1 | N/A (scrape) | Free | JBI critical appraisal tools and methodology checklists |
| 9 | Cochrane | `cochrane` | T1 | N/A (scrape) | Free | Risk of bias tools (RoB 2, ROBINS-I) |
| 10 | Discovery | `discovery` | — | N/A | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 EQUATOR Network (`guideline_source_equator`)

**Source:** equator-network.org (scrape of guideline listing pages)
**Coverage:** ~500+ reporting guidelines and extensions

| Field | Type | Description |
|-------|------|-------------|
| `equator_url` | String | EQUATOR page URL for this guideline |
| `equator_name` | String | Guideline name (e.g., "CONSORT 2010") |
| `equator_acronym` | String | Acronym (CONSORT, STROBE, PRISMA, etc.) |
| `equator_full_title` | String | Full title of the guideline paper |
| `equator_description` | Text | EQUATOR's description of the guideline |
| `equator_study_type` | Array[String] | Study types covered (RCT, observational, SR, etc.) |
| `equator_publication_doi` | String | DOI of the guideline publication |
| `equator_publication_url` | String | URL to the full-text guideline paper |
| `equator_checklist_url` | String | Direct URL to downloadable checklist |
| `equator_checklist_format` | String | PDF, Word, Excel, online |
| `equator_ee_url` | String | URL to Explanation & Elaboration document |
| `equator_ee_doi` | String | DOI of E&E document |
| `equator_flow_diagram_url` | String | URL to flow diagram template (e.g., PRISMA flow diagram) |
| `equator_translations` | Array[Object] | `{language, url}` — translated versions |
| `equator_extensions` | Array[Object] | `{name, url, study_type}` — registered extensions |
| `equator_date_published` | String | Publication date/year |
| `equator_category` | String | EQUATOR category (study design type) |
| `equator_developers` | String | Guideline development group |
| `equator_endorsed_by` | Array[String] | Journals that endorse this guideline |

---

### 3.2 FAIRsharing API (`guideline_source_fairsharing`)

**Lookup key:** Guideline name or FAIRsharing ID
**API endpoint:** `GET https://api.fairsharing.org/search/fairsharing_records?q={name}&registry=Standard`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `fairsharing_id` | `data[].id` | String | FAIRsharing record ID |
| `name` | `data[].attributes.name` | String | Standard name |
| `abbreviation` | `data[].attributes.abbreviation` | String | Abbreviation |
| `description` | `data[].attributes.description` | Text | Description |
| `doi` | `data[].attributes.doi` | String | DOI |
| `url` | `data[].attributes.homepage` | String | Homepage URL |
| `type` | `data[].attributes.record_type` | String | reporting guideline, terminology artefact, model/format |
| `status` | `data[].attributes.status` | String | ready, in_development, deprecated |
| `year_creation` | `data[].attributes.year_creation` | Integer | Year created |
| `subjects` | `data[].attributes.subjects[]` | Array[Object] | Subject classifications |
| `domains` | `data[].attributes.domains[]` | Array[Object] | Domain classifications |
| `taxonomies` | `data[].attributes.taxonomies[]` | Array[Object] | Species/taxonomies |
| `user_defined_tags` | `data[].attributes.user_defined_tags[]` | Array[String] | Tags |
| `countries` | `data[].attributes.countries[]` | Array[String] | Countries |
| `related_databases` | `data[].relationships.databases[]` | Array[Object] | Databases that implement this standard |
| `related_policies` | `data[].relationships.policies[]` | Array[Object] | Funder/journal policies that recommend this standard |
| `related_standards` | `data[].relationships.standards[]` | Array[Object] | Related standards |
| `publications` | `data[].attributes.publications[]` | Array[Object] | Linked publications with DOIs |

**Unique value:** FAIRsharing provides the relational mapping — "which funders mandate this guideline?" and "which data repositories accept data compliant with this standard?" No other source provides this.

---

### 3.3 Companion Website (`guideline_source_companion_website`)

**Source:** The guideline's own website (e.g., consort-statement.org, prisma-statement.org, strobe-statement.org)

| Field | Type | Description |
|-------|------|-------------|
| `companion_url` | String | Companion website URL |
| `checklist_url` | String | Direct download link for the checklist |
| `checklist_formats` | Array[String] | Available formats (PDF, Word, Excel, online) |
| `ee_url` | String | Explanation & Elaboration document URL |
| `flow_diagram_url` | String | Flow diagram template URL |
| `flow_diagram_tool_url` | String | Online flow diagram generator URL (e.g., PRISMA flow diagram generator) |
| `translations` | Array[Object] | `{language, url}` |
| `extensions` | Array[Object] | `{name, url, description, study_type}` |
| `endorsing_journals` | Array[String] | Journals that endorse this guideline |
| `endorsing_journals_count` | Integer | Number of endorsing journals |
| `example_articles` | Array[Object] | `{title, doi, url}` — published articles exemplifying correct use |
| `related_resources` | Array[Object] | Training materials, webinars, presentations |
| `development_group` | String | Name of the guideline development group |
| `contact_email` | String | Contact email for the group |
| `last_updated` | Date | When the website was last substantively updated |
| `version_history` | Array[Object] | `{version, year, url}` — previous versions of the guideline |

---

### 3.4 PubMed / CrossRef / OpenAlex (via linked article)

These sources use the same field inventories as defined in `field_mapping_article_complete.md`. The guideline resource links to its article record via `article_resource_id`, and the following fields are derived from the article's golden record:

| Derived Field | Source in Article Record | Description |
|--------------|--------------------------|-------------|
| `article_doi` | `doi` | DOI of the guideline paper |
| `article_pmid` | `pmid` | PubMed ID |
| `article_citation_count` | `citation_count` | How many times the guideline paper has been cited |
| `article_fwci` | `fwci` | Field-weighted citation impact |
| `article_altmetric_score` | `altmetric_score` | Attention metrics |
| `article_year` | `publication_year` | Publication year |
| `article_journal` | `journal_name` | Where published |
| `article_is_oa` | `is_open_access` | Whether freely accessible |
| `article_oa_url` | `best_oa_url` | Free access URL |

**Note:** These fields are not stored independently in the guideline golden record — they are looked up from the linked article record at display time. This avoids data duplication and ensures citation metrics stay current via the article refresh pipeline.

---

### 3.5 CASP (`guideline_source_casp`)

**Source:** casp-uk.net (scrape)
**For:** `critical_appraisal_tool` subtype

| Field | Type | Description |
|-------|------|-------------|
| `casp_url` | String | CASP page URL |
| `casp_tool_name` | String | Tool name (e.g., "CASP Qualitative Checklist") |
| `casp_study_type` | String | Which study type it appraises |
| `casp_question_count` | Integer | Number of checklist questions |
| `casp_download_url` | String | PDF download link |
| `casp_download_format` | String | PDF |
| `casp_how_to_use_url` | String | Usage instructions |
| `casp_sections` | Array[String] | Checklist sections (e.g., "Validity", "Results", "Applicability") |

---

### 3.6 JBI (`guideline_source_jbi`)

**Source:** jbi.global (scrape)
**For:** `critical_appraisal_tool` subtype and JBI methodology checklists

| Field | Type | Description |
|-------|------|-------------|
| `jbi_url` | String | JBI page URL |
| `jbi_tool_name` | String | Tool name (e.g., "JBI Checklist for Prevalence Studies") |
| `jbi_study_type` | String | Study type |
| `jbi_question_count` | Integer | Number of checklist items |
| `jbi_download_url` | String | Download link |
| `jbi_download_format` | String | PDF, Word |
| `jbi_manual_url` | String | Link to JBI reviewer's manual section |
| `jbi_domains` | Array[String] | Assessment domains |

---

### 3.7 Cochrane Risk of Bias Tools (`guideline_source_cochrane`)

**Source:** riskofbias.info, methods.cochrane.org (scrape)
**For:** `critical_appraisal_tool` subtype (specifically RoB 2, ROBINS-I, ROBINS-E)

| Field | Type | Description |
|-------|------|-------------|
| `cochrane_url` | String | Risk of Bias tool page URL |
| `tool_name` | String | Tool name (RoB 2, ROBINS-I, ROBINS-E) |
| `tool_version` | String | Current version |
| `study_type` | String | Randomized trials (RoB 2), Non-randomized (ROBINS-I), Environmental (ROBINS-E) |
| `domains` | Array[Object] | `{domain_name, description}` — assessment domains |
| `domain_count` | Integer | Number of domains |
| `download_url` | String | Tool download URL |
| `excel_template_url` | String | Excel assessment template |
| `guidance_url` | String | Detailed guidance document URL |
| `training_url` | String | Training materials URL |
| `cribsheet_url` | String | Domain-specific crib sheet URLs |
| `software_url` | String | Companion software (e.g., robvis for visualization) |

---

### 3.8 AI Assessment (`guideline_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{authority, currency, usability, specificity, adoption}` — guideline-specific dimensions |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | Which research methodologies this guideline applies to |
| `thesis_stages` | Array[String] | Primarily "Study" (data collection/reporting) and "Share" (publication) |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | primary_guideline, guideline_extension, critical_appraisal_tool |
| `editorial_description` | Text | 1–2 sentences: what this guideline covers and when to use it |
| `editorial_description_long` | Text | Extended description |
| `editorial_badges` | Array[String] | Max 3 |
| `guideline_scope` | Text | AI summary of what the guideline covers and its scope |
| `when_to_use` | Text | AI explanation of when a trainee should use this guideline |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Secondary Entity Links

### 4.1 Person (Guideline Author / Development Group)

**Relationship:** `reporting_guideline -[DEVELOPED_BY]-> person`
**Note:** Many guidelines are developed by large consortia (e.g., "The CONSORT Group"). Individual members can be linked as Person entities where identifiable, but the group name is also stored as a string field.

### 4.2 Journal (Where Published)

**Relationship:** Via linked article record → journal entity
**Note:** Many guidelines are simultaneously published in multiple journals (e.g., CONSORT appeared in BMJ, Lancet, Annals of Internal Medicine). The primary publication's journal is linked.

### 4.3 Institution (Endorsing Organisations)

**Relationship:** `reporting_guideline -[ENDORSED_BY]-> institution`
**Sources:** EQUATOR `endorsed_by`, companion_site `endorsing_journals` (journals resolved to institution entities)

### 4.4 Parent Guideline (for Extensions)

**Relationship:** `guideline_extension -[EXTENSION_OF]-> primary_guideline`
**Source:** EQUATOR `extensions`, companion site, FAIRsharing `related_standards`

---

## 5. Golden Record Merge Rules

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `guideline_acronym` | String | V | EQUATOR → FAIRsharing `abbreviation` → companion_site | CONSORT, STROBE, PRISMA, etc. |
| `guideline_name` | String | V | EQUATOR `equator_name` → FAIRsharing `name` → companion_site | Full guideline name. |
| `doi` | String | V | EQUATOR `publication_doi` → CrossRef → FAIRsharing | DOI of the guideline publication. |
| `fairsharing_id` | String | V | FAIRsharing | |
| `equator_url` | String | V | EQUATOR | URL on EQUATOR Network. |
| `article_resource_id` | String | D | Entity resolution | Link to article record for the guideline paper. |
| `url` | String | D | Derived | companion_site URL → EQUATOR URL → DOI URL. |

### 5.2 Core Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `full_title` | String | V | EQUATOR `equator_full_title` → FAIRsharing → companion_site | Full title of the guideline paper. |
| `description` | Text | V | EQUATOR `equator_description` → FAIRsharing `description` → companion_site | Official description. |
| `study_types` | Array[String] | V | EQUATOR `equator_study_type` → FAIRsharing `domains` | Study designs this guideline covers. |
| `publication_year` | Integer | V | EQUATOR `equator_date_published` → FAIRsharing `year_creation` | |
| `current_version` | String | V | companion_site `version_history[0]` → EQUATOR name parsing | E.g., "CONSORT 2010", "PRISMA 2020". |
| `development_group` | String | V | companion_site `development_group` → EQUATOR `equator_developers` | |
| `status` | String | V | FAIRsharing `status` → companion_site | `active`, `superseded`, `in_development`. |

### 5.3 Practical Use (Most Important for Trainees)

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `checklist_url` | String | V | companion_site → EQUATOR `equator_checklist_url` | Direct download link. |
| `checklist_formats` | Array[String] | V | companion_site → EQUATOR | PDF, Word, Excel, online. |
| `ee_url` | String | V | companion_site `ee_url` → EQUATOR `equator_ee_url` | Explanation & Elaboration document. |
| `ee_doi` | String | V | EQUATOR `equator_ee_doi` | |
| `flow_diagram_url` | String | V | companion_site | Flow diagram template (e.g., PRISMA). |
| `flow_diagram_tool_url` | String | V | companion_site | Online flow diagram generator. |
| `translations` | Array[Object] | V | companion_site → EQUATOR | `{language, url}`. |
| `example_articles` | Array[Object] | V | companion_site | Published articles exemplifying correct use. |
| `training_materials` | Array[Object] | V | companion_site → cochrane (for RoB tools) | Training/webinar links. |

### 5.4 Endorsement & Adoption

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `endorsing_journals` | Array[String] | V | companion_site → EQUATOR `equator_endorsed_by` | Journals requiring/recommending this guideline. |
| `endorsing_journals_count` | Integer | D | Derived | Count of endorsing journals. |
| `endorsing_funder_policies` | Array[Object] | V | FAIRsharing `related_policies` | Funder policies mandating this standard. |
| `related_databases` | Array[Object] | V | FAIRsharing `related_databases` | Databases implementing this standard. |
| `article_citation_count` | Integer | D | From linked article record | How many times the guideline paper has been cited. |

### 5.5 Extensions (for primary_guideline subtype)

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `extensions` | Array[Object] | D | EQUATOR `equator_extensions` + companion_site `extensions` | `{name, study_type, url, resource_id}`. Deduplicate. |
| `extension_count` | Integer | D | Derived | |

### 5.6 Parent Guideline (for guideline_extension subtype)

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `parent_guideline_acronym` | String | V | EQUATOR / companion_site / discovery | Parent guideline (e.g., CONSORT for CONSORT-Harms). |
| `parent_guideline_id` | String | D | Entity resolution | Link to parent guideline record. |
| `extension_scope` | String | V | EQUATOR / companion_site | What this extension adds (e.g., "for harms reporting", "for cluster trials"). |

### 5.7 Critical Appraisal Tool Fields (for critical_appraisal_tool subtype)

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `tool_name` | String | V | CASP / JBI / Cochrane | |
| `question_count` | Integer | V | CASP / JBI / Cochrane | Number of checklist questions/items. |
| `domains` | Array[Object] | V | Cochrane / JBI / CASP | Assessment domains with descriptions. |
| `download_url` | String | V | CASP / JBI / Cochrane | Direct download. |
| `download_formats` | Array[String] | V | CASP / JBI / Cochrane | PDF, Word, Excel. |
| `excel_template_url` | String | V | Cochrane | For RoB tools with Excel templates. |
| `guidance_url` | String | V | Cochrane / JBI | Detailed usage guidance. |
| `companion_software` | Object | V | Cochrane `software_url` | E.g., robvis for RoB visualization. |

### 5.8 LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Name, study types, description | When to use this guideline. |
| `editorial_description_long` | Text | L | All data | Extended description. |
| `guideline_scope` | Text | L | Description, study types, checklist items | AI summary of scope. |
| `when_to_use` | Text | L | Study types, methodology context | Plain-language guidance for trainees. |
| `methodology_tags` | Array[String] | L | AI Assessment | 162-methodology taxonomy. |
| `thesis_stages` | Array[String] | L | AI Assessment | Primarily Study, Share. |
| `difficulty_level` | String | L | AI Assessment | |
| `editorial_badges` | Array[String] | L | Adoption, citation count, status | Max 3. |
| `quality_score` | Float (0–1) | L | All data | |
| `quality_dimensions` | Object | L | | `{authority, currency, usability, specificity, adoption}` |

### 5.9 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `author_entity_ids` | Array[String] | D | Development group members → Person entities. |
| `journal_entity_id` | String | D | Via linked article record. |
| `endorsing_institution_ids` | Array[String] | D | Endorsing organisations → Institution entities. |
| `parent_guideline_id` | String | D | For extensions → parent guideline record. |
| `template_resource_ids` | Array[String] | D | Linked checklist/template resources in directory. |

---

## 6. Field Provenance & Versioning

Same structure as previous types.

---

## 7. Refresh Tiers

| Tier | Scope | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Active** | Current guidelines (status=active) | Quarterly | Companion website (new translations, extensions), EQUATOR, link check |
| **Stable** | Established guidelines with no recent changes | Biannually | Companion website, EQUATOR, FAIRsharing, link check |
| **Superseded** | Older versions (e.g., PRISMA 2009 after PRISMA 2020) | Annually | Link check only; mark as superseded |

**Key monitoring signals:**
- New versions of major guidelines (CONSORT, PRISMA, STROBE) — check companion sites quarterly
- New extensions — EQUATOR listing scrape quarterly
- New endorsing journals — companion site scrape quarterly
- FAIRsharing policy links — annual refresh

---

## 8. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| Checklist URLs | Companion site | May change hosting location |
| Translations | Companion site / EQUATOR | New translations added over time |
| Extensions | EQUATOR / companion site | New extensions published periodically |
| Endorsing journals | Companion site | Journals may adopt guidelines |
| Citation count | Via article record | Article pipeline handles this |
| Funder policies | FAIRsharing | Funders may mandate new guidelines |
| Version updates | Companion site | Major guideline updates every 5–15 years |

---

## 9. Field Summary

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~30 | guideline_name, acronym, study_types, checklist_url, ee_url, translations, endorsing_journals, domains |
| Derived (D) | ~10 | url, extension_count, endorsing_journals_count, entity IDs, article link |
| LLM-authored (L) | ~10 | editorial_description, guideline_scope, when_to_use, methodology_tags, quality_score |
| **Total reporting_guideline golden record fields** | **~50** | |

---

## 10. Source Coverage Heatmap

| Field Category | EQUATOR | FAIRsharing | Companion | CASP | JBI | Cochrane | Article Link |
|---------------|---------|-------------|-----------|------|-----|----------|-------------|
| **Identifiers** | ●●● | ●●○ | ●○○ | ●○○ | ●○○ | ●○○ | ●●○ |
| **Core metadata** | ●●● | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | — |
| **Checklist/practical** | ●●○ | — | ●●● | ●●● | ●●● | ●●● | — |
| **Endorsement** | ●●○ | ●●● | ●●● | — | — | — | — |
| **Extensions** | ●●● | ●●○ | ●●○ | — | — | — | — |
| **Translations** | ●●○ | — | ●●● | — | — | — | — |
| **Citation metrics** | — | — | — | — | — | — | ●●● |
| **Funder policies** | — | ●●● | — | — | — | — | — |
| **Study type domains** | ●●● | ●●○ | ●●○ | ●●● | ●●● | ●●● | — |
| **Training materials** | — | — | ●●○ | ●○○ | ●○○ | ●●● | — |
