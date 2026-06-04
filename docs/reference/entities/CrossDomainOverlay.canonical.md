# Entity: CrossDomainOverlay

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: entity_CrossCuttingArea.md (renamed + reduced — only entries that genuinely span multiple Domains)
SUPERSEDES: CrossSpecialtyDomain (for the 1–2 true overlay entries: BIOETHICS, and RESEARCH_METHODS if added)
NOTE: Reduced replacement for CrossSpecialtyDomain. Expected 2–3 entries total.
      Most CrossSpecialtyDomain entries → AcademicField (see AcademicField.canonical.md migration notes).

## Purpose
CrossDomainOverlay represents concepts that genuinely span multiple Domains (not just within HEALTH).
The test: does the concept apply equally to a Health practitioner AND a Lawyer AND an Engineer?

Distinct from AcademicField, which is anchored to a specific Domain (e.g. HEALTH).
CrossDomainOverlay is truly Domain-agnostic.

Expected entries:
- RESEARCH_METHODS — fundamental research methodology spans all domains (HEALTH, LAW, ENGINEERING, EDUCATION)
- BIOETHICS — ethical reasoning spans all professional domains
- WELLBEING — confirmed CrossDomainOverlay (OQ-010 resolved) — wellbeing applies equally across all professional domains: health, law, engineering, education, and others

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. e.g. RESEARCH_METHODS, BIOETHICS. Immutable once in production. |
| `name` | string | yes | Display name. e.g. "Research Methods", "Bioethics" |
| `description` | string | yes | Explain what makes this concept genuinely cross-domain. Required (not nullable) — the justification for cross-domain status must be documented. |
| `applicable_discipline_codes` | string[] | null | FK[] → ProfessionalDiscipline.code. Which disciplines this overlay applies to. May use ["*"] sentinel to mean all disciplines. Symmetric with ProfessionalDiscipline.cross_specialty_domains[]. |
| `is_active` | boolean | yes | Whether this overlay is live |

---

## Page Mixin Fields

NOT ATTACHED — CrossDomainOverlay entries do not generate standalone Compendium pages at launch.
Overlay concepts surface as tags/filters within Compendium pages for ProfessionalDiscipline and AcademicField.

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| CrossDomainOverlay.applicable_discipline_codes[] | many→many | ProfessionalDiscipline | symmetric | validated by CI script |

---

## Bidirectional Integrity

applicable_discipline_codes[] ↔ ProfessionalDiscipline.cross_specialty_domains[]
Both sides stored. Validated by `_merge/validation/cross_specialty_domain_symmetry.py`.

If applicable_discipline_codes uses ["*"] sentinel, the validation script treats it as matching
all active ProfessionalDiscipline codes — this must be explicitly handled in the validator.

---

## Conflicts Resolved (from entity_CrossCuttingArea.md §5)

1. NAMING — CrossCuttingArea vs CrossSpecialtyDomain → resolved: `CrossDomainOverlay` canonical (profession-agnostic per P1; distinguishes from AcademicField).
2. Self-link field renamed — `related_domains` (dataset spec) vs `related_areas` (shared schema) → resolved: no self-link field on CrossDomainOverlay (too few entries to warrant it).
3. applicable_specialties[] array vs junction table → resolved: embedded array retained (2–3 entries; ["*"] wildcard is awkward in junction). Sentinel ["*"] preserved.
4. regional_names conflict → resolved: not included — CrossDomainOverlay does not have regional names (concepts are universal).
5. compendium sub-object → resolved: Page Mixin NOT attached (no standalone Compendium pages).
6. URL path conflict → resolved: no standalone URL (not applicable — no pages generated).
7. No bidirectional-validation rule for self-links → resolved: self-links removed (too few entries).
8. Entry-count drift → resolved: canonical count is 3 (BIOETHICS confirmed; RESEARCH_METHODS added; WELLBEING confirmed OQ-010).
9. No reciprocal field on Specialty → resolved: ProfessionalDiscipline.cross_specialty_domains[] added as reciprocal field.

---

## Expected Entries

| code | name | status |
|---|---|---|
| BIOETHICS | Bioethics | confirmed — migrates from CrossSpecialtyDomain |
| RESEARCH_METHODS | Research Methods | new entry — genuinely cross-domain |
| WELLBEING | Wellbeing | confirmed CrossDomainOverlay (OQ-010 resolved) |

---

## Open Questions

None.

