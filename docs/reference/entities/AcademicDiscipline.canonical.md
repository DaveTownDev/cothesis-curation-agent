# Entity: AcademicDiscipline

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — absorbs ~175 subdomain entries from legacy D01.xx taxonomy)
COMPENDIUM_URL: /library/research-areas/{academic_field_slug}/{slug} (if has_page)

## Purpose
AcademicDiscipline is the third tier of the academic branch (below AcademicField, above
AcademicSubdiscipline). It represents a specific research discipline within a broad research area.

In the legacy dataset, these appear as D01.01, D01.02 … D30.xx subdomain codes.
Each D-major.D-minor code maps to one AcademicDiscipline row under its parent AcademicField.

Examples:
- Under CLINICAL_MEDICINE (AcademicField):
  - D01.01 → CARDIOLOGY_RESEARCH (Cardiology Research)
  - D01.02 → INTERNAL_MEDICINE_RESEARCH (Internal Medicine Research)
  - D01.06 → PSYCHIATRY_RESEARCH_DISC (Psychiatry Research)
- Under MEDICAL_EDUCATION (AcademicField):
  - CURRICULUM_DESIGN (Curriculum Design Research)
  - SIMULATION_RESEARCH (Simulation-Based Research)
  - ASSESSMENT_RESEARCH (Assessment & Evaluation Research)

Not all AcademicDisciplines will have a Compendium page at launch. has_page defaults to false.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. Meaningful code replacing numeric D-codes. e.g. CARDIOLOGY_RESEARCH, SIMULATION_RESEARCH. Immutable once in production. |
| `name` | string | yes | Display name. e.g. "Cardiology Research", "Simulation-Based Medical Education" |
| `description` | string | null | 1–3 sentences |
| `academic_field_code` | string | yes | FK → AcademicField.code. Required — every AcademicDiscipline belongs to exactly one AcademicField. |
| `parent_code` | string | null | FK → AcademicDiscipline.code. Self-referential for nested disciplines within the same AcademicField. |
| `anzsrc_group_code` | string | null | ANZSRC 2020 group-level code. e.g. "3201" = Cardiovascular Medicine and Haematology. |
| `is_active` | boolean | yes | Whether this discipline is live |

---

## Page Mixin Fields

Attached if the AcademicDiscipline has a Compendium page — not all will at launch.
has_page defaults to false until editorial content is authored.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name, nullable |
| `has_page` | boolean | Defaults false — only set true when editorial content is authored |
| `is_active` | boolean | Whether entity appears in user-facing surfaces |
| `phase` | integer | Rollout phase |

---

## Relationships

| From | Type | To | Via |
|---|---|---|---|
| AcademicDiscipline.academic_field_code | many→one | AcademicField | required FK |
| AcademicDiscipline.parent_code | many→one | AcademicDiscipline | self, nullable |
| AcademicDiscipline.code | one→many | AcademicSubdiscipline | AcademicSubdiscipline.academic_discipline_code |

---

## Migration Notes

Source: ~175 subdomain entries from the legacy D01.xx taxonomy.
Migration strategy:
1. Each D-major code maps to an AcademicField (see AcademicField migration table).
2. Each D-major.D-minor code maps to an AcademicDiscipline under that AcademicField.
3. Subdomain codes are replaced with meaningful UPPERCASE_SHORT codes.
4. Old subdomain_id strings (e.g. "D01.06") are preserved as a legacy_code field on the row
   during migration for reverse-lookup; legacy_code is not a public field.

Expected count: ~175 rows (all D-minor codes across D01–D30).

