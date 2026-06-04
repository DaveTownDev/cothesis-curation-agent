# Entity: ProfessionalSubdiscipline

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — was embedded subspecialty data within legacy Specialty rows)
COMPENDIUM_URL: /library/subspecialties/{slug}

## Purpose
ProfessionalSubdiscipline is the fourth and deepest tier of the professional branch. It represents
a recognised sub-area of practice within a ProfessionalDiscipline.

Examples:
- Under PSYCH (Adult Psychiatry):   Child & Adolescent Psychiatry (CAMHS), Geriatric Psychiatry,
                                     Forensic Psychiatry, Addiction Psychiatry, Consultation-Liaison
- Under GENSURG (General Surgery):  Colorectal Surgery, Vascular Surgery, Cardiothoracic Surgery

NOTE: In the legacy dataset, several of these appear as full ProfessionalDiscipline rows with a
parent_code. The parent_code self-reference on ProfessionalDiscipline handles two-level nesting
(e.g. CAMHS → PSYCH). ProfessionalSubdiscipline is used when a third level is needed, or when
an entry is clearly sub-subspecialty (e.g. Simulation-Based Child Psychiatry).

Editorial decision at data authoring time: entries that are adequately represented as
ProfessionalDiscipline.parent_code children stay there. True subspecialties requiring a third
level migrate to ProfessionalSubdiscipline.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. Pattern `^[A-Z][A-Z0-9_-]{1,19}$`. Immutable once in production. |
| `name` | string | yes | Display name, 2–100 chars |
| `description` | string | null | 1–3 sentences |
| `professional_discipline_code` | string | yes | FK → ProfessionalDiscipline.code. Required — every ProfessionalSubdiscipline belongs to exactly one ProfessionalDiscipline. |
| `parent_subdiscipline_code` | string | null | FK → ProfessionalSubdiscipline.code. Self-referential for four-level depth within the subspecialty branch (rare). |
| `training_colleges` | array | null | Embedded array of governing college/board entries. Sub-fields: `{college_code: string → Organisation.code, country_code: string → Country.code, training_pathway: string\|null, research_requirement: string\|null}`. May be empty array. |
| `isco_unit_group_code` | string | null | ISCO-08 unit group code. Usually null — ISCO does not reach clinical subspecialty depth. Populated only where a clear ISCO mapping exists. |
| `is_active` | boolean | yes | Whether this subspecialty is live |
| `display_order` | integer | null | Sort order within a ProfessionalDiscipline |

---

## Page Mixin Fields

Attached — /library/subspecialties/{slug}.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name, nullable |
| `has_page` | boolean | Whether Compendium page is generated. Defaults false — subspecialty pages are rare at launch. |
| `is_active` | boolean | Whether entity appears in user-facing surfaces |
| `phase` | integer | Rollout phase (1 = launch) |

---

## Relationships

| From | Type | To | Via |
|---|---|---|---|
| ProfessionalSubdiscipline.professional_discipline_code | many→one | ProfessionalDiscipline | required FK |
| ProfessionalSubdiscipline.parent_subdiscipline_code | many→one | ProfessionalSubdiscipline | self, nullable |

---

## Migration Notes

Embedded subspecialty data in legacy Specialty rows with parent_code is the primary source.
Examples that will migrate here (where a third level is warranted):
- Simulation-Based Child Psychiatry (under CAMHS)
- Paediatric Cardiac Surgery (under THORAC)
- Interventional Radiology sub-specialties (under RADIOL)

Most legacy parent_code children (CAMHS, GERIPSYCH, FORENSIC, ADDICTION, CONSULT under PSYCH) will
remain as ProfessionalDiscipline rows — they are well-established disciplines, not subspecialties.
See migration 06 for full mapping decisions.

