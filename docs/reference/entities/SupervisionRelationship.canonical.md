# SupervisionRelationship — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Stub authored OQ-007 session; full field set authored OQ-SR-01 session
NOTE: Private operational data — no Compendium page.
VERSION: 1.0.0

---

## Purpose

SupervisionRelationship records the existence of an active or historical supervision relationship between a Supervisor and a Trainee, optionally scoped to a specific Project and/or Program. It is the join record for the Supervisor ↔ Trainee many-to-many relationship and carries the operational metadata of that relationship over time.

A SupervisionContract formalises the terms of a relationship. A SupervisionRelationship may have zero contracts (informal arrangement) or many contracts over its lifetime. `current_contract_code` is a convenience pointer to the currently active contract.

**Relationship types (dual-branch, P1):** The `relationship_type` enum covers both clinical supervision roles (primary_supervisor, co_supervisor, associate_supervisor) and academic/research supervision roles (mentor, external_advisor, peer_supervisor). A clinician-researcher may carry multiple SupervisionRelationship records with different types — one as clinical supervisor and one as research mentor.

**Formal vs informal:** `is_formal` distinguishes college-recognised formal supervision (which typically requires a SupervisionContract and appears in progress records) from informal mentoring and peer-support arrangements.

**Meeting cadence:** `meeting_frequency` and `meeting_format` capture the operational agreement for how often and in what format supervision meetings occur. These are editorial; they may be overridden by SupervisionContract terms.

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. Convention: `SR-{supervisor_code}-{trainee_code}-{YY}[-N]` (e.g. SR-SMITH-J-JONES-R-24). Immutable once active. |
| `supervisor_code` | string | yes | Supervisor.code | FK to the Supervisor record |
| `trainee_code` | string | yes | Trainee.code | FK to the Trainee record |
| `project_code` | string \| null | no | Project.code | Scoped to a specific project. Null for general supervision not tied to a single project. |
| `program_code` | string \| null | no | Program.code | Program under which this supervision is conducted. Null for supervision outside a formal program. |
| `relationship_type` | enum | yes | — | See Enum Reference. `primary_supervisor \| co_supervisor \| associate_supervisor \| mentor \| external_advisor \| peer_supervisor` |
| `relationship_status` | enum | yes | — | See Enum Reference. `proposed \| active \| paused \| ended \| transferred` |
| `is_formal` | boolean | yes | — | True for college-recognised formal supervision requiring a contract; false for informal mentoring/peer arrangements. Default false. |
| `start_date` | date | yes | — | When the supervision relationship formally began (or was agreed). |
| `end_date` | date \| null | no | — | When the relationship ended. Null if ongoing. |
| `anticipated_end_date` | date \| null | no | — | Expected end date for planning purposes. Null if open-ended. |
| `meeting_frequency` | enum \| null | no | — | `weekly \| fortnightly \| monthly \| quarterly \| as_needed \| other`. How often supervision meetings occur. Nullable. |
| `meeting_format` | enum \| null | no | — | `in_person \| remote \| hybrid \| asynchronous`. Format of supervision meetings. Nullable. |
| `meeting_log_notes` | string \| null | no | — | Free-text field for supervisor/trainee notes on meeting arrangements and informal log. Not a structured meeting record (see future MeetingLog entity). |
| `current_contract_code` | string \| null | no | SupervisionContract.code | Convenience pointer to the currently active contract. Null for informal relationships or before a contract is signed. Must reference a contract where supervision_relationship_code = this.code and contract_status ∈ {active, renewed}. |
| `transferred_to_code` | string \| null | no | SupervisionRelationship.code | When relationship_status = transferred, points to the new SupervisionRelationship that replaced this one. Self-referential; nullable. |
| `notes` | string \| null | no | — | Internal operational notes |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private operational data.

---

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `has_active_contract` | current_contract_code | True when current_contract_code is not null and references a contract with status ∈ {active, renewed} |
| `duration_months` | start_date, end_date | `(end_date OR today) − start_date` in whole months |
| `is_ongoing` | relationship_status | True when relationship_status = `active` |
| `contract_count` | SupervisionContract records | Count of SupervisionContract records where supervision_relationship_code = this.code |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| `supervisor_code` | many→one | Supervisor | supervisor_code | Required |
| `trainee_code` | many→one | Trainee | trainee_code | Required |
| `project_code` | many→one | Project | project_code | Nullable |
| `program_code` | many→one | Program | program_code | Nullable |
| `current_contract_code` | many→one | SupervisionContract | current_contract_code | Nullable convenience pointer |
| `transferred_to_code` | many→one | SupervisionRelationship | transferred_to_code | Self-referential; nullable; only set when status=transferred |
| `code` | one→many | SupervisionContract | supervision_relationship_code | All contracts in this relationship's history |

---

## Enum Reference

### `relationship_type`
| Value | Description |
|---|---|
| `primary_supervisor` | The lead, college-recognised supervisor responsible for formal oversight. For clinical programs: the named principal supervisor on the college record. |
| `co_supervisor` | A co-equal supervisor sharing formal responsibility. Requires separate college registration in most programs. |
| `associate_supervisor` | A supporting supervisor with a subordinate formal role (e.g. RANZCP Associate Supervisor). |
| `mentor` | An informal or semi-formal mentor providing guidance without formal oversight responsibilities. |
| `external_advisor` | An advisor outside the trainee's home institution — e.g. methodology expert, statistician, content specialist. |
| `peer_supervisor` | Peer mentoring relationship — e.g. a senior resident supervising a junior on a specific project. |

### `relationship_status`
| Value | Description |
|---|---|
| `proposed` | Relationship has been proposed / agreed in principle but not yet formally started. |
| `active` | Relationship is current and ongoing. |
| `paused` | Relationship is temporarily paused (e.g. supervisor on leave, trainee deferral). |
| `ended` | Relationship has concluded (project complete, program exit, mutual agreement). |
| `transferred` | Supervision was formally transferred to a different supervisor. `transferred_to_code` records the new relationship. |

### `meeting_frequency`
| Value | Description |
|---|---|
| `weekly` | Weekly meetings |
| `fortnightly` | Every two weeks |
| `monthly` | Monthly meetings |
| `quarterly` | Quarterly meetings |
| `as_needed` | Ad hoc — no fixed schedule |
| `other` | Other arrangement |

### `meeting_format`
| Value | Description |
|---|---|
| `in_person` | Face-to-face meetings |
| `remote` | Video/phone meetings only |
| `hybrid` | Mix of in-person and remote |
| `asynchronous` | Primarily asynchronous (email, comments, async review) |

---

## Integrity Notes

- `current_contract_code` must reference a SupervisionContract where `supervision_relationship_code = this.code` and `contract_status ∈ {active, renewed}`. Validated by `supervision_contract_currency.py`.
- `transferred_to_code` must only be set when `relationship_status = transferred`.
- A Trainee should have exactly one `primary_supervisor` SupervisionRelationship with `relationship_status = active` at any time per Project. Validated by `supervision_relationship_integrity.py`.
- `is_formal = true` implies eventual `current_contract_code` population (warning-level, not blocking).
- `program_code` must be consistent with `project_code.program_code` when both are set (i.e. the project's program must match the relationship's program). Validated by `supervision_relationship_integrity.py`.
