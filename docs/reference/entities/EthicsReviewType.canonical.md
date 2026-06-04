# EthicsReviewType — Canonical Entity

STATUS: STUB (Tier 2 — app-only)
VERSION: v0.1.0 (stub — OQ-ETHICS-01 resolution, canonical v1.5.0)
Tier: 2 (App-only — Convex authors directly; not cloned from Compendium)

## Purpose

EthicsReviewType models jurisdictional ethics review bodies — the institutional committees
that review and approve research protocols (e.g. HREC in Australia, IRB in the USA,
REC in the UK, NHMRC-registered bodies, hospital research ethics committees).

This entity is **Tier 2 (app-only)**. The Compendium site does not model jurisdictional
ethics bodies — Compendium handles ethics at the cross-cutting skill level via FS-05
(Research Ethics) and the `ethics_typical` string field on Methodology. The CoThesis app's
Convex store models EthicsReviewType to support the trainee ethics submission workflow
(selecting the relevant review body, tracking approval timelines, storing protocol references).

**Not cloned from Compendium.** EthicsReviewType is authored and maintained by the CoThesis app.

## OQ-ETHICS-01 Resolution

Decision (2026-05-17, canonical v1.5.0): Standalone entity, Tier 2 (app-only). Clean
separation between:
- FS-05 Research Ethics (cross-cutting skill — how to navigate ethics; Tier 1, Compendium scope)
- EthicsReviewType (which body reviews a specific protocol; Tier 2, app scope)

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT format (e.g. `RPH_HREC`, `USYD_HREC`, `NIH_IRB`). |
| `name` | string | yes | — | Full name (e.g. "Royal Perth Hospital Human Research Ethics Committee") |
| `short_name` | string \| null | no | — | Abbreviation (e.g. "RPH HREC") |
| `body_type` | enum | yes | — | `hrec \| irb \| rec \| qai \| ethics_committee \| other` |
| `jurisdiction_code` | string \| null | no | — | ISO 3166-1 alpha-2 or ISO 3166-2 subdivision (e.g. `AU`, `AU-WA`, `US`, `GB`) |
| `organisation_code` | string \| null | no | Organisation.code | The institution hosting the review body (e.g. RPH, USYD) |
| `review_levels` | string[] \| null | no | — | Review pathways offered (e.g. `[full, low_risk, expedited, exempt]`) |
| `typical_review_duration_weeks_min` | integer \| null | no | — | Fastest expected review turnaround in weeks |
| `typical_review_duration_weeks_max` | integer \| null | no | — | Slowest expected review turnaround in weeks |
| `application_portal_url` | string \| null | no | — | URL for online submission portal |
| `guidance_url` | string \| null | no | — | URL for applicant guidance / SOPs |
| `is_active` | boolean | yes | — | Default true. False if body has been dissolved or merged. |
| `phase` | integer | yes | — | Rollout phase. Tier 2 — app implementation phase, not Compendium phase. |
| `created_at` | datetime | yes | — | |
| `updated_at` | datetime | yes | — | |

---

## Page Mixin Fields

NOT ATTACHED — EthicsReviewType is Tier 2 (app-only). No Compendium page.

---

## Derived Fields

| Field | Derived From | Rule |
|---|---|---|
| `is_currently_active` | is_active | True when is_active = true |

---

## Relationships

| Relation | Direction | Target | FK Field | Notes |
|---|---|---|---|---|
| organisation_code | many→one | Organisation | organisation_code | The host institution (optional; body may be standalone) |

---

## Notes

- This entity is a **stub**. Field set to be expanded when the CoThesis app implements the ethics submission workflow.
- Seed data (HREC, IRB, REC bodies) to be sourced from app requirements during Tier 2 build phase.
- `body_type: hrec` is Australian-specific; `irb` covers USA; `rec` covers UK; `qai` is Queensland Australia's Quality Assurance and Improvement pathway. The enum may be extended during build.
- See FS-05 (Research Ethics) for the cross-cutting skill that teaches trainees *how* to navigate ethics review regardless of which body applies.
- OQ-ETHICS-01 is RESOLVED. This stub satisfies the canonical schema placeholder; the full entity is a Tier 2 app build concern.
