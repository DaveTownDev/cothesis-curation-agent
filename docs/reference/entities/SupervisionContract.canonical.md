# SupervisionContract — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
VERSION: unified-schema v1.0 (OQ-007 resolution)
SOURCE: Authored — OQ-007 resolved as standalone entity (not a status field on SupervisionRelationship)
NOTE: Private supervision data — no Compendium page.

---

## Purpose

Formal supervision agreement between a Supervisor, Trainee, and (optionally) a Program. Captures terms of supervision, meeting cadence, deliverables, signed dates, renewals, and termination.

Distinct from SupervisionRelationship (which records the *existence* of the relationship) — SupervisionContract records the *formal agreement(s)* attached to that relationship. A SupervisionRelationship may have zero or many SupervisionContract records over its lifetime (informal start → formal contract → renewal → termination).

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT or UUID-derived. Contracts aren't user-browsable; human-readable code optional. |
| `supervision_relationship_code` | string | yes | SupervisionRelationship.code | The relationship this contract formalises |
| `contract_status` | enum | yes | — | `draft \| pending_signature \| active \| renewed \| expired \| terminated \| superseded` |
| `start_date` | date | yes | — | Effective date of this contract |
| `end_date` | date | null | — | Null for open-ended; expiry date otherwise |
| `agreed_meeting_frequency` | enum | null | — | `weekly \| fortnightly \| monthly \| ad_hoc \| other` |
| `meeting_modality` | enum | null | — | `in_person \| video \| phone \| mixed` |
| `time_commitment_hours_per_month` | integer | null | — | Estimated supervisor hours per month |
| `deliverables` | string | null | — | Free-text — what the trainee is producing under this contract |
| `college_requirement_codes` | string[] | null | Organisation.code | Which colleges' formal requirements this contract satisfies. FK to Organisation where types[] includes training_provider. |
| `signed_by_supervisor_at` | datetime | null | — | Timestamp of supervisor signature |
| `signed_by_trainee_at` | datetime | null | — | Timestamp of trainee signature |
| `signed_by_program_director_at` | datetime | null | — | Optional third-party signoff; required by some colleges |
| `document_attachment_url` | string | null | — | Signed PDF storage URL |
| `renewal_of_contract_code` | string | null | SupervisionContract.code (self-ref) | If this contract renews a prior contract |
| `superseded_by_contract_code` | string | null | SupervisionContract.code (self-ref) | If a newer contract supersedes this one |
| `termination_reason` | string | null | — | Free-text description when status = terminated |
| `terminated_by_user_code` | string | null | User.code | User who initiated termination |
| `terminated_at` | datetime | null | — | Timestamp of termination |
| `notes` | string | null | — | Internal notes |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private contract data, never surfaced on Compendium.

---

## Derived Fields

| Field | Derived From | Rule |
|---|---|---|
| `is_currently_active` | contract_status, start_date, end_date | `contract_status IN [active, renewed] AND start_date <= today AND (end_date IS NULL OR end_date >= today)` |
| `days_to_expiry` | end_date | `end_date - today` if end_date is not null; null otherwise |
| `signature_complete` | signed_by_supervisor_at, signed_by_trainee_at, signed_by_program_director_at | True when all required signatures populated (program_director signoff is optional per college; app layer enforces which signatures are required) |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| supervision_relationship_code | many→one | SupervisionRelationship | supervision_relationship_code | Required |
| terminated_by_user_code | many→one | User | terminated_by_user_code | Nullable |
| college_requirement_codes[] | many→many | Organisation | college_requirement_codes | FK where Organisation.types[] includes training_provider |
| renewal_of_contract_code | many→one | SupervisionContract (self-ref) | renewal_of_contract_code | Prior contract being renewed |
| superseded_by_contract_code | one→one | SupervisionContract (self-ref) | superseded_by_contract_code | Newer contract that supersedes this one |
| code | ←one | SupervisionRelationship | current_contract_code | Convenience pointer stored on relationship; see SupervisionRelationship.canonical.md |

---

## Integrity Notes

- A SupervisionRelationship may have zero or many SupervisionContract records over its lifetime.
- The "current" contract is resolved via `SupervisionRelationship.current_contract_code` (nullable FK pointer).
- Per P5, bidirectional integrity enforced by `_merge/validation/supervision_contract_currency.py`.
- `renewal_of_contract_code` → the prior contract MUST have `contract_status IN [superseded, expired]`.
- `superseded_by_contract_code` → the newer contract MUST have a later `start_date` than this one.
