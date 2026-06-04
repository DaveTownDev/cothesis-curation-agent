# UserProfile — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: entity_UserProfile.md (primary) + cothesis_shared_entity_schema.md §UserProfile (addendum)
VERSION: unified-schema v1.0 (merge output)
NOTE: The shared-schema "Layer 6 UserProfile" is a dangling FK reference, not a third schema — repointed to this entity.

## Purpose
UserProfile holds the user's professional/academic identity, personalisation preferences, and marketplace data. Distinct from User (which holds auth/account data). This is the entity exposed to the research-mentorship system.

## Source-of-Truth Fields
| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| user_code | string | yes | User.code | PK (1:1 with User) |
| professional_stage | enum | null | ProfessionalStage | At least one of professional_stage or academic_stage required |
| academic_stage | enum | null | AcademicStage | At least one of professional_stage or academic_stage required |
| academic_role | enum | null | — | faculty \| researcher \| clinician_researcher \| adjunct \| other; nullable, populate only when academic_stage is set |
| professional_discipline_code | string | null | ProfessionalDiscipline.code | Primary discipline/specialty |
| secondary_discipline_codes | string[] | null | ProfessionalDiscipline.code | Additional disciplines |
| program_code | string | null | Program.code | Enrolled program |
| institution_code | string | null | Organisation.code | Home institution |
| country_code | string | null | Country.code | Practice country |
| bio | string | null | — | Short biography |
| research_interests | string[] | null | — | Free-text tags |
| methodology_preference_codes | string[] | null | Methodology.code | Preferred methodologies |
| onboarding_complete | boolean | yes | — | default false |
| marketplace_visible | boolean | yes | — | default false; whether profile visible to other users |
| notification_preferences | jsonb | null | — | User notification settings |
| created_at | datetime | yes | — | |
| updated_at | datetime | yes | — | |

## Page Mixin Fields
NOT ATTACHED — UserProfiles are private data.

## Derived Fields
| Field | Derived From | Derivation Rule |
|---|---|---|
| stage_display_label | professional_stage OR academic_stage | Look up in active presentation layer |

## Relationships
| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| user_code | one→one | User | user_code | |
| professional_discipline_code | many→one | ProfessionalDiscipline | professional_discipline_code | |
| program_code | many→one | Program | program_code | |
| institution_code | many→one | Organisation | institution_code | |

## Notes
- `Program.stage_axis` enum (professional | academic | both) disambiguates which stage enum Program.stage references. Defaults to `professional` for Medicine Domain.
- The Shared Schema "Layer 6 UserProfile" dangling FK reference is resolved: it points to this entity.
