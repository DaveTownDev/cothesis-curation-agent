# CoThesis Compendium — Complete Field Mapping & Merge Logic: `funding`

**Type:** Funding & Grants
**Version:** 1.0
**Date:** April 2026

**Subtypes:** `government_national_grant`, `college_professional_body_grant`, `university_hospital_internal_grant`, `research_fellowship_scholarship`

**Note:** This type is unique because the Funder entity is the primary relationship, not secondary. A grant listing links TO a Funder entity, which itself has data from CrossRef Funder Registry and OpenAlex Funders. The Dimensions Grants API is the standout source — it uniquely links historical grants to the publications that resulted from them.

---

## 1. Architecture

```
funding_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── funding_source_dimensions_grants (API)
  │     ├── funding_source_nih_reporter (API)
  │     ├── funding_source_grantconnect (scrape — Australian)
  │     ├── funding_source_ukri_gtr (API — UK)
  │     ├── funding_source_cordis (API/download — EU)
  │     ├── funding_source_grants_gov (API — US federal)
  │     ├── funding_source_europe_pmc_grants (API)
  │     ├── funding_source_scrape (funder website — NHMRC, MRFF, Wellcome, MRC, colleges, universities)
  │     ├── funding_source_discovery
  │     └── funding_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── funder_entity_id (the funding body — primary relationship)
  │     ├── institution_entity_id (for university/hospital internal grants)
  │     └── medical_college_name (for college grants — string field)
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
| 1 | Funder website scrape | `scrape` | T1 | N/A | Free | Authoritative for eligibility, deadlines, amounts, application process |
| 2 | Dimensions Grants API | `dimensions_grants` | T1 | 30 req/min | Free (non-comm) | Largest linked grant database — grants to publications/trials/patents |
| 3 | NIH Reporter | `nih_reporter` | T1 | Standard | Free | US federal biomedical grants — most detailed for NIH |
| 4 | GrantConnect | `grantconnect` | T1 | N/A (scrape) | Free | Australian government grants |
| 5 | UKRI Gateway to Research | `ukri_gtr` | T2 | Standard | Free | All 7 UK Research Councils |
| 6 | EU CORDIS | `cordis` | T2 | Standard | Free | EU framework programme projects |
| 7 | Grants.gov | `grants_gov` | T2 | Standard | Free | US federal discretionary grants |
| 8 | Europe PMC Grants | `epmc_grants` | T2 | Standard | Free | Grant-to-publication links from 26+ funders |
| 9 | CrossRef Funder Registry | `crossref_funders` | T1 | 50 req/sec | Free | Funder identification and DOIs |
| 10 | Discovery | `discovery` | — | N/A | N/A | Agent-provided |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Dimensions Grants API (`funding_source_dimensions_grants`)

**Lookup key:** Funder name + keyword search via DSL
**API endpoint:** `POST https://app.dimensions.ai/api/dsl` with query `search grants for "..." where ...`

| Field | DSL Path | Data Type | Description |
|-------|----------|-----------|-------------|
| `dimensions_grant_id` | `id` | String | Dimensions grant ID |
| `title` | `title` | String | Grant title |
| `abstract` | `abstract` | Text | Grant abstract |
| `funder` | `funder[]` | Array[Object] | `{id, name, country_name, acronym}` |
| `funder_country` | `funder[].country_name` | String | Funder country |
| `funding_amount` | `funding_aud` / `funding_usd` / `funding_eur` / `funding_gbp` | Float | Grant amount in various currencies |
| `funding_currency` | Derived | String | Currency of primary amount |
| `start_date` | `start_date` | Date | Grant start date |
| `end_date` | `end_date` | Date | Grant end date |
| `start_year` | `start_year` | Integer | Start year |
| `end_year` | `end_year` | Integer | End year |
| `researchers` | `researchers[]` | Array[Object] | `{id, first_name, last_name, orcid}` — PI and co-investigators |
| `research_orgs` | `research_orgs[]` | Array[Object] | `{id, name, country_name, types[]}` — recipient institutions |
| `research_org_countries` | `research_org_countries[]` | Array[String] | Countries of recipient institutions |
| `category_for` | `category_for[]` | Array[Object] | ANZSRC Fields of Research classifications |
| `category_hrcs_hc` | `category_hrcs_hc[]` | Array[Object] | HRCS Health Categories |
| `category_hrcs_rac` | `category_hrcs_rac[]` | Array[Object] | HRCS Research Activity Classifications |
| `resulting_publications` | `resulting_publication_ids[]` | Array[String] | Dimensions publication IDs that resulted from this grant |
| `resulting_publication_count` | Derived (count) | Integer | Number of publications from this grant |
| `resulting_clinical_trials` | `clinical_trial_ids[]` | Array[String] | ClinicalTrials.gov IDs linked to this grant |
| `resulting_patents` | `patent_ids[]` | Array[String] | Patents linked to this grant |
| `language` | `language` | String | Language |
| `active` | `active` | Boolean | Whether grant is currently active |

**Unique value:** The `resulting_publications`, `resulting_clinical_trials`, and `resulting_patents` fields are uniquely available from Dimensions. No other source links grants to their downstream outputs.

---

### 3.2 NIH Reporter (`funding_source_nih_reporter`)

**Lookup key:** Project number or keyword search
**API endpoint:** `POST https://api.reporter.nih.gov/v2/projects/search`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `project_number` | `results[].project_num` | String | NIH project number (e.g., R01MH123456) |
| `project_title` | `results[].project_title` | String | Project title |
| `abstract` | `results[].abstract_text` | Text | Abstract |
| `pi_names` | `results[].principal_investigators[]` | Array[Object] | `{profile_id, first_name, last_name, email, is_contact_pi}` |
| `organization` | `results[].organization` | Object | `{org_name, city, state, country, org_duns, org_fips}` |
| `department` | `results[].organization.department_type` | String | Department |
| `funding_mechanism` | `results[].activity_code` | String | R01, R21, K23, F32, etc. |
| `nih_institute` | `results[].agency_ic_admin` | Object | `{code, abbreviation, name}` — which NIH institute |
| `award_amount` | `results[].award_amount` | Float | Award amount for this fiscal year |
| `total_cost` | `results[].total_cost` | Float | Total project cost |
| `project_start_date` | `results[].project_start_date` | Date | Project start |
| `project_end_date` | `results[].project_end_date` | Date | Project end |
| `fiscal_year` | `results[].fiscal_year` | Integer | Fiscal year |
| `is_active` | `results[].is_active` | Boolean | Whether currently active |
| `spending_categories` | `results[].spending_categories` | Object | NIH RCDC spending categories |
| `terms` | `results[].phr_text` | Text | Public health relevance statement |
| `cong_dist` | `results[].cong_dist` | String | Congressional district |
| `publications` | Via separate endpoint | Array[Object] | Linked publications |
| `clinical_studies` | Via separate endpoint | Array | Linked clinical studies |

---

### 3.3 GrantConnect — Australia (`funding_source_grantconnect`)

**Source:** grants.gov.au / grantconnect.gov.au (scrape)

| Field | Type | Description |
|-------|------|-------------|
| `grantconnect_url` | String | Grant opportunity URL |
| `title` | String | Grant program title |
| `description` | Text | Description |
| `funder` | String | Funding body (NHMRC, MRFF, ARC, etc.) |
| `grant_type` | String | Project grant, fellowship, scholarship, etc. |
| `amount_min` | Float | Minimum funding amount |
| `amount_max` | Float | Maximum funding amount |
| `currency` | String | AUD |
| `duration` | String | Grant duration (e.g., "3–5 years") |
| `eligibility` | Text | Eligibility criteria |
| `application_url` | String | Application portal URL |
| `open_date` | Date | Applications open date |
| `close_date` | Date | Applications close date |
| `outcome_date` | Date | Expected outcome announcement |
| `frequency` | String | Annual, biannual, rolling, one-off |
| `career_stage` | Array[String] | ECR, MCR, senior, any |
| `status` | String | open, closed, upcoming |

---

### 3.4 UKRI Gateway to Research (`funding_source_ukri_gtr`)

**Lookup key:** Organisation or keyword search
**API endpoint:** `GET https://gtr.ukri.org/gtr/api/projects?q={query}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `gtr_id` | `project.id` | String | GtR project ID |
| `title` | `project.title` | String | Project title |
| `abstract` | `project.abstractText` | Text | Abstract |
| `fund_start` | `project.fund.start` | Date | Funding start date |
| `fund_end` | `project.fund.end` | Date | Funding end date |
| `funder` | `project.fund.funder.name` | String | Funder name (MRC, EPSRC, etc.) |
| `amount` | `project.fund.valuePounds` | Float | Award amount in GBP |
| `category` | `project.fund.category` | String | Research Grant, Fellowship, Studentship, etc. |
| `pi` | `project.principalInvestigator` | Object | `{firstName, surname, id}` |
| `organisation` | `project.leadResearchOrganisation` | Object | `{name, id}` |
| `status` | `project.status` | String | Active, Closed |
| `research_topics` | `project.researchTopics[]` | Array[Object] | `{id, text, percentage}` |
| `outcomes` | `project.output[]` | Array[Object] | Publications, products, IP, collaborations |

---

### 3.5 EU CORDIS (`funding_source_cordis`)

**Lookup key:** Project ID or keyword search
**Access:** Open data download or API

| Field | Type | Description |
|-------|------|-------------|
| `cordis_project_id` | String | CORDIS project reference number |
| `title` | String | Project title |
| `acronym` | String | Project acronym |
| `abstract` | Text | Project abstract |
| `start_date` | Date | Start date |
| `end_date` | Date | End date |
| `total_cost` | Float | Total project cost (EUR) |
| `eu_contribution` | Float | EU contribution (EUR) |
| `funding_scheme` | String | ERC, MSCA, collaborative, etc. |
| `programme` | String | FP7, Horizon 2020, Horizon Europe |
| `coordinator` | Object | `{name, country}` |
| `participants` | Array[Object] | `{name, country, ec_contribution}` |
| `objective` | Text | Full project objective |
| `status` | String | SIGNED, CLOSED, TERMINATED |
| `topics` | Array[String] | Call topics |
| `publications` | Array[Object] | Linked publications |
| `url` | String | CORDIS project page URL |

---

### 3.6 Grants.gov (`funding_source_grants_gov`)

**Lookup key:** CFDA number or keyword search
**API endpoint:** `GET https://www.grants.gov/grantsws/rest/opportunities/search?keyword={query}`

| Field | Type | Description |
|-------|------|-------------|
| `opportunity_id` | String | Grants.gov opportunity ID |
| `opportunity_number` | String | Funding opportunity number |
| `title` | String | Opportunity title |
| `description` | Text | Description |
| `agency_name` | String | Funding agency (NIH, NSF, CDC, etc.) |
| `cfda_number` | String | CFDA catalogue number |
| `award_ceiling` | Float | Maximum award amount |
| `award_floor` | Float | Minimum award amount |
| `estimated_total_funding` | Float | Total programme funding |
| `expected_awards` | Integer | Number of awards expected |
| `close_date` | Date | Application deadline |
| `open_date` | Date | When opportunity opened |
| `post_date` | Date | Posted date |
| `archive_date` | Date | Archive date |
| `grant_type` | String | Discretionary, formula, etc. |
| `category` | String | Health, science, education, etc. |
| `eligibility` | Text | Eligible applicant types |

---

### 3.7 Europe PMC Grants (`funding_source_epmc_grants`)

**Lookup key:** Grant ID or funder name
**API endpoint:** `GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=GRANT_ID:{id}`

| Field | Type | Description |
|-------|------|-------------|
| `grant_id` | String | Grant identifier |
| `funder_name` | String | Funder name |
| `publication_count` | Integer | Number of publications linked to this grant |
| `publications` | Array[Object] | `{pmid, doi, title}` — publications acknowledging this grant |

---

### 3.8 Funder Website Scrape (`funding_source_scrape`)

**Sources:** NHMRC, MRFF, Wellcome Trust, MRC, medical college websites, university research offices

| Field | Type | Description |
|-------|------|-------------|
| `source_url` | String | Grant information page URL |
| `programme_name` | String | Grant programme name |
| `funder_name` | String | Funding body name |
| `description` | Text | Programme description |
| `amount_min` | Float | Minimum amount |
| `amount_max` | Float | Maximum amount |
| `currency` | String | Currency code |
| `duration` | String | Typical grant duration |
| `eligibility` | Text | Who can apply |
| `career_stage` | Array[String] | Target career stage(s) |
| `application_url` | String | Application portal |
| `application_deadline` | Date | Next deadline |
| `application_frequency` | String | Annual, biannual, rolling |
| `success_rate` | Float | Published success rate (if available) |
| `guidelines_url` | String | Application guidelines document URL |
| `past_recipients_url` | String | URL to list of past awardees |
| `contact_email` | String | Contact email |
| `status` | String | open, closed, upcoming |
| `specific_requirements` | Text | Any specific requirements (ethics, registration, etc.) |
| `methodology_focus` | Array[String] | Any methodology restrictions (clinical trials only, qualitative, etc.) |
| `college_name` | String | For college grants — which medical college |
| `institution_name` | String | For university/hospital internal grants |

---

### 3.9 AI Assessment (`funding_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | |
| `quality_dimensions` | Object | `{relevance, accessibility, amount, prestige, documentation}` |
| `confidence` | Float (0–1) | |
| `methodology_tags` | Array[String] | What methodologies this funding supports |
| `thesis_stages` | Array[String] | Primarily "Study" (funding the research) |
| `difficulty_level` | String | Application difficulty: beginner-friendly, intermediate, competitive |
| `specialty_tags` | Array[String] | |
| `subtype_classification` | String | One of 4 subtypes |
| `editorial_description` | Text | What this funding is for and who should apply |
| `editorial_description_long` | Text | Extended |
| `editorial_badges` | Array[String] | Max 3 |
| `who_should_apply` | Text | Plain-language guidance on ideal applicants |
| `assessed_at` | DateTime | |
| `model_used` | String | |
| `requires_human_review` | Boolean | |

---

## 4. Secondary Entity Links

### 4.1 Funder (Primary Relationship)

**Relationship:** `funding -[PROVIDED_BY]-> funder`
**Cardinality:** Many-to-one (many grants from one funder)
**Resolution:** Funder name → CrossRef Funder Registry (funder DOI) → Funder entity
**Note:** The Funder entity carries its own data (name, country, homepage, works_funded_count) from CrossRef and OpenAlex. The funding resource record carries the grant-specific data (amount, eligibility, deadlines).

### 4.2 Institution (for Internal Grants)

**Relationship:** `funding -[OFFERED_BY]-> institution`
**For:** `university_hospital_internal_grant` subtype
**Resolution:** Institution name → ROR match

### 4.3 Medical College (String Field)

**For:** `college_professional_body_grant` subtype
**Stored as:** String field `college_name` — not a separate entity (medical colleges are few and manually curated)

---

## 5. Golden Record Merge Rules

### 5.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `dimensions_grant_id` | String | V | Dimensions | |
| `nih_project_number` | String | V | NIH Reporter | For NIH grants. |
| `gtr_id` | String | V | UKRI GtR | For UK grants. |
| `cordis_id` | String | V | CORDIS | For EU grants. |
| `grantconnect_url` | String | V | GrantConnect | For Australian grants. |
| `grants_gov_id` | String | V | Grants.gov | For US federal. |
| `url` | String | D | Derived | scrape `source_url` → funder website → GrantConnect → Grants.gov. |

### 5.2 Core Metadata

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `programme_name` | String | V | scrape → Dimensions `title` → NIH Reporter `project_title` → UKRI GtR `title` → CORDIS `title` | |
| `funder_name` | String | V | scrape → Dimensions `funder[0].name` → NIH Reporter `nih_institute` → UKRI GtR `funder` → CORDIS | |
| `funder_entity_id` | String | D | Entity resolution | → Funder entity via CrossRef Funder Registry. |
| `description` | Text | V | scrape → Dimensions `abstract` → NIH Reporter `abstract` → UKRI GtR `abstract` → CORDIS `objective` | |
| `funder_country` | String | V | Dimensions `funder[0].country_name` → scrape → UKRI GtR (UK) → CORDIS (EU) | |

### 5.3 Financial

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `amount_min` | Float | V | scrape → GrantConnect → Grants.gov `award_floor` | |
| `amount_max` | Float | V | scrape → GrantConnect → Grants.gov `award_ceiling` → UKRI GtR `amount` → CORDIS `eu_contribution` | |
| `currency` | String | V | scrape → derived from funder country | AUD, USD, GBP, EUR. |
| `typical_duration` | String | V | scrape → Dimensions (derived from start/end dates) | |
| `total_programme_funding` | Float | V | Grants.gov `estimated_total_funding` → CORDIS `total_cost` | |

### 5.4 Eligibility & Application

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `eligibility` | Text | V | scrape → GrantConnect → Grants.gov | Who can apply. |
| `career_stage` | Array[String] | V | scrape → GrantConnect | ECR, MCR, senior, any. |
| `application_url` | String | V | scrape → GrantConnect → Grants.gov | Where to apply. |
| `guidelines_url` | String | V | scrape | Application guidelines. |
| `application_deadline` | Date | V | scrape → GrantConnect `close_date` → Grants.gov `close_date` | Next deadline. |
| `application_frequency` | String | V | scrape → GrantConnect `frequency` | Annual, biannual, rolling. |
| `success_rate` | Float | V | scrape | Published success rate (null if unavailable). |
| `status` | String | D | Derived | `open` (deadline in future), `closed` (past), `upcoming` (announced but not yet open). |
| `specific_requirements` | Text | V | scrape | Ethics, registration, etc. |
| `methodology_focus` | Array[String] | V | scrape | Any methodology restrictions. |

### 5.5 Outcomes (from Dimensions — Historical Grants)

| Golden Field | Type | Cat | Source | Merge Rule |
|-------------|------|-----|--------|------------|
| `resulting_publication_count` | Integer | V | Dimensions | How many papers resulted from this grant. |
| `resulting_publications` | Array[Object] | V | Dimensions → Europe PMC | `{dimensions_id, doi, title}`. |
| `resulting_clinical_trials` | Array[String] | V | Dimensions → NIH Reporter | ClinicalTrials.gov IDs. |
| `resulting_patents` | Array[String] | V | Dimensions | Patent IDs. |
| `research_categories` | Array[Object] | V | Dimensions `category_for` → UKRI GtR `research_topics` | ANZSRC or RCUK classifications. |

### 5.6 Fellowship-Specific Fields (for research_fellowship_scholarship subtype)

| Golden Field | Type | Cat | Source | Description |
|-------------|------|-----|--------|-------------|
| `fellowship_type` | String | V | scrape | Clinical fellowship, research fellowship, PhD scholarship, postdoc |
| `stipend_amount` | Float | V | scrape | Annual stipend amount |
| `stipend_currency` | String | V | scrape | |
| `includes_research_costs` | Boolean | V | scrape | Whether research/project costs are included |
| `research_cost_amount` | Float | V | scrape | Separate research cost allocation |
| `includes_tuition` | Boolean | V | scrape | Whether tuition fees are covered (PhD) |
| `duration_years` | Float | V | scrape | Duration in years |
| `location_requirements` | String | V | scrape | Location/residency requirements |

### 5.7 LLM-Authored Fields

| Golden Field | Type | Cat | Notes |
|-------------|------|-----|-------|
| `editorial_description` | Text | L | What this funding is for, in plain language. |
| `editorial_description_long` | Text | L | Extended description. |
| `who_should_apply` | Text | L | Guidance on ideal applicants. |
| `methodology_tags` | Array[String] | L | What methodologies this funding supports. |
| `thesis_stages` | Array[String] | L | Primarily "Study". |
| `difficulty_level` | String | L | Application competitiveness: beginner-friendly, intermediate, competitive. |
| `specialty_tags` | Array[String] | L | |
| `editorial_badges` | Array[String] | L | Max 3. |
| `quality_score` | Float (0–1) | L | |
| `quality_dimensions` | Object | L | `{relevance, accessibility, amount, prestige, documentation}` |
| `subtype_classification` | String | L | One of 4 subtypes. |

### 5.8 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `funder_entity_id` | String | D | Funder name → CrossRef Funder Registry → Funder entity. |
| `institution_entity_id` | String | D | For internal grants → Institution via ROR. |
| `college_name` | String | V | For college grants — string field. |

---

## 6. Refresh Tiers

| Tier | Scope | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Open** | Currently open/upcoming funding opportunities | Monthly | Scrape (deadlines, status), GrantConnect, Grants.gov |
| **Recurring** | Annual recurring programmes (closed but will reopen) | Quarterly | Scrape (new round dates, updated guidelines) |
| **Historical** | Past grants with outcome data | Biannually | Dimensions (resulting publications — accumulate over time) |
| **Archive** | One-off grants, completed | Annually | Link check only |

**Key monitoring:** Deadlines are the most time-sensitive data in the entire directory. Monthly scrape of funder websites for deadline changes is essential.

---

## 7. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| Deadlines | Funder website scrape | Most time-sensitive field — monthly check |
| Eligibility changes | Funder website scrape | May change between rounds |
| Success rates | Funder website scrape | Published annually by some funders |
| Resulting publications | Dimensions | Accumulate over grant lifetime and beyond |
| New funding rounds | Funder websites, GrantConnect, Grants.gov | May open at any time |
| Amount changes | Funder website scrape | May change between rounds |
| Status (open/closed) | Derived from deadlines | Automated based on current date vs deadline |

---

## 8. Field Summary

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim (V) | ~30 | programme_name, funder, description, amount, eligibility, career_stage, deadline, success_rate, resulting_publications |
| Derived (D) | ~5 | url, status, funder_entity_id, institution_entity_id |
| LLM-authored (L) | ~10 | editorial_description, who_should_apply, methodology_tags, quality_score |
| **Total funding golden record fields** | **~45** | |

---

## 9. Source Coverage Heatmap

| Field Category | Scrape | Dimensions | NIH Rep | GrntCon | UKRI | CORDIS | Grants.gov | EPMC |
|---------------|--------|-----------|---------|---------|------|--------|-----------|------|
| **Identifiers** | ●○○ | ●●● | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | ●○○ |
| **Core metadata** | ●●● | ●●● | ●●● | ●●○ | ●●○ | ●●○ | ●●○ | — |
| **Financial** | ●●● | ●●○ | ●●● | ●●● | ●●● | ●●● | ●●● | — |
| **Eligibility** | ●●● | — | — | ●●○ | — | — | ●●○ | — |
| **Deadlines** | ●●● | — | — | ●●● | — | — | ●●● | — |
| **Outcomes** | — | ●●● | ●●○ | — | ●●○ | ●○○ | — | ●●● |
| **Research categories** | — | ●●● | ●○○ | — | ●●● | ●○○ | — | — |
| **PI/investigators** | — | ●●● | ●●● | — | ●●○ | ●○○ | — | — |

Scrape=Funder Website, NIH Rep=NIH Reporter, GrntCon=GrantConnect, EPMC=Europe PMC Grants
