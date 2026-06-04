# AssessmentCriterion — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Promoted from Program-embedded nested shape — OQ-008 deferred promotion, Task D session
NOTE: Private operational data — no Compendium page.
VERSION: 1.0.0

---

## Purpose

AssessmentCriterion is a named criterion used to assess the quality, completeness, or academic rigour of a trainee's research project within a training Program. Assessment criteria are defined at the Program level and applied across all Projects running under that Program.

Examples:
- "Research Question Clarity" — criterion requiring a clearly stated, answerable research question
- "Methodology Appropriateness" — criterion assessing whether the chosen method fits the question
- "Ethics Compliance" — criterion confirming ethics approval obtained and process followed
- "Statistical Analysis Rigour" — criterion for quantitative work in a fellowship program

A Program references its assessment criteria via `assessment_criterion_codes[]`. Individual Project assessments (e.g. supervisor sign-off, examination panel feedback) reference criteria to score or comment against.

**Promotion rationale (OQ-008):** This shape was estimated during the nested shape audit as belonging to Program. Full OQ-PROG-01 authoring confirmed it. PROMOTED over KEEP_EMBEDDED because:
- Criteria are reused across programs (e.g. "Research Question Clarity" applies to RANZCP and RACP programs)
- Criteria carry their own lifecycle (version, weight, rubric)
- Criteria need independent FK resolution for assessment tooling

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT. e.g. ASSESS-RQ-CLARITY, ASSESS-METHODOLOGY, ASSESS-ETHICS-COMPLIANCE. Immutable once in production. |
| `name` | string | yes | — | Criterion name (e.g. "Research Question Clarity") |
| `description` | string | yes | — | What this criterion assesses. 1–3 sentences. |
| `criterion_category` | enum | yes | — | `research_design \| methodology \| ethics \| writing \| data_analysis \| reporting \| process \| other`. Groups criteria for assessment display. |
| `weight` | number \| null | no | — | Relative weight of this criterion in a weighted assessment scheme (0.0–1.0). Null if equal weighting or unweighted. |
| `rubric` | string \| null | no | — | Free-text rubric or scoring guide. May contain markdown. |
| `minimum_pass_score` | number \| null | no | — | Minimum score to pass this criterion (where scoring applies). Null if pass/fail or not scored. |
| `program_codes` | string[] \| null | no | Program.code | Programs that use this criterion. Reciprocal to Program.assessment_criterion_codes[]. One-sided storage per P5; bidirectional integrity enforced by assessment_criterion_integrity.py. |
| `domain_codes` | string[] \| null | no | Domain.code | Domains this criterion applies to. Null = all domains. |
| `version` | string | yes | — | Semantic version (e.g. "1.0.0"). |
| `is_active` | boolean | yes | — | Default true. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — private operational data.

---

## Derived Fields

| Field | Derived From | Derivation Rule |
|---|---|---|
| `program_count` | program_codes[] | Count of Programs referencing this criterion. |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| `program_codes[]` | many→many | Program | program_codes | Reciprocal to Program.assessment_criterion_codes[]; P5 enforced |
| `domain_codes[]` | many→many | Domain | domain_codes | Nullable |

---

## Enum Reference

### `criterion_category`
| Value | Description |
|---|---|
| `research_design` | Quality of the research question, objectives, and overall design |
| `methodology` | Appropriateness and rigour of the research method |
| `ethics` | Ethics approval, compliance with ethical standards |
| `writing` | Clarity, structure, and quality of written output |
| `data_analysis` | Rigour and appropriateness of data analysis |
| `reporting` | Adherence to reporting guidelines (CONSORT, PRISMA, etc.) |
| `process` | Process milestones (e.g. supervisor meetings attended, deadlines met) |
| `other` | Not categorised above |
