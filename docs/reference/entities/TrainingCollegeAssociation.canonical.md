# TrainingCollegeAssociation — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
VERSION: unified-schema v1.0 (OQ-008 nested shape promotion)
SOURCE: Promoted from ProfessionalDiscipline.training_colleges[] embedded array
NOTE: Private operational data — no Compendium page.

---

## Purpose

TrainingCollegeAssociation records the relationship between a ProfessionalDiscipline and a governing college or board that provides training and accreditation for that discipline in a specific jurisdiction.

For example, in Australia/New Zealand, Adult Psychiatry (PSYCH) is governed by RANZCP; in the UK it is governed by the Royal College of Psychiatrists. These are separate TrainingCollegeAssociation records — one for each (discipline, college, jurisdiction) combination.

This entity was previously embedded as an array of objects within `ProfessionalDiscipline.training_colleges[]`. It was promoted to a standalone entity (OQ-008) because:
- It contains 2 FK references (Organisation.code, Country.code)
- Requirements change independently of the discipline (a college updates its research requirement without the discipline changing)
- Records may be queried by Project for compliance tracking ("does this project satisfy RANZCP research requirements?")

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `id` | uuid | yes | — | Surrogate PK |
| `professional_discipline_code` | string | yes | ProfessionalDiscipline.code | The discipline this association governs |
| `college_code` | string | yes | Organisation.code | FK to the governing college/board. Organisation must have types[] including training_provider. |
| `country_code` | string | yes | Country.code | Jurisdiction this association applies to |
| `training_pathway` | string | null | — | Free-text description of the training pathway offered by this college for this discipline in this jurisdiction |
| `research_requirement` | string | null | — | Free-text description of the research/thesis requirement mandated by this college |
| `research_requirement_stage` | string | null | — | Rough stage of training at which the research requirement must be completed (e.g. "Year 3", "Advanced Training", "Fellowship") |
| `is_primary` | boolean | yes | — | True when this is the primary governing body for this discipline in this jurisdiction. False for co-governing or secondary bodies. Default false. |
| `is_active` | boolean | yes | — | Default true. Set false when a college withdraws accreditation or the pathway is retired. |
| `notes` | string | null | — | Internal notes |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private operational data.

---

## Derived Fields

None.

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| professional_discipline_code | many→one | ProfessionalDiscipline | professional_discipline_code | Required |
| college_code | many→one | Organisation | college_code | Required; Organisation must be training_provider |
| country_code | many→one | Country | country_code | Required |

---

## Integrity Notes

- `college_code` must reference an Organisation where `types[]` includes `training_provider`. Validated by `_merge/validation/training_organisation_consistency.py`.
- Multiple records per discipline are expected (one per governing college per jurisdiction). There is no uniqueness constraint on `professional_discipline_code` alone.
- When `is_primary = true`, there should be at most one primary association per (professional_discipline_code, country_code) pair. Enforced at application layer.

---

## Migration Note

The embedded `training_colleges[]` array in `ProfessionalDiscipline.canonical.md` should be updated to remove the embedded sub-object definition and replaced with a documentation reference to this entity. ProfessionalDiscipline.canonical.md Relationships table gains a `one→many` entry to TrainingCollegeAssociation.

---

## Open Questions

None.
