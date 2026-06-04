# Entity: ReportingGuideline

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: Authored (new entity — was free-text arrays in Methodology.primary_reporting_standard_codes[] and Resource reporting_guideline subtype)
COMPENDIUM_URL: /library/reporting-guidelines/{slug}
NOTE: Promotes what were free-text string arrays in Methodology into queryable, linkable records with
URLs, version tracking, and extension relationships. A ResourceSubtype.reporting_guideline.canonical.md
also exists in entities/ — that file defines the Resource subtype shape. This file is the normalised
FK target that ReportingGuideline-subtype Resources may reference via `reporting_guideline_code`.

## Purpose
ReportingGuideline is a first-class entity for research reporting standards and checklists.
Examples: CONSORT, STROBE, PRISMA, SQUIRE, CARE, AGREE.

Each guideline record captures the standard's full name, acronym, version, issuing body, canonical URLs,
and linkages to the Methodologies it covers. Extension guidelines (e.g. CONSORT-AI extending CONSORT)
are modelled via a self-referential `extension_codes[]` array.

Cross-references issuing bodies (e.g. EQUATOR Network) via Organisation.code.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. Pattern includes version where stable. e.g. `CONSORT-2010`, `STROBE`, `PRISMA-2020`. Immutable once in production. |
| `name` | string | yes | Full guideline name. e.g. "Consolidated Standards of Reporting Trials" |
| `acronym` | string | yes | Short acronym. e.g. "CONSORT", "PRISMA", "STROBE" |
| `version` | string | null | Version string. e.g. "2010", "2020". Null if versionless. |
| `description` | string | null | 1–3 sentences describing the guideline scope and target study types. |
| `issuing_body_code` | string | null | FK → Organisation.code. e.g. EQUATOR Network. |
| `checklist_url` | string | null | URL to downloadable checklist (PDF or web form). |
| `publication_url` | string | null | URL of the primary reporting guideline publication. |
| `methodology_codes` | string[] | null | FK[] → Methodology.code. Methodologies this guideline covers. Informational — not a constraint. |
| `extension_codes` | string[] | null | FK[] → ReportingGuideline.code. Companion extension guidelines. e.g. CONSORT-AI, CONSORT-SPI. Symmetric — see Bidirectional Integrity. |
| `is_active` | boolean | yes | Whether live in platform. |

---

## Page Mixin Fields

Attached — Reporting guidelines have Compendium pages at /library/reporting-guidelines/{slug}.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name, nullable |
| `has_page` | boolean | Whether Compendium page is generated |
| `is_active` | boolean | Whether entity appears in user-facing surfaces |
| `phase` | integer | Rollout phase (1 = launch) |

---

## Derived Fields

None.

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| ReportingGuideline.issuing_body_code | many→one | Organisation | nullable FK | |
| ReportingGuideline.methodology_codes[] | many→many | Methodology | one-sided array | no reciprocal on Methodology |
| ReportingGuideline.extension_codes[] | many→many | ReportingGuideline (self) | symmetric self-ref | see Bidirectional Integrity |
| ReportingGuideline.code | one→many | Resource (reporting_guideline subtype) | via Resource.reporting_guideline_code | |

---

## Bidirectional Integrity

| Relationship | Rule | Validator |
|---|---|---|
| extension_codes[] | Symmetric — if A lists B in extension_codes[], B must list A | `_merge/validation/reporting_guideline_extensions_symmetry.py` |

---

## Seed Data Examples

| code | acronym | name |
|---|---|---|
| `CONSORT-2010` | CONSORT | Consolidated Standards of Reporting Trials |
| `STROBE` | STROBE | Strengthening the Reporting of Observational Studies in Epidemiology |
| `PRISMA-2020` | PRISMA | Preferred Reporting Items for Systematic Reviews and Meta-Analyses |
| `SQUIRE-2015` | SQUIRE | Standards for Quality Improvement Reporting Excellence |
| `CARE-2013` | CARE | CAse REport guideline |
| `AGREE-II` | AGREE | Appraisal of Guidelines for Research and Evaluation |

---

## Open Questions

- OQ-RG-01: Should ReportingGuideline replace the reporting_guideline ResourceSubtype, or coexist? Current recommendation: coexist — Resource.reporting_guideline subtype links to ReportingGuideline.code via `reporting_guideline_code` field. Confirm with Dave.
- OQ-RG-02: extension_codes[] is currently one-sided + validated (P5 pattern). Confirm this is preferred over two-sided storage.
