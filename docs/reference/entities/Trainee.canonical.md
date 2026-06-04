# Entity: Trainee

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — inferred from entity_SupervisionRelationship.md trainee_id FK)
PRESENTATION_LABEL: "Trainee / Registrar" in Medical layer | "Pupil" in Legal layer | "Candidate / PhD Student" in Academic layer
NOTE: Trainee extends User with trainee-specific research journey data. Distinct from User (the
authentication and core identity entity) and UserProfile (personalisation/settings entity).
The addendum §14.1 referenced trainees only as User FKs; this entity captures the professional
stage, program enrolment, and experience level data that drive the THESIS framework.

## Purpose
Trainee is the first-class entity for a platform user whose research journey is tracked through the
THESIS framework.

A Trainee is always a User (1:1 relationship via user_code). This entity holds the research and
professional context data that drives stage activation, blueprint selection, and supervision matching.

Not all Users are Trainees — supervisors, administrators, and anonymous users are not. Not all
Trainees are actively enrolled (is_active flag).

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_code` | string | yes | PK — 1:1 FK → User.code. Immutable. |
| `professional_stage` | enum | yes | ProfessionalStage value. Trainee's current stage in their profession. Drives stage-gated content. |
| `professional_discipline_code` | string | null | FK → ProfessionalDiscipline.code. Primary specialty/discipline. |
| `program_code` | string | null | FK → Program.code. Enrolled training program, if applicable. |
| `institution_code` | string | null | FK → Organisation.code. Home institution. |
| `year_of_training` | integer | null | Year within current stage (e.g. 1, 2, 3). Null if not applicable. |
| `research_experience` | enum | null | Self-reported research experience level. Values: `none` \| `basic` \| `intermediate` \| `advanced`. |
| `is_active` | boolean | yes | Whether actively enrolled. False = deferred, withdrawn, or completed. Default true. |

---

## Page Mixin Fields

NOT ATTACHED — Trainee is app-private data. Trainees are not Compendium-facing entities.

---

## Derived Fields

None.

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| Trainee.user_code | one→one | User | required FK | |
| Trainee.professional_discipline_code | many→one | ProfessionalDiscipline | nullable FK | |
| Trainee.program_code | many→one | Program | nullable FK | |
| Trainee.institution_code | many→one | Organisation | nullable FK | |
| Trainee.user_code | one→many | Project | Project.user_code | trainee's research projects |
| Trainee.user_code | one→many | SupervisionRelationship | SupervisionRelationship.trainee_code | |

---

## Source Field Migration

| Source field | Source entity | Canonical field |
|---|---|---|
| `trainee_id` (UUID) | SupervisionRelationship | `trainee_code` (string FK → Trainee.user_code) |

---

## Presentation Labels

| Layer | Label |
|---|---|
| Medical layer | "Trainee / Registrar" |
| Legal layer | "Pupil" |
| Academic layer | "Candidate / PhD Student" |

See `_merge/presentation_layers/` for full override configuration.

---

## Open Questions

- OQ-TRAINEE-01: Is a Trainee record created automatically when a User first creates a Project, or via an explicit onboarding step? Affects whether user_code=PK is safe vs a surrogate key.
- OQ-TRAINEE-02: Can a User be simultaneously a Trainee and a Supervisor (e.g. a senior resident who peer-mentors juniors)? If yes, Trainee and Supervisor are additive roles on the same User.
