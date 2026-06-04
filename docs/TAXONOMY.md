# TAXONOMY — controlled vocabularies

Full canonical taxonomies (162 methodologies, 48 subtypes, 46 agent-discovery types) live in the Cowork project / Qdrant. The MVP grounds on the four methodologies below; classification still uses the full 14 resource types and the FS/THESIS vocabularies.

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
psychiatry, cardiology, general-practice, emergency-medicine, surgery, internal-medicine, paediatrics, obstetrics-gynaecology, radiology, pathology, anaesthetics, oncology, neurology, dermatology, ophthalmology, orthopaedics, urology, ent, geriatrics, rheumatology, endocrinology, gastroenterology, respiratory, nephrology, haematology, infectious-diseases, immunology, public-health, sports-medicine, palliative-care, intensive-care, rehabilitation, psychiatry-child-adolescent, addiction-medicine. Omit if the resource applies broadly.
