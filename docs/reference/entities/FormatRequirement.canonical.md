# FormatRequirement — Canonical Entity

STATUS: CANONICAL
Tier: 2 (App-only — Convex authors directly)
SOURCE: Promoted from Program-embedded nested shape — OQ-008 deferred promotion, Task D session
NOTE: Private operational data — no Compendium page.
VERSION: 1.0.0

---

## Purpose

FormatRequirement defines a specific formatting or structural requirement for research output submitted under a training Program. Format requirements are defined at the Program level and apply to all Projects running under that Program.

Examples:
- "Maximum word count: 15,000 words (excluding references and appendices)"
- "Reference format: Vancouver style, maximum 100 references"
- "File format: PDF, single-spaced, 12pt Times New Roman"
- "Required sections: Abstract (250 words), Introduction, Methods, Results, Discussion, Conclusion, References"

A Program references its format requirements via `format_requirement_codes[]`.

**Promotion rationale (OQ-008):** Promoted over KEEP_EMBEDDED because:
- Requirements are reused across Programs (e.g. word count rules shared by multiple fellowships)
- Requirements have their own versioning (college requirements change between cohorts)
- Independent FK resolution needed for submission validation tooling

---

## Source-of-Truth Fields

| Field | Type | Required | FK Target | Notes |
|---|---|---|---|---|
| `code` | string | yes | — | PK. UPPERCASE_SHORT. e.g. FMT-WORDCOUNT-15K, FMT-REF-VANCOUVER, FMT-SECTIONS-IMRaD. Immutable once in production. |
| `name` | string | yes | — | Requirement name (e.g. "Maximum Word Count 15,000") |
| `description` | string | yes | — | Full statement of the requirement. Should be actionable for a trainee. |
| `requirement_category` | enum | yes | — | `word_count \| reference_style \| file_format \| section_structure \| font_layout \| submission_format \| language \| other` |
| `applies_to_output_type` | string[] \| null | no | OutputType.code | Output types this requirement applies to. Null = all output types in the program. |
| `constraint_value` | string \| null | no | — | Machine-readable constraint for validation tooling (e.g. `"max:15000"`, `"style:vancouver"`, `"format:pdf"`). Nullable; free-form. |
| `is_mandatory` | boolean | yes | — | True if non-compliance fails submission; false if advisory. Default true. |
| `program_codes` | string[] \| null | no | Program.code | Programs that use this requirement. Reciprocal to Program.format_requirement_codes[]. P5 integrity enforced by format_requirement_integrity.py. |
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
| `applies_to_output_type[]` | many→many | OutputType | applies_to_output_type | Nullable |
| `program_codes[]` | many→many | Program | program_codes | Reciprocal to Program.format_requirement_codes[]; P5 enforced |

---

## Enum Reference

### `requirement_category`
| Value | Description |
|---|---|
| `word_count` | Word count limits or minimums (total, per-section, or per-component) |
| `reference_style` | Citation and reference list format (Vancouver, APA, AMA, etc.) |
| `file_format` | File type, compression, or delivery format requirements |
| `section_structure` | Required sections, headings, or ordering |
| `font_layout` | Typography, spacing, margin, and layout requirements |
| `submission_format` | Submission portal, cover sheet, or packaging requirements |
| `language` | Language, writing style, or readability requirements |
| `other` | Not categorised above |
