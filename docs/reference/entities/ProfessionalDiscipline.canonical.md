# Entity: ProfessionalDiscipline

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_Specialty.md (renamed + extended per Conflict 7 resolution)
SUPERSEDES: entity_Specialty.md (all Specialty data migrates to ProfessionalDiscipline)
COMPENDIUM_URL: /library/specialties/{slug}
NOTE: Compendium URL uses 'specialties' — medical-first Compendium at launch; presentation layer handles label.
PRESENTATION_LABEL: "Specialty" in Medical layer | "Practice Area" in Legal layer (see presentation_layers/)

## Purpose
ProfessionalDiscipline is a specific area of professional practice within a ProfessionalField.
It is profession-agnostic at canonical level; context-specific labels are applied by presentation layers.

Examples (Medical):   Psychiatry, Cardiology, General Practice, Anaesthesia, Radiology
Examples (Legal):     Family Law, Criminal Law, Corporate Law
Examples (Nursing):   Mental Health Nursing, Paediatric Nursing

This entity absorbs and renames the legacy `Specialty` / `professional_specialty` dataset (~70 entries).
It resolves all 11 audit-flagged sub-conflicts from entity_Specialty.md §5.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. Pattern `^[A-Z][A-Z0-9_-]{1,19}$`. e.g. PSYCH, CARDIO, CAMHS, GENPRAC. Immutable once in production. NOTE: former Domain code PSYCH is now free for this entity (Adult Psychiatry). |
| `name` | string | yes | Canonical display name, profession-agnostic register, 2–100 chars. e.g. "Adult Psychiatry" |
| `description` | string | null | Clinical/professional description, 1–3 sentences |
| `professional_field_code` | string | yes | FK → ProfessionalField.code. Required — resolves the domain_code gap from entity_Specialty.md §5 conflict 2. |
| `parent_code` | string | null | FK → ProfessionalDiscipline.code. Self-referential cascade parent (CAMHS → PSYCH → null). Must not create cycles. Top-level disciplines are null. |
| `domain_code` | string | null | FK → Domain.code. Denormalised convenience field — resolved via professional_field_code; populated for direct domain-level queries. |
| `regional_names` | object | yes | 5-key fixed shape: `{au_nz: string\|null, uk: string\|null, us: string\|null, india: string\|null, international: string\|null}`. All 5 keys required in every record; any may be null if name is identical to canonical. Open-map variant from shared schema rejected — fixed shape is canonical per Conflict 7 resolution. |
| `isco_unit_group_code` | string | null | ISCO-08 unit group code. International anchor. e.g. "2212" = Specialist Medical Practitioners. |
| `category` | enum | null | Practice grouping for onboarding pickers and Compendium navigation. Enum values: `clinical \| surgical \| diagnostic \| therapeutic \| primary_care \| other`. Locked — expansion requires schema version bump. Resolves entity_Specialty.md §5 conflict 6 (category enum vs free-text): fixed enum adopted, category strings outside enum are normalised to `other` or a new value via migration. |
| `training_colleges` | array | null | **OQ-008 PROMOTED** — this embedded array has been promoted to the `TrainingCollegeAssociation` canonical entity. The field is retained here as a documentation reference only and should not be stored on the ProfessionalDiscipline record in production. Query `TrainingCollegeAssociation.professional_discipline_code` for all governing college records for this discipline. |
| `subdomain_mappings` | string[] | null | FK[] → AcademicField.code. Linked academic fields (cross-branch link, professional→academic). Required array; may be empty. NOTE: Replaces old Specialty.subdomain_mappings[{subdomain_id, is_primary}] shape. Old D01.06 numeric codes map to AcademicField UPPERCASE_SHORT codes via migration 06. Resolves entity_Specialty.md §5 conflict 5 — treated as core (not [P] provisional). |
| `cross_specialty_domains` | string[] | null | FK[] → CrossDomainOverlay.code. Cross-domain overlay concepts that apply to this discipline (e.g. RESEARCH_METHODS, BIOETHICS). Symmetric — validated by CI script. |
| `related_disciplines` | string[] | null | FK[] → ProfessionalDiscipline.code. Self-referential cross-links. Symmetric — validated by _merge/validation/related_disciplines_symmetry.py. Equivalent to legacy related_specialties[]. |
| `common_methodologies` | string[] | null | FK[] → Methodology.code. Commonly used methodologies for research in this discipline. Uses canonical CoThesis Methodology codes. Resolves entity_Specialty.md §5 conflict 10 — code system normalised to Methodology entity codes. |
| `estimated_trainee_count` | integer | null | Approximate number of trainees in this discipline globally or in primary jurisdiction (AU/NZ at launch). |
| `is_active` | boolean | yes | Whether live in platform/Compendium. Decoupled from has_page. |
| `display_order` | integer | null | Sort order within a ProfessionalField |

---

## Page Mixin Fields

Attached — /library/specialties/{slug} (URL path uses "specialties" for current medical-first Compendium).

| Field | Type | Notes |
|---|---|---|
| `slug` | string | URL slug, kebab-case, stable once published |
| `page_title` | string \| null | SEO `<title>` tag |
| `meta_description` | string \| null | ≤160 chars |
| `short_description` | string \| null | Card/tile copy, 1–2 sentences |
| `seo_keywords` | string[] | Primary search terms |
| `icon` | string \| null | Lucide icon name, nullable. Resolves entity_Specialty.md §5 conflict 8 — icon is nullable (not required). |
| `has_page` | boolean | Whether Compendium page is generated |
| `is_active` | boolean | Whether entity appears in user-facing surfaces |
| `phase` | integer | Rollout phase (1 = launch) |

Note: The legacy `compendium` sub-object (entity_Specialty.md) is flattened — fields live directly on
the entity via this mixin. Resolves entity_Specialty.md §5 conflict 4.

---

## Derived Fields

None.

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| ProfessionalDiscipline.professional_field_code | many→one | ProfessionalField | required FK | resolves missing domain_code gap |
| ProfessionalDiscipline.parent_code | many→one | ProfessionalDiscipline | self, nullable | cascade hierarchy |
| ProfessionalDiscipline.code | one→many | ProfessionalSubdiscipline | ProfessionalSubdiscipline.professional_discipline_code | |
| ProfessionalDiscipline.subdomain_mappings[] | many→many | AcademicField | cross-branch link | no reciprocal array on AcademicField |
| ProfessionalDiscipline.cross_specialty_domains[] | many→many | CrossDomainOverlay | symmetric | validated by CI script |
| ProfessionalDiscipline.related_disciplines[] | many→many | ProfessionalDiscipline | self-ref, symmetric | validated by CI script |
| ProfessionalDiscipline.common_methodologies[] | many→many | Methodology | via Methodology.code | |
| ProfessionalDiscipline.code | one→many | TrainingCollegeAssociation | TrainingCollegeAssociation.professional_discipline_code | Promoted from embedded array (OQ-008) |

---

## Bidirectional Integrity

| Relationship | Rule | Validator |
|---|---|---|
| related_disciplines[] | Symmetric — if D1 lists D2, D2 must list D1 | `_merge/validation/related_disciplines_symmetry.py` |
| cross_specialty_domains[] ↔ CrossDomainOverlay.applicable_discipline_codes[] | Both stored; must agree | `_merge/validation/cross_specialty_domain_symmetry.py` |

---

## Presentation Labels

See `presentation_layers/` for full label tables.

| Layer | Label for ProfessionalDiscipline |
|---|---|
| Medical layer | "Specialty" |
| Legal layer | "Practice Area" |
| Compendium layer | "Specialty" (medical-only Compendium at launch) |
| Profession-agnostic / API | "ProfessionalDiscipline" |

---

## Conflicts Resolved (all 11 from entity_Specialty.md §5)

1. **NAMING** — Specialty vs Discipline vs Professional Specialty → resolved: `ProfessionalDiscipline` canonical; `Specialty` as presentation label in Medical layer only.
2. **domain_code FK gap** → resolved: `professional_field_code` (required) provides domain linkage; `domain_code` added as denormalised convenience field.
3. **regional_names shape** → resolved: 5-key fixed object (`au_nz`, `uk`, `us`, `india`, `international`). `india` key retained per conflict_7_resolution.md; no `canonical` key. Open-map variant from shared schema rejected.
4. **compendium sub-object** → resolved: flattened to Page Mixin (9 fields attached directly).
5. **subdomain_mappings [P] label** → resolved: treated as core field, no provisional marking. Shape changed from [{subdomain_id, is_primary}] to string[] → AcademicField.code[].
6. **category enum** → resolved: enum fixed to {clinical | surgical | diagnostic | therapeutic | primary_care | other}. Locked.
7. **training_colleges representation** → resolved: embedded array retained (junction cannot hold research_requirement_stage, has_research_requirement without duplication). shared schema junction is deprecated for this entity.
8. **icon required-ness** → resolved: nullable (not required). In Page Mixin.
9. **No reciprocal fields for bidirectional relationships** → resolved: `cross_specialty_domains[]` added to this entity; `related_disciplines[]` is the symmetric self-ref field. Bidirectional integrity by validation script (P5).
10. **Methodology code-system mismatch** → resolved: canonical CoThesis Methodology.code used. Old QUAL-01/QM-01 aliases resolved via Methodology entity mapping.
11. **Coverage-map version drift** → resolved: coverage map refreshed to v1.1.0 in entity_coverage_map.canonical.md.

---

## Code Examples (from legacy professional_specialty dataset)

| Legacy Specialty code | ProfessionalDiscipline code | Name |
|---|---|---|
| PSYCH | PSYCH | Adult Psychiatry |
| CAMHS | CAMHS | Child & Adolescent Psychiatry |
| GERIPSYCH | GERIPSYCH | Geriatric Psychiatry |
| CARDIO | CARDIO | Cardiology |
| GENSURG | GENSURG | General Surgery |
| GENPRAC | GENPRAC | General Practice |
| EMERG | EMERG | Emergency Medicine |
| RADIOL | RADIOL | Diagnostic Radiology |

Note: All ~70 legacy specialty codes are preserved as-is in ProfessionalDiscipline. No code changes
except where explicitly listed in migration 06.

