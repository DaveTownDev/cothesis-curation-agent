# Entity: ProfessionalField

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: Authored (new entity — second tier of professional branch; did not exist in source files)
COMPENDIUM_URL: /library/professional-fields/{slug}

## Purpose
ProfessionalField is the second tier of the professional branch, sitting between Domain and
ProfessionalDiscipline. It groups practice areas that share a professional identity and regulatory
framework.

Examples:
- HEALTH Domain → Medicine, Nursing, Allied Health, Pharmacy, Dentistry, Veterinary
- LAW Domain → Legal Practice, Judicial Work
- ENGINEERING Domain → Civil Engineering, Software Engineering

International anchor: ISCO-08 sub-major group codes (e.g. "22" = Health Professionals).

This tier was implicit in source files (entity_Domain.md seed data mixed Domain and ProfessionalField
concepts). It is now formalised as its own entity to give the hierarchy clean four-tier depth.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. e.g. MEDICINE, NURSING, ALLIED_HEALTH, PHARMACY, DENTISTRY, VETERINARY. Immutable once in production. |
| `name` | string | yes | Display name. e.g. "Medicine", "Nursing & Midwifery" |
| `description` | string | null | 1–2 sentences describing the professional field |
| `domain_code` | string | yes | FK → Domain.code. Required — every ProfessionalField belongs to exactly one Domain. |
| `isco_sub_major_code` | string | null | ISCO-08 sub-major group code. e.g. "22" = Health Professionals, "26" = Legal/Social/Cultural Professionals. International anchor for equivalence mapping. |
| `is_active` | boolean | yes | Whether this field is live in the platform |
| `display_order` | integer | null | Sort order within a Domain |

---

## Page Mixin Fields

Attached — ProfessionalFields surface on /library/professional-fields/{slug}.

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name, nullable |
| `has_page` | boolean | Whether Compendium page is generated. Defaults false until editorial content authored. |
| `is_active` | boolean | Whether entity appears in user-facing surfaces |
| `phase` | integer | Rollout phase (1 = launch) |

---

## Relationships

| From | Type | To | Via |
|---|---|---|---|
| ProfessionalField.domain_code | many→one | Domain | required FK |
| ProfessionalField.code | one→many | ProfessionalDiscipline | ProfessionalDiscipline.professional_field_code |

---

## Seed Data (HEALTH domain, expected at launch)

| code | name | domain_code | isco_sub_major_code | is_active |
|---|---|---|---|---|
| MEDICINE | Medicine | HEALTH | 22 | true |
| NURSING | Nursing & Midwifery | HEALTH | 22 | false |
| ALLIED_HEALTH | Allied Health | HEALTH | 22 | false |
| PHARMACY | Pharmacy | HEALTH | 22 | false |
| DENTISTRY | Dentistry | HEALTH | 22 | false |
| VETERINARY | Veterinary | HEALTH | 22 | false |

---

## Notes

- At launch, only MEDICINE is fully populated. Other fields are scaffolded (is_active: false).
- ProfessionalDisciplines currently in source data are almost entirely medical (under MEDICINE).
- Non-medical fields are deferred to Phase 2.

