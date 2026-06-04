# Entity: AcademicField

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — absorbs CrossSpecialtyDomain D-code entries + 8 CrossSpecialtyDomain
        overlay entries that are within-domain research areas, not truly cross-domain)
COMPENDIUM_URL: /library/research-areas/{slug}
PRESENTATION_LABEL: "Research Area" in Medical layer

## Purpose
AcademicField is the second tier of the academic branch (below Domain, above AcademicDiscipline).
It represents a broad research area within a Domain.

Distinct from CrossDomainOverlay: AcademicField entries are anchored to a specific Domain (e.g. HEALTH).
CrossDomainOverlay entries span multiple Domains (e.g. HEALTH + LAW + ENGINEERING).

Examples:
- Medical Education (within HEALTH)
- Public Health (within HEALTH)
- Implementation Science (within HEALTH)
- Health Informatics (within HEALTH)
- Health Economics (within HEALTH)

This entity replaces the D01–D30 numeric "Research Domain" taxonomy from the legacy specialty dataset
spec and absorbs the within-domain CrossSpecialtyDomain entries (see Migration Notes).

International anchors: ANZSRC 2020 Field of Research (AU/NZ), FORD (Fields of Research & Development).

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. Replaces old numeric D01–D30 codes. e.g. PUBLIC_HEALTH, MEDICAL_EDUCATION, CLINICAL_MEDICINE. Immutable once in production. |
| `name` | string | yes | Display name. e.g. "Medical Education", "Public Health" |
| `description` | string | null | 1–3 sentences describing the research area |
| `domain_code` | string | yes | FK → Domain.code. Required — every AcademicField belongs to exactly one Domain. Typically HEALTH for medical fields. |
| `anzsrc_division_code` | string | null | ANZSRC 2020 Field of Research division code. e.g. "32" = Biomedical and Clinical Sciences. Enables AU/NZ research classification. |
| `ford_subfield_code` | string | null | FORD subfield code for international cross-referencing. |
| `is_active` | boolean | yes | Whether this field is live |
| `display_order` | integer | null | Sort order within a Domain |

---

## Page Mixin Fields

Attached — /library/research-areas/{slug}.

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

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| AcademicField.domain_code | many→one | Domain | required FK | |
| AcademicField.code | one→many | AcademicDiscipline | AcademicDiscipline.academic_field_code | |
| AcademicField.code | many→many (reverse) | ProfessionalDiscipline | ProfessionalDiscipline.subdomain_mappings[] | cross-branch link; no reciprocal array stored on AcademicField |

---

## Migration Notes

### 1. CrossSpecialtyDomain → AcademicField (8 entries)

The following 8 of 10 CrossSpecialtyDomain entries migrate to AcademicField because they are
within-Domain research areas (scoped to HEALTH), not genuinely cross-Domain concepts.

| Old CrossSpecialtyDomain code | New AcademicField code | Name |
|---|---|---|
| MEDEDU | MEDICAL_EDUCATION | Medical Education |
| IMPLSCI | IMPLEMENTATION_SCIENCE | Implementation Science |
| HEALTHSERV | HEALTH_SERVICES_RESEARCH | Health Services Research |
| CLINPHARM_D | CLINICAL_PHARMACOLOGY_RESEARCH | Clinical Pharmacology (Research Domain) |
| TRANSRES | TRANSLATIONAL_RESEARCH | Translational Research |
| DIGHEALTH | HEALTH_INFORMATICS | Digital Health & Informatics |
| HEALTHECON | HEALTH_ECONOMICS | Health Economics & Policy |
| QI_PTSAFETY | QUALITY_IMPROVEMENT | Quality Improvement & Patient Safety |
| INDIG_HEALTH | INDIGENOUS_HEALTH | Indigenous Health Research |

Note: INDIG_HEALTH migrates here (9 entries total). See CrossDomainOverlay for the remaining 2 entries
(BIOETHICS, WELLBEING) that are confirmed true cross-domain overlays (OQ-010 resolved: WELLBEING → CrossDomainOverlay).

### 2. Numeric D01–D30 → AcademicField (30 entries)

The D01–D30 research domain taxonomy from the legacy specialty dataset spec maps to AcademicField
UPPERCASE_SHORT codes. Exact mapping requires data review of the full D01–D30 list; indicative
mappings below (to be confirmed during seed data authoring):

| Old code | New AcademicField code | Indicative name |
|---|---|---|
| D01 | CLINICAL_MEDICINE | Clinical Medicine & Surgery |
| D02 | PUBLIC_HEALTH | Public Health |
| D03 | MENTAL_HEALTH | Mental Health Research |
| D04 | OBSTETRICS_GYNAECOLOGY_RESEARCH | Obstetrics & Gynaecology Research |
| D05 | PAEDIATRIC_RESEARCH | Paediatric Research |
| D06 | PSYCHIATRY_RESEARCH | Psychiatry Research |
| D07 | EMERGENCY_CRITICAL_CARE_RESEARCH | Emergency & Critical Care Research |
| D08 | ANAESTHESIA_RESEARCH | Anaesthesia Research |
| D09 | MEDICAL_IMAGING_RESEARCH | Medical Imaging Research |
| D10 | PATHOLOGY_RESEARCH | Pathology & Laboratory Medicine Research |
| D11 | ONCOLOGY_RESEARCH | Oncology Research |
| D12 | GERIATRIC_RESEARCH | Geriatric Medicine Research |
| D13–D30 | (needs data review) | Remaining domains — codes assigned during seed data authoring |

NOTE: The D01.xx subdomain codes (e.g. D01.06 = Psychiatry research) map to AcademicDiscipline rows
under the parent AcademicField. See AcademicDiscipline.canonical.md.

---

## Open Questions

None.

