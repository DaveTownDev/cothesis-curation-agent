# EthicsRequirement — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Promoted from Program-embedded nested shape — OQ-008 deferred promotion, Task D session
NOTE: Private operational data — no Compendium page.
VERSION: 1.0.0

---

## Purpose

EthicsRequirement defines a specific ethics-related requirement or obligation that applies to research conducted under a training Program. Ethics requirements capture what approvals, notifications, or processes a trainee must complete before or during their research.

Examples:
- "Institutional Ethics Approval Required (HREC)" — full ethics review required before data collection
- "Low-Risk Exemption Pathway Available" — projects meeting low-risk criteria may use expedited review
- "Quality Improvement / Audit Exemption" — clinical audits and QI projects may be exempt from HREC
- "Research Involving Vulnerable Populations — Additional Approval Required"
- "Data Privacy Impact Assessment Required for Secondary Data Use"

A Program references its ethics requirements via `ethics_requirement_codes[]`. The `Project` entity carries `ethics_approval_code` and `ethics_approval_status` to record compliance with applicable requirements.

**Promotion rationale (OQ-008):** Promoted over KEEP_EMBEDDED because:
- Ethics requirements are reused across Programs (e.g. HREC requirement shared by all clinical fellowship programs)
- Requirements have structured, versioned rules — not free-form text
- Independent FK resolution needed for compliance tracking and ethics approval dashboards

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT. e.g. ETHICS-HREC-FULL, ETHICS-LOWRISK-EXEMPT, ETHICS-QI-EXEMPT, ETHICS-VULN-POP. Immutable once in production. |
| `name` | string | yes | — | Requirement name (e.g. "Full HREC Approval Required") |
| `description` | string | yes | — | Full statement of the requirement. Should be actionable for a trainee. |
| `requirement_type` | enum | yes | — | `approval_required \| notification_required \| exemption_available \| conditional \| waived \| other` |
| `approval_body` | string \| null | no | — | Name of the ethics body or committee responsible (e.g. "Institutional HREC", "National Ethics Advisory Committee"). Free-text. |
| `applies_to_study_types` | string[] \| null | no | — | Study or methodology types this requirement applies to (e.g. ["rct", "observational", "secondary_data"]). Editorial; not FK-normalised. Null = all types. |
| `is_blocking` | boolean | yes | — | True if research cannot proceed without satisfying this requirement (blocking gate). False if advisory or post-hoc. Default true for approval_required type. |
| `regulatory_reference` | string \| null | no | — | Relevant legislation or guideline reference (e.g. "National Statement on Ethical Conduct in Human Research 2007 (updated 2018)"). |
| `guidance_url` | string \| null | no | — | URL to official guidance for satisfying this requirement. |
| `program_codes` | string[] \| null | no | Program.code | Programs that impose this requirement. Reciprocal to Program.ethics_requirement_codes[]. P5 integrity enforced by ethics_requirement_integrity.py. |
| `domain_codes` | string[] \| null | no | Domain.code | Domains this requirement applies to. Null = all domains. |
| `version` | string | yes | — | Semantic version (e.g. "1.0.0"). |
| `is_active` | boolean | yes | — | Default true. |
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
| `program_codes[]` | many→many | Program | program_codes | Reciprocal to Program.ethics_requirement_codes[]; P5 enforced |
| `domain_codes[]` | many→many | Domain | domain_codes | Nullable |

---

## Enum Reference

### `requirement_type`
| Value | Description |
|---|---|
| `approval_required` | Full ethics committee approval required before research proceeds |
| `notification_required` | Ethics body must be notified (but approval not required) |
| `exemption_available` | Expedited or exempt pathway available for qualifying research |
| `conditional` | Ethics requirements depend on study characteristics (type, population, data source) |
| `waived` | Ethics review explicitly waived for this program/study type |
| `other` | Not categorised above |
