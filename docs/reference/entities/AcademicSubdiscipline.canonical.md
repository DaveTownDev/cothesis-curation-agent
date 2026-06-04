# Entity: AcademicSubdiscipline

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — deepest level of academic branch)
COMPENDIUM_URL: /library/research-areas/{academic_field_slug}/{academic_discipline_slug}/{slug} (if has_page)

## Purpose
AcademicSubdiscipline is the fourth and deepest tier of the academic branch. It represents a
specific sub-area of academic research within an AcademicDiscipline.

Examples:
- Under SIMULATION_RESEARCH (AcademicDiscipline):
  - Simulation-Based Psychiatry Education
  - High-Fidelity Mannequin Simulation
  - Standardised Patient Research
- Under CARDIOLOGY_RESEARCH (AcademicDiscipline):
  - Interventional Cardiology Research
  - Heart Failure Biomarker Research

At launch, AcademicSubdiscipline rows are sparse — most research areas are adequately described at
the AcademicDiscipline level. This tier is scaffolded for completeness and future editorial growth.

has_page defaults to false for all AcademicSubdiscipline rows at launch.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. Immutable once in production. |
| `name` | string | yes | Display name. e.g. "Simulation-Based Psychiatry Education" |
| `description` | string | null | 1–3 sentences |
| `academic_discipline_code` | string | yes | FK → AcademicDiscipline.code. Required — every AcademicSubdiscipline belongs to exactly one AcademicDiscipline. |
| `parent_subdiscipline_code` | string | null | FK → AcademicSubdiscipline.code. Self-referential (rare — most subdisciplines are leaves). |
| `anzsrc_field_code` | string | null | ANZSRC 2020 specific field code (4-digit). e.g. "3201" = Cardiovascular Medicine and Haematology. |
| `is_active` | boolean | yes | Whether this subdiscipline is live |

---

## Page Mixin Fields

Attached if the AcademicSubdiscipline has a Compendium page.
has_page defaults to false.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name, nullable |
| `has_page` | boolean | Defaults false |
| `is_active` | boolean | Whether entity appears in user-facing surfaces |
| `phase` | integer | Rollout phase |

---

## Relationships

| From | Type | To | Via |
|---|---|---|---|
| AcademicSubdiscipline.academic_discipline_code | many→one | AcademicDiscipline | required FK |
| AcademicSubdiscipline.parent_subdiscipline_code | many→one | AcademicSubdiscipline | self, nullable |

---

## Notes

- Sparse at launch — editorial team grows this layer post-launch.
- Primarily useful for deep research taxonomy (e.g. linking highly specific Resource entries).
- ANZSRC field-level code (most specific ANZSRC level) provides international anchoring.

