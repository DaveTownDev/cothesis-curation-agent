# ResourceSubtype.course — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: course
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A course is a structured educational offering — online course, workshop, webinar series, or formal programme — with enrollment, certification, and duration metadata.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `provider_code` | string | No | → Organisation.code. Provider/institution offering the course. Was: `institution_entity_id`, `institution_name`. |
| `course_url` | string (uri) | No | Direct URL to enrol or access the course. May differ from Resource.url (landing page vs direct access). |
| `duration_hours` | number | No | Estimated total duration in hours. Cluster E canonical for courses. Was: `total_hours`, `total_video_hours`. |
| `effort_hours_per_week` | number | No | Estimated effort in hours per week (self-paced guidance). |
| `duration_weeks` | integer | No | Estimated duration in weeks. |
| `format` | string (enum) | No | `self_paced` \| `cohort` \| `live` \| `workshop` \| `blended`. |
| `certification_available` | boolean | No | Whether a certificate of completion is offered. |
| `cost_aud` | number | No | Cost in AUD. Null = free. |
| `price_currency` | string | No | ISO 4217 currency code (default `AUD`). |
| `has_free_tier` | boolean | No | Whether audit/free access is available. Was: `audit_available`. |
| `financial_aid` | boolean | No | Whether financial aid is available. |
| `cme_credits` | number | No | Continuing medical education credits awarded on completion. |
| `is_peer_reviewed` | boolean | No | Whether the course itself is peer-reviewed (e.g. MedEdPortal, MERLOT). |
| `platform_rating` | number | No | Course platform average rating (Coursera, edX, etc.). Cluster H. |
| `class_central_rating` | number | No | Class Central aggregate rating. |
| `merlot_peer_review_score` | number | No | MERLOT peer review score. |
| `enrollment_count` | integer | No | Total enrollments (from platform API). |
| `instructor_names` | string[] | No | Instructor names (free-text). Cluster C. |
| `presenter_person_ids` | string[] | No | → Person.code[] for workshop presenters. |
| `institution_logo_url` | string (uri) | No | Provider institution logo. Cluster F. |
| `course_image_url` | string (uri) | No | Course card/hero image. Cluster F; maps to thumbnail_url on Resource base. |
| `sample_cards` | object[] | No | Sample flash cards or quiz items (for spaced-repetition courses). |
| `card_count` | integer | No | Number of flash cards/quiz items. |
| `materials_files` | string[] | No | URLs to downloadable course materials. |
| `slides_url` | string (uri) | No | URL to course slides. |
| `recording_url` | string (uri) | No | URL to course recording (for completed live/workshop courses). |
| `video_count` | integer | No | Number of video lectures. |
| `start_date` | string (date) | No | Course start date (for cohort/live formats). |
| `workshop_date` | string (date) | No | Workshop event date. |
| `conference_entity_id` | string | No | → Conference entity if this is a conference workshop. |
| `series_name` | string | No | Course series or specialisation name. Was: `part_of_specialization`. |
| `time_commitment` | string | No | AI assessment of realistic time commitment. |
| `download_url` | string (uri) | No | URL to download course materials (OA/free courses). |

## Notes

- Course is a heterogeneous subtype covering ~5 sub-types (MOOC, workshop, webinar, formal programme, short course). "Many fields will be null for simpler subtypes" (per matrix §6.6).
- `cost_aud` is null for free courses (has_free_tier=true and cost_aud=null are both valid; audit courses have has_free_tier=true but cost_aud may reflect the paid price).
- `cme_credits` is important for Australian/NZ specialty college CPD requirements — key for CoThesis audience.
- Cluster E duration for courses: `duration_hours` is canonical; `effort_hours_per_week` and `duration_weeks` provide additional granularity for structured courses.
