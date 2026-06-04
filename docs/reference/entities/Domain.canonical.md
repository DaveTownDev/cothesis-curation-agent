# Entity: Domain

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: entity_Domain.md (extended — added ford_broad_field_code, aligned PSYCH→PSYCHOLOGY rename)
COMPENDIUM_URL: /library/domains/{slug}

## Purpose
Domain is the top-level tier of both the professional and academic branches. It enables cross-profession
generalisability — every other hierarchy entity scopes through a Domain. Examples: HEALTH, LAW,
ENGINEERING, EDUCATION, PSYCHOLOGY.

NOTE: The code value PSYCH is renamed to PSYCHOLOGY at this tier (see §Code Rename below) to free
the code PSYCH for use at the ProfessionalDiscipline tier (Adult Psychiatry). This resolves
entity_Domain.md §5 conflict 6.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. e.g. HEALTH, LAW, ENGINEERING, EDUCATION, PSYCHOLOGY. Immutable once in production. **RENAME: PSYCH → PSYCHOLOGY** (see migration 06). |
| `name` | string | yes | Display name. e.g. "Health Sciences", "Law" |
| `description` | string | null | 1–2 sentences, plain English |
| `ford_broad_field_code` | string | null | FORD (Fields of Research & Development) broad field code. e.g. "3" = Medical and Health Sciences, "5" = Social Sciences. Enables mapping to international research classification. |
| `is_active` | boolean | yes | Whether this Domain is live. Only HEALTH is active at launch. |
| `display_order` | integer | null | Sort order in navigation and picker lists |

---

## Page Mixin Fields

Attached — Domains have top-level Compendium browse pages at /library/domains/{slug}.

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

Note: `is_active` appears in both Source-of-Truth and Page Mixin definitions — the Page Mixin value
is the canonical is_active. Single field, not duplicated in storage.

---

## Relationships

| From | Type | To | Via |
|---|---|---|---|
| Domain.code | one→many | ProfessionalField | ProfessionalField.domain_code |
| Domain.code | one→many | AcademicField | AcademicField.domain_code |
| Domain.code | one→many | Organisation (nullable) | Organisation.domain_code |
| Domain.code | one→many | Program | Program.domain_code |
| Domain.code | one→many | Terminology | Terminology.domain_code |

No reciprocal arrays stored on Domain — back-references are resolved by FK lookups on child entities.

---

## Code Rename

| Old Code | New Code | Reason |
|---|---|---|
| PSYCH | PSYCHOLOGY | Frees PSYCH for ProfessionalDiscipline (Adult Psychiatry). See migration 06. |

---

## Seed Data (expected at launch)

| code | name | is_active | ford_broad_field_code |
|---|---|---|---|
| HEALTH | Health Sciences | true | 3 |
| LAW | Law | false | 18 |
| ENGINEERING | Engineering | false | 9 |
| EDUCATION | Education | false | 13 |
| PSYCHOLOGY | Psychology | false | 17 |
| NURSING | Nursing & Midwifery | false | 3 |
| ALLIED_HEALTH | Allied Health | false | 3 |
| DENTISTRY | Dentistry | false | 3 |
| PHARMACY | Pharmacy | false | 3 |
| BIOMED | Biomedical Sciences | false | 3 |

---

## Conflicts Resolved

- entity_Domain.md §5 conflict 6: PSYCH collision — resolved by rename to PSYCHOLOGY.
- entity_Domain.md §5 conflict 1: "Domain" overloading (top-level domain vs research-taxonomy D01-D30) — resolved by this file using "Domain" exclusively for top-level profession entity; D01-D30 taxonomy maps to AcademicField (see AcademicField.canonical.md).
- entity_Domain.md §5 conflict 4: no reciprocal collections — confirmed: Domain holds no back-reference arrays; bidirectional integrity enforced by FK constraint on child entities.

