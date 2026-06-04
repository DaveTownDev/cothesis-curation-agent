# CoThesis Compendium — Complete Field Mapping & Merge Logic: `article`

**Type:** Journal Articles & Papers
**Version:** 2.0 (consolidated)
**Date:** April 2026
**Supersedes:** `field_mapping_article.md` v1.0, `field_mapping_article_secondary_entities.md` v1.0, `field_mapping_article_merge_logic.md` v1.0, `field_mapping_article_addendum.md` v1.0

**Subtypes covered:** `seminal_paper`, `methodology_review`, `exemplar_study`, `methodology_paper`, `methodology_comparison`, `research_article`, `review_article`, `preprint`, `editorial`, `guideline_article`

---

## 1. Architecture

Each article resource has:
- **1 master record** (the golden record displayed in the directory)
- **Up to 13 source sub-records** from enrichment APIs
- **1 AI assessment record** from the quality/classification pipeline
- **1 discovery record** from the original discovery source
- **Links to shared secondary entities** (Person, Journal, Institution, Funder)

```
article_master (golden record)
  │
  ├── Source Sub-Records (persisted in graph, refreshed independently)
  │     ├── article_source_crossref
  │     ├── article_source_pubmed
  │     ├── article_source_openalex
  │     ├── article_source_semantic_scholar
  │     ├── article_source_unpaywall
  │     ├── article_source_nih_icite
  │     ├── article_source_dimensions
  │     ├── article_source_europe_pmc
  │     ├── article_source_lens
  │     ├── article_source_plumx
  │     ├── article_source_overton
  │     ├── article_source_pubpeer
  │     ├── article_source_discovery
  │     └── article_ai_assessment
  │
  ├── Article-Level Impact Enrichment
  │     ├── article_altmetrics (Altmetric.com)
  │     ├── article_citation_context (Scite.ai)
  │     ├── article_supplementary_materials (journal website scrape)
  │     └── article_retraction_status (CrossRef + Retraction Watch)
  │
  ├── Secondary Entity Links (shared entities — defined in secondary_entity_reference.md)
  │     ├── person_entity_ids[] (one per author)
  │     ├── journal_entity_id
  │     ├── institution_entity_ids[]
  │     └── funder_entity_ids[]
  │
  └── Metadata
        ├── field_provenance: {field_name: {source, timestamp}}
        ├── golden_record_version: timestamp
        ├── golden_record_hash: sha256
        └── source_sub_record_versions: {source: timestamp}
```

**Rebuild trigger:** The periodic source refresh pipeline compares each source sub-record's new data against its previous snapshot. If any field value has changed, the golden record is flagged for rebuild. The rebuild re-runs the merge logic against current source sub-records. If the resulting golden record hash differs from the stored hash, the new version is persisted and the `golden_record_version` timestamp is updated.

**AI assessment regeneration:** Only triggered when the refresh pipeline flags a significant change (e.g., retraction detected, citation count crosses a threshold, new OA version found). The AI assessment record is otherwise stable.

---

## 2. Source Trust Ranking

Used to resolve the priority source for verbatim fields. Ranking reflects data quality, completeness, editorial curation, and institutional trust.

| Rank | Source | Code | Tier | Rate Limit | Free? | Rationale |
|------|--------|------|------|-----------|-------|-----------|
| 1 | PubMed E-utilities | `pubmed` | T1 | 10 req/sec (API key); 3/sec without | Yes | Curated by NLM librarians; structured abstracts; authoritative MeSH indexing; trusted by the global medical community |
| 2 | CrossRef | `crossref` | T1 | 50 req/sec (polite pool with mailto header) | Yes | Publisher-deposited metadata; authoritative for DOI, dates, references, funding; most complete bibliographic record |
| 3 | OpenAlex | `openalex` | T1 | 100K credits/day (free API key) | Yes | Largest open dataset; excellent author-institution linking; best citation analytics; very current |
| 4 | NIH iCite | `nih_icite` | T1 | 200 PMIDs/request; no stated rate limit | Yes | Authoritative for Relative Citation Ratio, APT, clinical classification — unique to this source |
| 5 | Unpaywall | `unpaywall` | T1 | 100K req/day | Yes | Authoritative specifically for OA status and OA URLs |
| 6 | Europe PMC | `europe_pmc` | T1 | Standard (generous) | Yes | Authoritative for text-mined annotations and grant linkage from 26+ funders |
| 7 | Dimensions | `dimensions` | T1 | 30 req/min (free tier) | Yes (non-commercial) | Authoritative for cross-system linkage (grants→trials→patents→policy) |
| 8 | Semantic Scholar | `semantic_scholar` | T1 | 100 req/5 min | Yes | Influential citations, TLDR, embeddings |
| 9 | Lens.org | `lens` | T2 | Per plan (free academic tier) | Yes (academic) | Authoritative for patent citation detail |
| 10 | Altmetric.com | `altmetric` | T1 | Unspecified (reasonable for individual lookups) | Yes (Details Page API) | Attention metrics — social, news, policy |
| 11 | Overton | `overton` | T2 | Per licence | Paid (institutional) | Authoritative for policy citation detail |
| 12 | PlumX | `plumx` | T3 | Per subscription | Paid (institutional) | Usage/engagement metrics |
| 13 | PubPeer | `pubpeer` | T2 | Per agreement | Yes (API key) | Post-publication integrity signal |
| 14 | Scite.ai | `scite` | T2 | Per plan | Paid | Citation context (supporting/contrasting/mentioning) |
| 15 | Discovery record | `discovery` | — | N/A | N/A | Agent-provided; useful as fallback but unverified |

**Enrichment tier assignments (which sources are called for which articles):**

| Enrichment Tier | Which Articles | Sources Called |
|----------------|----------------|---------------|
| Tier 1 (every article) | All | CrossRef, PubMed, OpenAlex, Unpaywall, NIH iCite, Altmetric |
| Tier 2 (high-quality articles) | citation_count > 50 OR badged OR AI quality_score > 0.7 | + Semantic Scholar, Europe PMC, Dimensions, Scite.ai, PubPeer |
| Tier 3 (featured/badged articles) | Editor's Choice, Essential Reference, or manually flagged | + Lens.org, Overton, PlumX — full enrichment |

---

## 3. Source Sub-Record Field Inventories

### 3.1 CrossRef (`article_source_crossref`)

**Lookup key:** DOI
**API endpoint:** `GET https://api.crossref.org/works/{doi}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `doi` | `message.DOI` | String | Digital Object Identifier |
| `title` | `message.title[0]` | String | Article title (array, take first) |
| `subtitle` | `message.subtitle[0]` | String | Article subtitle if present |
| `container_title` | `message.container-title[0]` | String | Journal name |
| `container_title_short` | `message.short-container-title[0]` | String | Journal abbreviation |
| `volume` | `message.volume` | String | Volume number |
| `issue` | `message.issue` | String | Issue number |
| `page` | `message.page` | String | Page range (e.g., "123-145") |
| `article_number` | `message.article-number` | String | Article number (for journals without page numbers) |
| `type` | `message.type` | String | CrossRef type: journal-article, book-chapter, proceedings-article, etc. |
| `publisher` | `message.publisher` | String | Publisher name |
| `issn_print` | `message.ISSN[0]` | String | Print ISSN |
| `issn_electronic` | `message.ISSN[1]` | String | Electronic ISSN |
| `language` | `message.language` | String | ISO language code |
| `published_print_date` | `message.published-print.date-parts[0]` | Array[Int] | [year, month, day] — print publication date |
| `published_online_date` | `message.published-online.date-parts[0]` | Array[Int] | [year, month, day] — online publication date |
| `created_date` | `message.created.date-time` | DateTime | When record was created in CrossRef |
| `deposited_date` | `message.deposited.date-time` | DateTime | When metadata was last deposited |
| `abstract` | `message.abstract` | String (JATS XML) | Abstract text (often in JATS XML format — needs stripping) |
| `authors` | `message.author[]` | Array[Object] | Author list — see author sub-fields below |
| `citation_count` | `message.is-referenced-by-count` | Integer | Number of works citing this one |
| `reference_count` | `message.references-count` | Integer | Number of references in this work |
| `references` | `message.reference[]` | Array[Object] | Reference list with DOIs where available |
| `subject` | `message.subject[]` | Array[String] | Subject categories (being deprecated by CrossRef) |
| `license` | `message.license[].URL` | Array[Object] | License URL(s) and start dates |
| `link` | `message.link[]` | Array[Object] | Full-text links (content-type, intended-application) |
| `url` | `message.URL` | String | DOI resolution URL |
| `resource_url` | `message.resource.primary.URL` | String | Publisher landing page URL |
| `funders` | `message.funder[]` | Array[Object] | Funding bodies with grant award numbers |
| `update_to` | `message.update-to[]` | Array[Object] | Corrections, retractions, updates |
| `clinical_trial_number` | `message.clinical-trial-number[]` | Array[Object] | Linked clinical trial registrations |

**Author sub-fields** (per author in `message.author[]`):

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `given` | `author[].given` | String | First name |
| `family` | `author[].family` | String | Last name |
| `orcid` | `author[].ORCID` | String | ORCID URL (if deposited) |
| `affiliation` | `author[].affiliation[].name` | Array[String] | Institutional affiliations |
| `sequence` | `author[].sequence` | String | "first" or "additional" |
| `authenticated_orcid` | `author[].authenticated-orcid` | Boolean | Whether ORCID was authenticated |

---

### 3.2 PubMed E-utilities (`article_source_pubmed`)

**Lookup key:** PMID or DOI (via ESearch → EFetch)
**API endpoint:** `GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=xml`

| Field | XML Path | Data Type | Description |
|-------|----------|-----------|-------------|
| `pmid` | `MedlineCitation/PMID` | String | PubMed identifier |
| `pmcid` | `PubmedData/ArticleIdList/ArticleId[@IdType="pmc"]` | String | PubMed Central ID (PMCxxxxxxx) |
| `doi` | `PubmedData/ArticleIdList/ArticleId[@IdType="doi"]` | String | DOI |
| `title` | `MedlineCitation/Article/ArticleTitle` | String | Article title |
| `abstract` | `MedlineCitation/Article/Abstract/AbstractText` | String/Structured | Abstract — may be structured (Background, Methods, Results, Conclusions) |
| `abstract_structured` | `Abstract/AbstractText[]@Label` | Object | Labelled abstract sections |
| `journal_title` | `MedlineCitation/Article/Journal/Title` | String | Full journal title |
| `journal_abbreviation` | `MedlineCitation/Article/Journal/ISOAbbreviation` | String | ISO journal abbreviation |
| `journal_issn` | `MedlineCitation/Article/Journal/ISSN` | String | ISSN |
| `volume` | `MedlineCitation/Article/Journal/JournalIssue/Volume` | String | Volume |
| `issue` | `MedlineCitation/Article/Journal/JournalIssue/Issue` | String | Issue |
| `pagination` | `MedlineCitation/Article/Pagination/MedlinePgn` | String | Page range |
| `pub_date` | `MedlineCitation/Article/Journal/JournalIssue/PubDate` | Object | Year, Month, Day (may be partial) |
| `article_date` | `MedlineCitation/Article/ArticleDate` | Object | Electronic publication date |
| `authors` | `MedlineCitation/Article/AuthorList/Author[]` | Array[Object] | Author list — see sub-fields below |
| `language` | `MedlineCitation/Article/Language` | String | Language code (eng, fre, etc.) |
| `publication_types` | `MedlineCitation/Article/PublicationTypeList/PublicationType[]` | Array[String] | "Journal Article", "Review", "Randomized Controlled Trial", "Meta-Analysis", etc. |
| `mesh_terms` | `MedlineCitation/MeshHeadingList/MeshHeading[]` | Array[Object] | MeSH descriptors with qualifiers and major topic flag |
| `keywords` | `MedlineCitation/KeywordList/Keyword[]` | Array[String] | Author-assigned keywords |
| `grants` | `MedlineCitation/Article/GrantList/Grant[]` | Array[Object] | Funding grants (GrantID, Agency, Country) |
| `data_bank_list` | `MedlineCitation/Article/DataBankList` | Array[Object] | Clinical trial registrations, gene/protein accessions |
| `conflict_of_interest` | `MedlineCitation/CoiStatement` | String | Conflict of interest statement |
| `publication_status` | `PubmedData/PublicationStatus` | String | epublish, ppublish, aheadofprint |
| `full_text_urls` | `PubmedData/ArticleIdList` | Array | Links to PMC full text |
| `date_created` | `MedlineCitation/DateCreated` | Date | When record was created in PubMed |
| `date_revised` | `MedlineCitation/DateRevised` | Date | Last revision date |

**PubMed author sub-fields** (per author):

| Field | XML Path | Type | Description |
|-------|----------|------|-------------|
| `last_name` | `Author/LastName` | String | Surname |
| `fore_name` | `Author/ForeName` | String | Given name(s) |
| `initials` | `Author/Initials` | String | Author initials |
| `affiliation` | `Author/AffiliationInfo/Affiliation` | String | Full affiliation string |
| `orcid` | `Author/Identifier[@Source="ORCID"]` | String | ORCID if indexed |
| `collective_name` | `Author/CollectiveName` | String | For group authors (e.g., "CONSORT Group") |

---

### 3.3 OpenAlex (`article_source_openalex`)

**Lookup key:** DOI, PMID, PMCID, or OpenAlex ID
**API endpoint:** `GET https://api.openalex.org/works/{identifier}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `openalex_id` | `id` | String | OpenAlex ID (e.g., W2741809807) |
| `doi` | `doi` | String | DOI |
| `title` | `title` | String | Article title |
| `publication_date` | `publication_date` | Date | YYYY-MM-DD |
| `publication_year` | `publication_year` | Integer | Year |
| `type` | `type` | String | article, review, book-chapter, etc. |
| `type_crossref` | `type_crossref` | String | CrossRef type mapping |
| `is_oa` | `open_access.is_oa` | Boolean | Whether open access |
| `oa_status` | `open_access.oa_status` | String | gold, green, hybrid, bronze, diamond, closed |
| `oa_url` | `open_access.oa_url` | String | Best OA URL |
| `primary_location` | `primary_location` | Object | Source, license, version, is_oa, landing_page_url, pdf_url |
| `source_name` | `primary_location.source.display_name` | String | Journal/source name |
| `source_issn` | `primary_location.source.issn` | Array[String] | ISSNs |
| `source_type` | `primary_location.source.type` | String | journal, repository, ebook platform |
| `source_is_oa` | `primary_location.source.is_oa` | Boolean | Whether journal is fully OA |
| `cited_by_count` | `cited_by_count` | Integer | Total citation count |
| `citation_normalized_percentile` | `citation_normalized_percentile` | Object | Min/max percentile within year+subfield |
| `fwci` | `fwci` | Float | Field-weighted citation impact |
| `counts_by_year` | `counts_by_year[]` | Array[Object] | Citations per year (last 10 years) |
| `authorships` | `authorships[]` | Array[Object] | Authors with institutions — see sub-fields |
| `countries_distinct_count` | `countries_distinct_count` | Integer | Number of countries represented |
| `institutions_distinct_count` | `institutions_distinct_count` | Integer | Number of institutions |
| `abstract_inverted_index` | `abstract_inverted_index` | Object | Inverted index (reconstruct abstract from word→position mapping) |
| `topics` | `topics[]` | Array[Object] | OpenAlex topic assignments with scores |
| `keywords` | `keywords[]` | Array[Object] | OpenAlex keyword assignments with scores |
| `concepts` | `concepts[]` | Array[Object] | Legacy concept assignments (being deprecated) |
| `referenced_works` | `referenced_works[]` | Array[String] | OpenAlex IDs of cited works |
| `related_works` | `related_works[]` | Array[String] | OpenAlex IDs of related works |
| `funders` | `funders[]` | Array[Object] | Funder objects with OpenAlex IDs |
| `grants` | `grants[]` | Array[Object] | Grant details (funder, award_id) |
| `language` | `language` | String | ISO 639-1 language code |
| `is_retracted` | `is_retracted` | Boolean | Whether retracted |
| `is_paratext` | `is_paratext` | Boolean | Whether it's paratext (ToC, editorial note, etc.) |
| `locations` | `locations[]` | Array[Object] | All locations where this work is available (journal, repos, etc.) |
| `best_oa_location` | `best_oa_location` | Object | Best freely available version |
| `created_date` | `created_date` | Date | When created in OpenAlex |
| `updated_date` | `updated_date` | DateTime | When last updated in OpenAlex |

**OpenAlex authorship sub-fields** (per author in `authorships[]`):

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `author_id` | `author.id` | String | OpenAlex author ID |
| `author_name` | `author.display_name` | String | Display name |
| `author_orcid` | `author.orcid` | String | ORCID |
| `author_position` | `author_position` | String | first, middle, last |
| `institutions` | `institutions[]` | Array[Object] | Institution IDs, names, ROR IDs, country codes, types |
| `countries` | `countries[]` | Array[String] | Country codes for this author |
| `is_corresponding` | `is_corresponding` | Boolean | Whether corresponding author |
| `raw_affiliation_strings` | `raw_affiliation_strings[]` | Array[String] | Raw affiliation text |

---

### 3.4 Semantic Scholar (`article_source_semantic_scholar`)

**Lookup key:** DOI, PMID, ArXiv ID, Semantic Scholar Paper ID
**API endpoint:** `GET https://api.semanticscholar.org/graph/v1/paper/{identifier}?fields=...`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `paper_id` | `paperId` | String | Semantic Scholar paper ID |
| `external_ids` | `externalIds` | Object | `{DOI, PubMed, PubMedCentral, ArXiv, MAG, CorpusId}` |
| `title` | `title` | String | Paper title |
| `abstract` | `abstract` | String | Abstract text (plain text) |
| `year` | `year` | Integer | Publication year |
| `venue` | `venue` | String | Publication venue |
| `journal` | `journal` | Object | `{name, volume, pages}` |
| `publication_date` | `publicationDate` | Date | YYYY-MM-DD |
| `citation_count` | `citationCount` | Integer | Total citations |
| `influential_citation_count` | `influentialCitationCount` | Integer | Citations that are "influential" (S2's own metric) |
| `reference_count` | `referenceCount` | Integer | Number of references |
| `is_open_access` | `isOpenAccess` | Boolean | Whether OA |
| `open_access_pdf` | `openAccessPdf` | Object | `{url, status}` — direct PDF link |
| `authors` | `authors[]` | Array[Object] | Author list — see sub-fields |
| `publication_types` | `publicationTypes[]` | Array[String] | JournalArticle, Review, CaseReport, etc. |
| `fields_of_study` | `fieldsOfStudy[]` | Array[String] | Computer Science, Medicine, etc. |
| `s2_fields_of_study` | `s2FieldsOfStudy[]` | Array[Object] | S2-assigned fields with confidence |
| `tldr` | `tldr` | Object | `{model, text}` — AI-generated one-line summary |
| `citations` | `citations[]` | Array[Object] | List of citing papers (dehydrated) |
| `references` | `references[]` | Array[Object] | List of referenced papers (dehydrated) |
| `embedding` | `embedding` | Object | `{model, vector[]}` — paper embedding vector |
| `citation_styles` | `citationStyles` | Object | `{bibtex}` — formatted citation |

**S2 author sub-fields** (per author):

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `author_id` | `authorId` | String | S2 author ID |
| `name` | `name` | String | Author name |
| `url` | `url` | String | S2 author profile URL |

---

### 3.5 Unpaywall (`article_source_unpaywall`)

**Lookup key:** DOI
**API endpoint:** `GET https://api.unpaywall.org/v2/{doi}?email={email}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `doi` | `doi` | String | DOI |
| `is_oa` | `is_oa` | Boolean | Whether any OA version exists |
| `oa_status` | `oa_status` | String | gold, green, hybrid, bronze, closed |
| `best_oa_location_url` | `best_oa_location.url` | String | Best OA landing page URL |
| `best_oa_location_pdf` | `best_oa_location.url_for_pdf` | String | Direct PDF URL |
| `best_oa_location_license` | `best_oa_location.license` | String | License (CC-BY, CC-BY-NC, etc.) |
| `best_oa_location_version` | `best_oa_location.version` | String | publishedVersion, acceptedVersion, submittedVersion |
| `best_oa_location_host` | `best_oa_location.host_type` | String | publisher, repository |
| `title` | `title` | String | Article title |
| `journal_name` | `journal_name` | String | Journal name |
| `journal_issns` | `journal_issns` | String | Comma-separated ISSNs |
| `published_date` | `published_date` | Date | Publication date |
| `updated` | `updated` | DateTime | When Unpaywall last checked |
| `all_oa_locations` | `oa_locations[]` | Array[Object] | All OA locations found (repos, publisher, etc.) |
| `journal_is_in_doaj` | `journal_is_in_doaj` | Boolean | Whether journal is in DOAJ |
| `data_standard` | `data_standard` | Integer | Data quality level (1 or 2) |

---

### 3.6 NIH iCite (`article_source_nih_icite`)

**Lookup key:** PMID (batch: up to 200 PMIDs per request)
**API endpoint:** `GET https://icite.od.nih.gov/api/pubs?pmids={pmid1,pmid2,...}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `pmid` | `data[].pmid` | Integer | PubMed ID |
| `doi` | `data[].doi` | String | DOI |
| `title` | `data[].title` | String | Article title |
| `year` | `data[].year` | Integer | Publication year |
| `citation_count` | `data[].citation_count` | Integer | Citation count (NIH's own count) |
| `relative_citation_ratio` | `data[].relative_citation_ratio` | Float | RCR — field-normalised citation rate. 1.0 = average for field. >1.0 = above average. |
| `nih_percentile` | `data[].nih_percentile` | Float | Percentile rank among NIH-funded papers of same year and field |
| `expected_citations_per_year` | `data[].expected_citations_per_year` | Float | Expected annual citations based on field and year |
| `field_citation_rate` | `data[].field_citation_rate` | Float | Average citation rate for the paper's field |
| `is_research_article` | `data[].is_research_article` | Boolean | Whether classified as a research article (vs review, editorial, etc.) |
| `is_clinical` | `data[].is_clinical` | Boolean | Whether the article involves clinical research |
| `provisional` | `data[].provisional` | Boolean | Whether the RCR is provisional (article < 2 years old) |
| `apt` | `data[].apt` | Float | Approximate Potential to Translate — likelihood of clinical application (0–1) |
| `human` | `data[].human` | Float | Proportion of cited articles involving human subjects |
| `animal` | `data[].animal` | Float | Proportion of cited articles involving animal subjects |
| `molecular_cellular` | `data[].molecular_cellular` | Float | Proportion of cited articles at molecular/cellular level |
| `cited_by_clin` | `data[].cited_by_clin` | Array[Integer] | PMIDs of clinical articles citing this paper |
| `x_coord` | `data[].x_coord` | Float | Position on NIH's "translation spectrum" (basic → clinical → applied) |
| `y_coord` | `data[].y_coord` | Float | Position on NIH's "translation spectrum" |

---

### 3.7 Dimensions (`article_source_dimensions`)

**Lookup key:** DOI, PMID, or Dimensions ID
**API endpoint:** `POST https://app.dimensions.ai/api/dsl` (Dimensions Search Language)

| Field | DSL Path | Data Type | Description |
|-------|----------|-----------|-------------|
| `dimensions_id` | `id` | String | Dimensions publication ID |
| `field_citation_ratio` | `field_citation_ratio` | Float | Dimensions' field-normalised citation metric |
| `relative_citation_ratio` | `relative_citation_ratio` | Float | Dimensions' RCR (similar to iCite but broader coverage) |
| `grants` | `funding_details[]` | Array[Object] | Linked grants: funder name, grant ID, funder country |
| `clinical_trial_ids` | `clinical_trial_ids[]` | Array[String] | ClinicalTrials.gov IDs for linked trials |
| `patent_citations` | `times_cited_by_patents` | Integer | Number of patents citing this paper |
| `policy_citations` | `times_cited_in_policy` | Integer | Number of policy documents citing this paper |
| `research_categories` | `category_for[]` | Array[Object] | ANZSRC Fields of Research classifications |
| `sdgs` | `sustainable_development_goals[]` | Array[Object] | UN Sustainable Development Goals alignment |
| `source_title` | `source_title` | String | Journal name |
| `open_access` | `open_access_categories[]` | Array[String] | OA categories |
| `altmetric_score` | `altmetric` | Float | Altmetric score (from Altmetric.com partnership) |
| `cited_by` | `times_cited` | Integer | Dimensions citation count |

---

### 3.8 Europe PMC (`article_source_europe_pmc`)

**Lookup key:** PMID, PMC ID, or DOI
**API endpoint:** `GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={id}&format=json`
**Annotations endpoint:** `GET https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds?articleIds=MED:{pmid}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `europepmc_id` | `resultList.result[].id` | String | Europe PMC ID |
| `has_text_mined_entities` | `resultList.result[].hasTextMinedEntities` | Boolean | Whether text mining was performed |
| `text_mined_entities` | Via annotations endpoint | Array[Object] | Extracted entities: genes, diseases, chemicals, organisms, GO terms |
| `grant_ids` | `resultList.result[].grantsList.grant[]` | Array[Object] | Grants: agency, grantId, orderIn — from 26+ funders |
| `has_references` | `resultList.result[].hasReferences` | Boolean | Whether references are available |
| `reference_count` | `resultList.result[].citedByCount` | Integer | Citation count (Europe PMC's count) |
| `first_index_date` | `resultList.result[].firstIndexDate` | Date | When first indexed in Europe PMC |
| `preprint_id` | `resultList.result[].commentCorrectionList` | String | Link to preprint version |
| `published_version_doi` | (via linking endpoint) | String | For preprints: DOI of the published version |
| `has_supplementary` | `resultList.result[].hasSuppl` | Boolean | Whether supplementary files exist |
| `full_text_url` | `resultList.result[].fullTextUrlList` | Array[Object] | URLs to full text (PMC, publisher) |
| `has_data_links` | `resultList.result[].hasData` | Boolean | Whether data availability statements/links exist |

---

### 3.9 Lens.org (`article_source_lens`)

**Lookup key:** DOI, PMID, or Lens ID
**API endpoint:** `POST https://api.lens.org/scholarly/search` (JSON body with query)

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `lens_id` | `data[].lens_id` | String | Lens identifier |
| `patent_citation_count` | `data[].scholarly_citations_count` (from patent corpus) | Integer | Number of patents citing this work |
| `patent_citations` | Via patent search cross-reference | Array[Object] | Patent IDs, jurisdictions, applicants citing this work |
| `clinical_trial_links` | `data[].fields_of_study[]` + cross-reference | Array | Linked clinical trial references |
| `source_urls` | `data[].source_urls[]` | Array[Object] | Multiple access URLs with types |

---

### 3.10 PlumX Metrics (`article_source_plumx`)

**Lookup key:** DOI or PMID
**Endpoint:** Via Elsevier Developer Portal (institutional access required)

| Field | Type | Description |
|-------|------|-------------|
| `plumx_citations` | Integer | Citation count (PlumX's aggregation) |
| `plumx_usage_abstract_views` | Integer | Abstract views |
| `plumx_usage_full_text_views` | Integer | Full text views |
| `plumx_usage_link_outs` | Integer | Click-throughs to full text |
| `plumx_captures_mendeley_readers` | Integer | Mendeley reader count |
| `plumx_captures_exports_saves` | Integer | Export/save count |
| `plumx_mentions_blog_count` | Integer | Blog mentions |
| `plumx_mentions_news_count` | Integer | News mentions |
| `plumx_mentions_comment_count` | Integer | Comments on article |
| `plumx_social_tweets` | Integer | Tweet count |
| `plumx_social_facebook` | Integer | Facebook interactions |
| `plumx_social_reddit` | Integer | Reddit mentions |

---

### 3.11 Overton (`article_source_overton`)

**Lookup key:** DOI
**Endpoint:** Overton API (institutional subscription required)

| Field | Type | Description |
|-------|------|-------------|
| `overton_policy_citation_count` | Integer | Number of policy documents citing this article |
| `overton_citing_policy_docs` | Array[Object] | Policy documents: title, organisation, country, date, document type |
| `overton_policy_sources` | Array[String] | Types of policy sources (parliamentary, government, think tank, IGO) |
| `overton_countries` | Array[String] | Countries where this research influenced policy |
| `overton_sdgs` | Array[Object] | SDG relevance derived from policy context |

---

### 3.12 PubPeer (`article_source_pubpeer`)

**Lookup key:** DOI
**API endpoint:** `GET https://pubpeer.com/api/v1/publications?doi={doi}` (API key required)

| Field | Type | Description |
|-------|------|-------------|
| `has_pubpeer_comments` | Boolean | Whether any PubPeer comments exist |
| `pubpeer_comment_count` | Integer | Number of comments |
| `pubpeer_url` | String | URL to PubPeer discussion page |
| `pubpeer_first_comment_date` | Date | When first commented |
| `pubpeer_last_comment_date` | Date | Most recent comment |

---

### 3.13 Altmetric.com (`article_altmetrics`)

**Lookup key:** DOI, PMID, or Altmetric ID
**API endpoint:** `GET https://api.altmetric.com/v1/doi/{doi}` (free Details Page API)

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `altmetric_id` | `altmetric_id` | Integer | Altmetric record ID |
| `altmetric_score` | `score` | Float | Overall Altmetric Attention Score |
| `altmetric_score_context_journal` | `context.journal` | Object | Score percentile within same journal |
| `altmetric_score_context_all` | `context.all` | Object | Score percentile across all outputs |
| `altmetric_score_context_age` | `context.similar_age_3m` | Object | Score percentile among outputs of similar age |
| `altmetric_details_url` | `details_url` | String | URL to Altmetric details page |
| `altmetric_image_url` | `images.small` / `medium` / `large` | String | Altmetric donut badge image URLs |
| `cited_by_tweeters_count` | `cited_by_tweeters_count` | Integer | Number of X/Twitter accounts mentioning |
| `cited_by_feeds_count` | `cited_by_feeds_count` | Integer | Blog mentions |
| `cited_by_fbwalls_count` | `cited_by_fbwalls_count` | Integer | Facebook mentions |
| `cited_by_rdts_count` | `cited_by_rdts_count` | Integer | Reddit mentions |
| `cited_by_wikipedia_count` | `cited_by_wikipedia_count` | Integer | Wikipedia citations |
| `cited_by_msm_count` | `cited_by_msm_count` | Integer | Mainstream media mentions |
| `cited_by_policies_count` | `cited_by_policies_count` | Integer | Policy document citations |
| `cited_by_patents_count` | `cited_by_patents_count` | Integer | Patent citations |
| `cited_by_posts_count` | `cited_by_posts_count` | Integer | Total post count |
| `readers_mendeley` | `readers.mendeley` | Integer | Mendeley reader count |
| `readers_citeulike` | `readers.citeulike` | Integer | CiteULike saves |
| `last_updated` | `last_updated` | Integer | Unix timestamp of last update |

---

### 3.14 Scite.ai (`article_citation_context`)

**Lookup key:** DOI
**API endpoint:** `GET https://api.scite.ai/papers/{doi}`

| Field | Type | Description |
|-------|------|-------------|
| `scite_supporting_count` | Integer | Number of citations that support this paper's claims |
| `scite_contrasting_count` | Integer | Number of citations that contrast/contradict this paper |
| `scite_mentioning_count` | Integer | Number of citations that mention without supporting/contrasting |
| `scite_total_citations` | Integer | Total citations analysed by Scite |
| `scite_url` | String | Link to Scite details page |

---

### 3.15 Supplementary Materials (`article_supplementary_materials`)

**Source:** Journal website scrape
**Triggered:** On initial discovery only (supplements don't change after publication)

| Field | Type | Description |
|-------|------|-------------|
| `has_supplementary` | Boolean | Whether supplementary materials exist |
| `supplementary_urls` | Array[String] | URLs to supplementary files |
| `supplementary_types` | Array[String] | File types (PDF, Excel, R code, dataset, appendix, protocol) |
| `supplementary_descriptions` | Array[String] | What each supplement contains |

---

### 3.16 Retraction / Correction Status (`article_retraction_status`)

**Sources:** CrossRef (`update-to` field), OpenAlex (`is_retracted`), Retraction Watch database

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `is_retracted` | Boolean | CrossRef, OpenAlex, Retraction Watch | Whether the article has been retracted |
| `retraction_date` | Date | CrossRef / Retraction Watch | When retracted |
| `retraction_reason` | String | Retraction Watch | Reason for retraction |
| `retraction_notice_doi` | String | CrossRef | DOI of the retraction notice |
| `has_correction` | Boolean | CrossRef (`update-to`) | Whether corrections exist |
| `correction_doi` | String | CrossRef | DOI of the correction |
| `has_expression_of_concern` | Boolean | CrossRef / Retraction Watch | Whether an expression of concern exists |

---

### 3.17 Discovery Record (`article_source_discovery`)

**Origin:** Manus AI agent, manual curation, or web scrape

| Field | Type | Description |
|-------|------|-------------|
| `discovered_url` | String | The URL where this article was found |
| `discovered_at` | DateTime | When it was discovered |
| `discovered_by` | String | Agent name, "manual", or spider name |
| `discovery_source_name` | String | Name of the source website/database |
| `discovery_source_url` | String | URL of the page where the link was found |
| `discovery_context` | Text | Context/description from the discovery source |
| `agent_assigned_type` | String | Resource type assigned by the discovery agent (from 46-type list) |
| `agent_description` | Text | Description written by the discovery agent |
| `agent_methodology_relevance` | Text | Agent's assessment of methodology relevance |
| `agent_access_type` | String | free, freemium, paid, subscription, institutional |

---

### 3.18 AI Assessment Record (`article_ai_assessment`)

**Origin:** Z.AI / Ollama quality assessment pipeline
**Triggered:** On initial discovery, then only when flagged by refresh pipeline

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Overall quality score |
| `quality_dimensions` | Object | Sub-scores: `{authority, currency, relevance, accuracy, pedagogy}` |
| `confidence` | Float (0–1) | AI confidence in its assessment |
| `methodology_tags` | Array[String] | From 162-methodology taxonomy |
| `thesis_stages` | Array[String] | THESIS stage tags (Theory, History, Evaluate, Study, Interpret, Share) |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | Medical specialty relevance |
| `subtype_classification` | String | Assigned subtype (seminal_paper, methodology_review, etc.) |
| `editorial_description` | Text | AI-generated original description (1–2 sentences) |
| `editorial_description_long` | Text | Extended description (3–5 sentences) for detail page |
| `editorial_badges` | Array[String] | Recommended badges (for human review) |
| `assessed_at` | DateTime | When assessed |
| `model_used` | String | Which AI model was used |
| `requires_human_review` | Boolean | Whether confidence is below threshold |

---

## 4. Secondary Entity Links

This type links to the following shared entities (fully defined in `secondary_entity_reference.md`):

### 4.1 Person (Author)

**Relationship:** `article -[AUTHORED_BY {position, is_corresponding}]-> person`
**Cardinality:** Many-to-many (one article has many authors; one person authors many articles)
**Resolution:** Match authors from article source data to Person entity via (1) ORCID exact match, (2) family name + first initial + position, (3) family name + affiliation fuzzy match.
**Entity data sources:** ORCID, OpenAlex Authors, S2 Authors, Google Scholar (scrape), institutional page (scrape)
**Article-specific author fields stored on the relationship (not on the Person entity):**
- `position`: first, middle, last (from OpenAlex) or first/additional (from CrossRef)
- `is_corresponding`: Boolean (from OpenAlex)
- `affiliation_at_publication`: String (the affiliation at time of this article, from PubMed)

### 4.2 Journal

**Relationship:** `article -[PUBLISHED_IN]-> journal`
**Cardinality:** Many-to-one (many articles in one journal)
**Resolution:** Match via ISSN (from CrossRef or PubMed)
**Entity data sources:** OpenAlex Sources, CrossRef Journals, DOAJ, Sherpa Romeo, Scopus (institutional)

### 4.3 Institution

**Relationship:** `article -[AFFILIATED_WITH]-> institution` (via author affiliations)
**Cardinality:** Many-to-many (one article has authors from many institutions)
**Resolution:** Match via ROR ID (from OpenAlex author affiliations)
**Entity data sources:** ROR, OpenAlex Institutions

### 4.4 Funder

**Relationship:** `article -[FUNDED_BY {grant_id}]-> funder`
**Cardinality:** Many-to-many
**Resolution:** Match via CrossRef funder DOI or OpenAlex funder ID
**Entity data sources:** CrossRef Funder Registry, OpenAlex Funders

---

## 5. Golden Record Merge Rules

### 5.1 Field Categories

| Category | Code | Description | Example |
|----------|------|-------------|---------|
| **Verbatim with priority** | `V` | Copied directly from the highest-priority source that has a non-null value | `title`, `doi`, `journal_name` |
| **Verbatim + max** | `V+max` | Store both priority value (with source) AND max value across sources (with source) | `citation_count` |
| **Derived / computed** | `D` | Calculated from source data using deterministic logic | `publication_year`, `is_seminal`, `is_open_access` |
| **LLM-authored** | `L` | Requires AI generation; cannot be assembled mechanically | `editorial_description`, `methodology_tags` |

### 5.2 Identifiers

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `doi` | String | V | CrossRef → PubMed → OpenAlex → S2 → Dimensions → Lens → Discovery | First non-null. Normalise to lowercase, strip `https://doi.org/` prefix. |
| `pmid` | String | V | PubMed → OpenAlex → S2 → iCite | First non-null. |
| `pmcid` | String | V | PubMed → OpenAlex → S2 | First non-null. |
| `openalex_id` | String | V | OpenAlex | Single source. |
| `semantic_scholar_id` | String | V | S2 | Single source. |
| `dimensions_id` | String | V | Dimensions | Single source. |
| `lens_id` | String | V | Lens | Single source. |
| `url` | String | D | Derived | `https://doi.org/{doi}` if DOI exists; else `https://pubmed.ncbi.nlm.nih.gov/{pmid}`; else Discovery URL. |

### 5.3 Bibliographic Core

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `title` | String | V | PubMed → CrossRef → OpenAlex → S2 → Discovery | First non-null. Trim whitespace. Strip trailing period (PubMed convention). |
| `abstract` | Text | V | PubMed → S2 → CrossRef → OpenAlex | **PubMed:** Preserve structured section labels. **S2:** Use as-is (clean plain text). **CrossRef:** Strip JATS XML tags. **OpenAlex:** Reconstruct from inverted index. |
| `abstract_plain` | Text | D | Derived from `abstract` | Strip all section labels and markup for embedding generation. |
| `journal_name` | String | V | PubMed → CrossRef → OpenAlex → Dimensions | First non-null. Use full journal title. |
| `journal_abbreviation` | String | V | PubMed → CrossRef | First non-null. ISO abbreviation. |
| `volume` | String | V | CrossRef → PubMed → S2 | First non-null. |
| `issue` | String | V | CrossRef → PubMed | First non-null. |
| `pages` | String | V | CrossRef → PubMed → S2 | First non-null. Normalise to `start-end` format. |
| `article_number` | String | V | CrossRef | Single source. |
| `publisher` | String | V | CrossRef → OpenAlex | First non-null. |
| `language` | String | V | PubMed → CrossRef → OpenAlex | First non-null. Normalise to ISO 639-1 two-letter code. |
| `publication_date` | Date | D | Derived | CrossRef `published-print` → CrossRef `published-online` → PubMed `PubDate` → OpenAlex → S2. Normalise to ISO 8601. |
| `publication_date_precision` | String | D | Derived | `day`, `month`, or `year`. |
| `publication_year` | Integer | D | Derived from `publication_date` | |

### 5.4 Authors

| Golden Record Field | Type | Cat | Merge Rule |
|-------------------|------|-----|------------|
| `authors` | Array[Object] | D | Start with PubMed author list. Match to CrossRef (name + position), OpenAlex (ORCID or name + affiliation), S2 (name). Assemble richest composite per author. |
| `author_count` | Integer | D | Count of `authors` array. |

**Per-author composite:**

| Author Field | Priority Source | Fallback | Notes |
|-------------|---------------|----------|-------|
| `given_name` | PubMed (`ForeName`) | CrossRef (`given`) → OpenAlex split | |
| `family_name` | PubMed (`LastName`) | CrossRef (`family`) → OpenAlex split | |
| `display_name` | D: Derived | `{given_name} {family_name}` | |
| `orcid` | CrossRef (if `authenticated-orcid`) | OpenAlex → PubMed | Authenticated ORCIDs highest trust |
| `affiliation_raw` | PubMed | CrossRef | Richest raw strings |
| `affiliation_structured` | OpenAlex (`institutions[]`) | — | ROR-linked, structured |
| `position` | OpenAlex (first/middle/last) | CrossRef (first/additional) | |
| `is_corresponding` | OpenAlex | — | |
| `person_entity_id` | D: Entity resolution | — | Link to Person entity |

**Author matching across sources:** (1) ORCID exact match, (2) family name + first initial + position, (3) family name + affiliation similarity.

### 5.5 Classification & Typing

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `article_type_raw` | Object | D | Store all | `{pubmed, crossref, openalex, s2, icite}` — input for AI classification |
| `article_subtype` | String | L | AI Assessment | seminal_paper, methodology_review, etc. |
| `mesh_terms` | Array[Object] | V | PubMed | Single source. Preserve major topic flags and qualifiers. |
| `keywords_author` | Array[String] | V | PubMed → OpenAlex | Deduplicate (case-insensitive). |
| `topics_openalex` | Array[Object] | V | OpenAlex | Store as-is. |
| `fields_of_study` | Array[String] | V | S2 → OpenAlex | Broad field classification. |
| `publication_types_pubmed` | Array[String] | V | PubMed | Most granular typing. |
| `research_categories_dimensions` | Array[Object] | V | Dimensions | ANZSRC Fields of Research. |
| `methodology_tags` | Array[String] | L | AI Assessment | 162-methodology taxonomy. |
| `thesis_stages` | Array[String] | L | AI Assessment | THESIS stage tags. |
| `difficulty_level` | String | L | AI Assessment | beginner, intermediate, advanced. |
| `specialty_tags` | Array[String] | L | AI Assessment | Medical specialty relevance. |

### 5.6 Citation Metrics

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `citation_count` | Integer | V | OpenAlex `cited_by_count` | Priority source. Store with `citation_count_source: "openalex"`. |
| `citation_count_max` | Integer | D | max(CrossRef, OpenAlex, S2, Dimensions, iCite, Lens) | Store with `citation_count_max_source`. |
| `citation_count_max_source` | String | D | Whichever provided max | |
| `influential_citation_count` | Integer | V | S2 | Single source. |
| `citation_percentile` | Object | V | OpenAlex | Min/max percentile within year+subfield. |
| `fwci` | Float | V | OpenAlex | Field-weighted citation impact. |
| `citations_by_year` | Array[Object] | V | OpenAlex | Annual breakdown (last 10 years). |
| `reference_count` | Integer | V | CrossRef → S2 | |
| `reference_dois` | Array[String] | V | CrossRef `reference[].DOI` | Filter to non-null DOIs. |
| `related_work_ids` | Array[String] | V | OpenAlex `related_works` | |
| `citing_works_sample` | Array[Object] | V | S2 `citations` (limited) | With `isInfluential` flag. |

### 5.7 Clinical Translation Metrics

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `relative_citation_ratio` | Float | V | iCite (authoritative) → Dimensions (fallback) | iCite is the original source. |
| `nih_percentile` | Float | V | iCite | Single source. |
| `apt_score` | Float | V | iCite | Approximate Potential to Translate (0–1). |
| `is_clinical` | Boolean | V | iCite | Whether classified as clinical research. |
| `translation_spectrum` | Object | V | iCite `{x_coord, y_coord}` | Position on basic→clinical→applied. |
| `rcr_provisional` | Boolean | V | iCite `provisional` | Whether RCR is provisional (< 2 years). |

### 5.8 Cross-System Linkage

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `linked_clinical_trials` | Array[String] | D | Dimensions → Europe PMC → CrossRef `clinical-trial-number` | ClinicalTrials.gov IDs; deduplicate. |
| `patent_citation_count` | Integer | V+max | Dimensions (priority), Lens (max) | Store both with sources. |
| `patent_citation_count_max` | Integer | D | max(Dimensions, Lens, Altmetric `cited_by_patents_count`) | |
| `patent_citation_count_max_source` | String | D | Whichever provided max | |
| `patent_citations_detail` | Array[Object] | V | Lens | Patent ID, jurisdiction, applicant. |
| `policy_citation_count` | Integer | V | Overton (richest) → Dimensions (count only) → Altmetric `cited_by_policies_count` | |
| `policy_documents` | Array[Object] | V | Overton | Title, org, country, date. |
| `sdg_alignment` | Array[Object] | V | Dimensions → Overton | |
| `linked_grants_extended` | Array[Object] | D | Merge Europe PMC grants + Dimensions grants + CrossRef funders + PubMed grants | Deduplicate by grant ID. |

### 5.9 Text-Mined Annotations

| Golden Record Field | Type | Cat | Source | Merge Rule |
|-------------------|------|-----|--------|------------|
| `text_mined_genes` | Array[String] | V | Europe PMC annotations | Single source. |
| `text_mined_diseases` | Array[String] | V | Europe PMC annotations | Single source. |
| `text_mined_chemicals` | Array[String] | V | Europe PMC annotations | Single source. |
| `text_mined_organisms` | Array[String] | V | Europe PMC annotations | Single source. |
| `has_text_mined_entities` | Boolean | D | Derived | `true` if any text-mined arrays are non-empty. |

### 5.10 Open Access & Full Text

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `is_open_access` | Boolean | D | Derived | `true` if ANY source reports OA. |
| `oa_status` | String | V | Unpaywall → OpenAlex | gold, green, hybrid, bronze, diamond, closed. |
| `best_oa_url` | String | D | Derived | (1) Unpaywall PDF, (2) Unpaywall landing, (3) OpenAlex PDF, (4) OpenAlex landing, (5) S2 PDF, (6) PMC URL. First that returns HTTP 200. |
| `best_oa_url_type` | String | D | Derived | `pdf` or `landing_page`. |
| `license` | String | V | Unpaywall → CrossRef → OpenAlex | Normalise to CC-BY etc. |
| `oa_version` | String | V | Unpaywall | publishedVersion, acceptedVersion, submittedVersion. |
| `publisher_url` | String | V | CrossRef `resource.primary.URL` → OpenAlex | Publisher landing page. |
| `pmc_url` | String | D | Derived | `https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/` if pmcid exists. |
| `journal_is_in_doaj` | Boolean | V | Unpaywall → DOAJ lookup | |

### 5.11 Attention & Impact Metrics

| Golden Record Field | Type | Cat | Source | Merge Rule |
|-------------------|------|-----|--------|------------|
| `altmetric_score` | Float | V | Altmetric.com | Direct from API. |
| `altmetric_score_context` | Object | V | Altmetric.com | Percentile within journal and similar age. |
| `altmetric_donut_url` | String | V | Altmetric.com `images.medium` | Embeddable badge. |
| `altmetric_details_url` | String | V | Altmetric.com | Link to details page. |
| `altmetric_breakdown` | Object | V | Altmetric.com | `{twitter, news, blogs, policy, wikipedia, reddit, facebook, mendeley_readers}`. |
| `scite_supporting` | Integer | V | Scite.ai | Supporting citation count. |
| `scite_contrasting` | Integer | V | Scite.ai | Contrasting citation count. |
| `scite_mentioning` | Integer | V | Scite.ai | Mentioning citation count. |
| `scite_url` | String | V | Scite.ai | Link to details page. |

### 5.12 Usage Metrics

| Golden Record Field | Type | Cat | Source | Merge Rule |
|-------------------|------|-----|--------|------------|
| `abstract_views` | Integer | V | PlumX | Single source (if available). |
| `full_text_views` | Integer | V | PlumX | Single source (if available). |
| `mendeley_readers` | Integer | V+max | Altmetric (priority), PlumX (max) | Store both. |
| `mendeley_readers_max_source` | String | D | Whichever provided max | |

### 5.13 Supplementary Materials

| Golden Record Field | Type | Cat | Source | Merge Rule |
|-------------------|------|-----|--------|------------|
| `has_supplementary` | Boolean | D | Journal scrape OR Europe PMC `hasSuppl` | `true` if either source confirms. |
| `supplementary_files` | Array[Object] | V | Journal website scrape | Each: `{url, file_type, description, size}`. |
| `has_code` | Boolean | D | Derived from `supplementary_files` | `true` if R/Python/Stata/SPSS syntax or GitHub link. |
| `has_data` | Boolean | D | Derived from `supplementary_files` OR Europe PMC `hasData` | `true` if dataset file or data availability statement. |
| `has_protocol` | Boolean | D | Derived from `supplementary_files` | `true` if labelled as protocol. |

### 5.14 Retraction & Integrity

Safety-critical — merge logic is deliberately aggressive.

| Golden Record Field | Type | Cat | Merge Rule |
|-------------------|------|-----|------------|
| `is_retracted` | Boolean | D | `true` if ANY source flags: CrossRef `update-to` type "retraction", OR OpenAlex `is_retracted`, OR Retraction Watch match. **Never auto-resolve to false.** |
| `retraction_date` | Date | V | CrossRef → Retraction Watch. Earliest available. |
| `retraction_notice_doi` | String | V | CrossRef `update-to[].DOI` where type = retraction. |
| `retraction_reason` | String | V | Retraction Watch. Only source with categorised reasons. |
| `has_correction` | Boolean | D | `true` if CrossRef `update-to` contains type "correction". |
| `correction_doi` | String | V | CrossRef. |
| `has_expression_of_concern` | Boolean | D | `true` if CrossRef or Retraction Watch flags. |
| `has_pubpeer_comments` | Boolean | V | PubPeer. |
| `pubpeer_comment_count` | Integer | V | PubPeer. |
| `pubpeer_url` | String | V | PubPeer. |
| `integrity_flags` | Array[String] | D | Aggregate: retraction, expression of concern, correction, PubPeer comments. Enables single "integrity status" display. |

### 5.15 Funding

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `funders` | Array[Object] | D | Merge Europe PMC + Dimensions + CrossRef + PubMed | Match on funder name, deduplicate. Each: `{name, funder_doi, award_numbers[], country, funder_entity_id}`. |

### 5.16 Preprint Tracking (applies to `preprint` subtype)

| Golden Record Field | Type | Cat | Source Priority | Merge Rule |
|-------------------|------|-----|----------------|------------|
| `preprint_server` | String | D | Derived from URL | bioRxiv, medRxiv, SSRN, etc. |
| `preprint_posted_date` | Date | V | bioRxiv/medRxiv API → Europe PMC | |
| `published_version_doi` | String | V | Europe PMC → OpenAlex → bioRxiv API | First non-null. |
| `preprint_version_count` | Integer | V | bioRxiv/medRxiv API | |
| `current_version` | Integer | V | bioRxiv/medRxiv API | |

### 5.17 LLM-Authored Fields

| Golden Record Field | Type | Cat | Input Sources | Generation Notes |
|-------------------|------|-----|--------------|-----------------|
| `editorial_description` | Text (1–2 sentences) | L | Title, abstract, journal, methodology tags, subtype | Original. Never copy abstract. Written for medical trainee audience. |
| `editorial_description_long` | Text (3–5 sentences) | L | All source data | Extended description for registered users. |
| `methodology_tags` | Array[String] | L | Title, abstract, MeSH, PubMed pub types, OpenAlex topics | From 162-methodology taxonomy. |
| `thesis_stages` | Array[String] | L | Content analysis + subtype | THESIS stage tags. |
| `difficulty_level` | String | L | Journal prestige, abstract complexity | beginner, intermediate, advanced. |
| `specialty_tags` | Array[String] | L | MeSH terms, abstract, journal scope | Medical specialty relevance. |
| `article_subtype` | String | L | PubMed pub types, citation count, content analysis | CoThesis subtype assignment. |
| `editorial_badges` | Array[String] | L | Quality score, citations, OA, difficulty, subtype | Max 3. AI recommends, human confirms. |
| `quality_score` | Float (0–1) | L | All source data | Multi-dimensional: authority, currency, relevance, accuracy, pedagogy. |
| `quality_dimensions` | Object | L | All source data | `{authority, currency, relevance, accuracy, pedagogy}` — each 0–1. |
| `is_seminal` | Boolean | D | Citation count + AI assessment | `citation_count_max > methodology threshold AND subtype == "seminal_paper"`. |

### 5.18 Entity Links

| Golden Record Field | Type | Cat | Merge Rule |
|-------------------|------|-----|------------|
| `author_entity_ids` | Array[String] | D | Entity resolution: ORCID → name+institution fuzzy match. |
| `journal_entity_id` | String | D | ISSN match to Journal entity. |
| `institution_entity_ids` | Array[String] | D | Unique institutions from author affiliations, matched via ROR. |
| `funder_entity_ids` | Array[String] | D | Via CrossRef funder DOI or OpenAlex funder ID. |

### 5.19 Subtype-Specific Fields

| Field | Applies To | Source | Description |
|-------|-----------|--------|-------------|
| `seminal_status_evidence` | `seminal_paper` | AI Assessment + S2 citations | Why seminal. |
| `methodologies_compared` | `methodology_comparison` | AI Assessment | Which methodologies. |
| `comparison_recommendation` | `methodology_comparison` | AI Assessment | Conclusion. |
| `exemplar_methodology` | `exemplar_study` | AI Assessment | Which methodology exemplified. |
| `exemplar_quality_notes` | `exemplar_study` | AI Assessment | What makes it a good example. |
| `guideline_body` | `guideline_article` | Discovery / Scrape | Issuing organisation. |
| `preprint_server` | `preprint` | Derived from URL | bioRxiv, medRxiv, SSRN. |
| `preprint_published_doi` | `preprint` | Europe PMC / OpenAlex | DOI of published version. |

---

## 6. Field Provenance Record

Every golden record carries a `field_provenance` JSON:

```json
{
  "title": {"source": "pubmed", "timestamp": "2026-04-09T12:00:00Z"},
  "doi": {"source": "crossref", "timestamp": "2026-04-09T12:00:00Z"},
  "citation_count": {"source": "openalex", "timestamp": "2026-04-09T12:00:00Z"},
  "citation_count_max": {"source": "semantic_scholar", "value": 15420, "timestamp": "2026-04-09T12:00:00Z"},
  "relative_citation_ratio": {"source": "nih_icite", "timestamp": "2026-04-09T12:00:00Z"},
  "is_open_access": {"derived_from": ["unpaywall", "openalex"], "timestamp": "2026-04-09T12:00:00Z"},
  "editorial_description": {"source": "ai_assessment", "model": "glm-4-flash", "timestamp": "2026-04-01T08:00:00Z"},
  "methodology_tags": {"source": "ai_assessment", "model": "glm-4-flash", "timestamp": "2026-04-01T08:00:00Z"}
}
```

---

## 7. Golden Record Versioning

```json
{
  "golden_record_version": "2026-04-09T12:00:00Z",
  "golden_record_hash": "sha256:abc123...",
  "previous_hash": "sha256:def456...",
  "rebuild_reason": "openalex_citation_count_changed",
  "source_sub_record_versions": {
    "crossref": "2026-04-08T10:00:00Z",
    "pubmed": "2026-04-07T14:00:00Z",
    "openalex": "2026-04-09T11:30:00Z",
    "semantic_scholar": "2026-04-05T09:00:00Z",
    "unpaywall": "2026-04-06T16:00:00Z",
    "nih_icite": "2026-04-09T12:00:00Z",
    "dimensions": "2026-04-03T08:00:00Z",
    "europe_pmc": "2026-04-04T10:00:00Z",
    "lens": null,
    "plumx": null,
    "overton": null,
    "pubpeer": "2026-04-09T12:00:00Z",
    "altmetric": "2026-04-09T12:00:00Z",
    "scite": "2026-04-03T08:00:00Z",
    "ai_assessment": "2026-04-01T08:00:00Z"
  }
}
```

Hash computed over all golden record field values (excluding provenance/timestamps). Rebuild producing same hash = no-op.

---

## 8. Refresh Tiers

| Tier | Articles | Frequency | Sources Refreshed |
|------|----------|-----------|-------------------|
| **Hot** | < 6 months old, OR altmetric > 50, OR flagged | Weekly | All T1 + Altmetric + Scite + iCite + PubPeer + link check |
| **Warm** | 6 months – 3 years, OR citation > 100 | Monthly | OpenAlex, Unpaywall, Altmetric, iCite, link check |
| **Cold** | > 3 years, citation < 100 | Quarterly | OpenAlex, link check, retraction check, PubPeer check |
| **Archive** | > 10 years, citation < 20, not badged | Biannually | Link check, retraction check only |
| **On-demand** | Featured/badged articles | When flagged | Dimensions, Europe PMC, Lens, Overton, PlumX — full enrichment |

---

## 9. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| Altmetric scores | Altmetric.com | Changes rapidly for new articles, stabilises over time |
| Citation counts | OpenAlex, iCite | Accumulate gradually; monthly is sufficient |
| Retraction status | CrossRef, OpenAlex, Retraction Watch | Safety-critical — check weekly for Hot tier |
| PubPeer comments | PubPeer | Integrity signal — check weekly for Hot tier |
| OA status | Unpaywall | May change when embargo lifts or green version deposited |
| Text-mined entities | Europe PMC | Stable after initial mining; re-check annually |
| Policy citations | Overton | Accumulate slowly; quarterly sufficient |
| Patent citations | Dimensions, Lens | Accumulate slowly; quarterly sufficient |
| Supplementary materials | Journal scrape | Don't change after publication; one-time capture |

---

## 10. Field Summary

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim with priority (V) | ~53 | title, abstract, doi, pmid, journal_name, mesh_terms, altmetric_score, rcr |
| Verbatim + max (V+max) | ~4 | citation_count, patent_citation_count, mendeley_readers |
| Derived / computed (D) | ~28 | url, publication_year, is_open_access, is_retracted, has_code, entity IDs, integrity_flags |
| LLM-authored (L) | ~12 | editorial_description, methodology_tags, thesis_stages, quality_score, badges |
| **Total golden record fields** | **~93** | |
| **Source sub-records** | **18** | 13 enrichment APIs + Altmetric + Scite + supplementary scrape + retraction + discovery + AI assessment |

---

## 11. Source Coverage Heatmap

| Field Category | CR | PM | OA | S2 | UW | iCite | Dim | EPMC | Lens | AltM | Overt | PlumX | PubP | Scite |
|---------------|----|----|----|----|----|----|----|----|------|------|-------|-------|------|------|
| **Identifiers** | ●●● | ●●○ | ●●● | ●●○ | ●○○ | ●○○ | ●●○ | ●●○ | ●●○ | — | — | — | — | — |
| **Bibliographic** | ●●● | ●●● | ●●○ | ●●○ | ●○○ | — | ●○○ | ●●○ | ●○○ | — | — | — | — | — |
| **Authors** | ●●○ | ●●● | ●●● | ●○○ | — | — | ●○○ | ●○○ | — | — | — | — | — | — |
| **Classification** | ●○○ | ●●● | ●●● | ●●○ | — | ●○○ | ●●○ | ●●● | — | — | — | — | — | — |
| **Citations** | ●○○ | — | ●●● | ●●● | — | ●●● | ●●● | ●○○ | ●○○ | — | — | ●○○ | — | — |
| **Clinical translation** | — | — | — | — | — | ●●● | ●○○ | — | — | — | — | — | — | — |
| **Cross-system links** | ●○○ | — | — | — | — | — | ●●● | ●●○ | ●●● | — | ●●● | — | — | — |
| **Text-mined entities** | — | — | — | — | — | — | — | ●●● | — | — | — | — | — | — |
| **Open Access** | ●○○ | ●○○ | ●●○ | ●○○ | ●●● | — | ●○○ | ●○○ | ●○○ | — | — | — | — | — |
| **Attention/Social** | — | — | — | — | — | — | ●○○ | — | — | ●●● | — | ●●● | — | — |
| **Citation context** | — | — | — | — | — | — | — | — | — | — | — | — | — | ●●● |
| **Policy impact** | — | — | — | — | — | — | ●●○ | — | — | ●○○ | ●●● | — | — | — |
| **Usage/engagement** | — | — | — | — | — | — | — | — | — | ●○○ | — | ●●● | — | — |
| **Integrity** | ●●○ | — | ●○○ | — | — | — | — | — | — | — | — | — | ●●● | — |
| **Funding** | ●●● | ●●○ | ●●○ | — | — | — | ●●● | ●●● | — | — | — | — | — | — |

CR=CrossRef, PM=PubMed, OA=OpenAlex, S2=Semantic Scholar, UW=Unpaywall, Dim=Dimensions, EPMC=Europe PMC, AltM=Altmetric, Overt=Overton, PubP=PubPeer

● = partial coverage, ●● = good coverage, ●●● = best/most complete source for this category
