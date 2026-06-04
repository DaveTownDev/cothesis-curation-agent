# Entity: OutputType

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
SOURCE: Authored (new entity — inferred from entity_ProjectDocument.md FK output_type_id)
NOTE: OutputType was referenced as a UUID FK on ProjectDocument but never defined in the addendum.
This file defines the entity and records the UUID→code migration path.

## Purpose
OutputType classifies the kind of output or deliverable a Project produces.
It is a platform-administered lookup/reference entity — values are set by CoThesis, not by users.

Examples: Research Report, Journal Article, Thesis, Conference Poster, Ethics Protocol, Grant Application.

---

## Source-of-Truth Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `code` | string | yes | UPPERCASE_SHORT PK. e.g. `RESEARCH_REPORT`, `JOURNAL_ARTICLE`, `THESIS`, `CONF_POSTER`, `ETHICS_PROTOCOL`. Immutable once in production. |
| `name` | string | yes | Display name. e.g. "Journal Article", "Conference Poster" |
| `description` | string | null | 1–2 sentences describing this output type. |
| `compatible_methodology_codes` | string[] | null | FK[] → Methodology.code. Methodologies that typically produce this output type. Informational — not a constraint. |
| `is_active` | boolean | yes | Whether live in platform. |
| `display_order` | integer | null | Sort order in pickers and lists. |

---

## Page Mixin Fields

NOT ATTACHED — OutputType is a platform reference entity, not a Compendium-facing entity.

---

## Derived Fields

None.

---

## Relationships

| From | Type | To | Via | Notes |
|---|---|---|---|---|
| OutputType.compatible_methodology_codes[] | many→many | Methodology | one-sided array | no reciprocal on Methodology |
| OutputType.code | one→many | ProjectDocument | ProjectDocument.output_type_code | |

---

## Source Field Migration

| Source field | Source entity | Canonical field |
|---|---|---|
| `output_type_id` (UUID) | ProjectDocument | `output_type_code` (string FK → OutputType.code) |

---

## Open Questions

- OQ-OUTPUT-01: Should OutputType have Compendium pages (e.g. /library/output-types/journal-article)? If yes, attach Page Mixin. Confirm with Dave.
- OQ-OUTPUT-02: Is compatible_methodology_codes the right model, or should it be a junction entity to carry additional metadata (e.g. default templates per combination)?
