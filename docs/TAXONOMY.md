# TAXONOMY — controlled vocabularies

Full canonical taxonomies live on the production Compendium site. **Runtime source of truth for the curation pipeline:** `data/taxonomy/live_methodologies.json` (148 platform codes, refreshed via `python -m scripts.fetch_live_taxonomy`) and `data/taxonomy/live_specialties.json` (53 specialty slugs). Vertex AI Search still grounds on the four MVP methodology cards below; the classifier may assign any live platform code.

## Resource types (14)
`article, book, book_chapter, video, podcast, software, reporting_guideline, course, web_guide, template, visual_reference, dataset, community, funding`. Each has subtypes (full set in Cowork); `type_fields` is discriminated by the type code (docs/SCHEMA.md, docs/field_maps/).

## THESIS stages (6)
`TH` Theory/question · `HI` History/literature · `EV` Evaluate/planning+ethics · `ST` Study/doing · `IN` Interpret/analysis · `SH` Share/writing+dissemination.

## MVP methodologies (4 — platform codes)
| Code | Name |
|---|---|
| SYN-01 | Narrative Systematic Review |
| SYN-02 | Scoping Review |
| OBS-01 | Retrospective Chart Review |
| EVAL-01 | Standards-Based Clinical Audit |
Full definitions for grounding go in `data/methodologies/` (drop-in).

## Legacy → platform code mapping (classifier emits platform codes)
The legacy classifier prompt uses display codes (RS-/OD-/EI-…). Emit platform codes instead, applying:
`RS-01 -> SYN-01` · `RS-04 -> SYN-02` · `OD-01 -> OBS-01` · `OD-06 -> EVAL-01`. The full crosswalk for non-MVP methods is in the Cowork cross-reference file; for MVP these four are the ones that matter.

## Foundation Skills (cross-cutting, FS-01..FS-16)
Project Management, Literature Searching, Literature Synthesis, Critical Appraisal, Research Ethics, Quantitative Methods, Qualitative Methods, Mixed Methods, Statistical Literacy, Data Management, Research Software, Academic Writing, Research Presentation, Research Dissemination, Supervision & Mentoring, Grant Writing. Use FS codes only for resources that *teach* the skill, not ones that merely use it.

## Specialty slugs (max 3 per resource)
Use slugs from `data/taxonomy/live_specialties.json` (e.g. `cardiology`, `adult-psychiatry`, `general-practice`). Omit if the resource applies broadly.
