# Entity: Supervisor

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Authored (new entity — inferred from entity_SupervisionRelationship.md supervisor_id FK)
PRESENTATION_LABEL: "Supervisor" in Medical layer | "Pupil Master" in Legal layer | "Doctoral Supervisor / PI" in Academic layer
NOTE: Supervisor extends User with supervisor-specific professional profile data. Distinct from User
(the authentication and core identity entity) and Person (the Compendium-facing public profile entity).
The addendum §14.1 referenced supervisors only as User FKs; this entity captures the professional
profile, capacity management, and marketplace data that drive supervision matching.

## Purpose
Supervisor is the first-class entity for a platform user who holds a supervisory role.

A Supervisor is always a User (1:1 relationship via user_code). This entity holds supervisor-specific
data beyond what User holds: marketplace visibility, supervision capacity, methodological expertise,
and professional context. It supports the Dual-Track Adaptive Mentorship patent (track_type in
SupervisionRelationship).

Not all Users are Supervisors. A User becomes a Supervisor when their role includes supervision
responsibilities and they have an active Supervisor record.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_code` | string | yes | PK — 1:1 FK → User.code. The user must have role=supervisor. Immutable. |
| `professional_discipline_code` | string | null | FK → ProfessionalDiscipline.code. Primary specialty/discipline. |
| `institution_code` | string | null | FK → Organisation.code. Home institution. |
| `professional_stage` | enum | null | ProfessionalStage value. Supervisor's own career stage — typically `independent` or `cpd`. |
| `supervision_capacity` | integer | null | Maximum simultaneous active supervisees. Null = no stated limit. |
| `supervision_types` | enum[] | null | Types of supervision offered. Values: `research` \| `clinical` \| `pastoral` \| `academic`. May hold multiple. |
| `methodology_expertise_codes` | string[] | null | FK[] → Methodology.code. Areas of methodological expertise for matching. |
| `bio` | string | null | Short professional biography. ≤500 chars. |
| `accepts_new_supervisees` | boolean | yes | Whether actively accepting new supervisees. Default false. |
| `marketplace_visible` | boolean | yes | Whether listed on the supervisor marketplace. Default false. Decoupled from accepts_new_supervisees — a supervisor can be visible but paused. |

---

## Page Mixin Fields

NOT ATTACHED — Supervisor is app-private data. Supervisors may have public Person profiles (see
Person.canonical.md) but Supervisor itself is not a Compendium page entity.

---

## Derived Fields

| Field | Derivation | Type |
|---|---|---|
| `current_supervisee_count` | COUNT of active SupervisionRelationship records where supervisor_code = this.user_code | integer |
| `is_at_capacity` | current_supervisee_count ≥ supervision_capacity (when supervision_capacity is not null) | boolean |

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| Supervisor.user_code | one→one | User | required FK | user must have role=supervisor |
| Supervisor.professional_discipline_code | many→one | ProfessionalDiscipline | nullable FK | |
| Supervisor.institution_code | many→one | Organisation | nullable FK | |
| Supervisor.methodology_expertise_codes[] | many→many | Methodology | one-sided array | no reciprocal on Methodology |
| Supervisor.user_code | one→many | SupervisionRelationship | SupervisionRelationship.supervisor_code | |

---

## Source Field Migration

| Source field | Source entity | Canonical field |
|---|---|---|
| `supervisor_id` (UUID) | SupervisionRelationship | `supervisor_code` (string FK → Supervisor.user_code) |

---

## Presentation Labels

| Layer | Label |
|---|---|
| Medical layer | "Supervisor" |
| Legal layer | "Pupil Master" |
| Academic layer | "Doctoral Supervisor / Principal Investigator" |

See `_merge/presentation_layers/` for full override configuration.

---

## Open Questions

- OQ-SUP-01: Should Supervisor have a public Compendium-style profile page (/supervisors/{slug})? If yes, attach Page Mixin. Confirm with Dave.
- OQ-SUP-02: `marketplace_visible` vs `accepts_new_supervisees` — confirm these are two distinct flags: discoverability vs willingness.
