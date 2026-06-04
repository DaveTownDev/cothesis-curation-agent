# ResourceSubtype.book — Subtype-Specific Fields

STATUS: CANONICAL
Tier: 1 (Shared — Compendium produces, Convex clones)
PARENT_TYPE: book
INHERITS: Resource.canonical.md (universal base fields)
SOURCE: _task6_field_mapping_matrix.md

## Purpose
A book is a monograph, edited volume, or textbook — physical or digital — with bibliographic metadata including ISBN, edition, and structured cover/pricing information.

## Subtype-Specific Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `isbn_13` | string | No | ISBN-13 (preferred). |
| `isbn_10` | string | No | ISBN-10 (legacy; kept for lookup compatibility). |
| `edition` | string | No | Edition identifier e.g. `2nd`, `3rd revised`. Was: `edition_number`. |
| `chapter_count` | integer | No | Total number of chapters. |
| `has_ebook` | boolean | No | Whether an e-book version is available. |
| `ebook_url` | string (uri) | No | URL to purchase or access e-book version. |
| `series_name` | string | No | Book series name (if part of a series). |
| `dimensions` | string | No | Physical dimensions e.g. `234x156mm`. |
| `weight` | string | No | Physical weight e.g. `450g`. |
| `binding` | string | No | Binding type e.g. `hardcover`, `paperback`, `spiral`. |
| `cover_image_url` | string (uri) | No | Full-resolution cover image. Cluster F; canonical thumbnail_url is the standardised form. |
| `cover_image_small` | string (uri) | No | Small/thumbnail cover image (for card display). |
| `citation_count` | integer | No | Total citations (OpenAlex/CrossRef). |
| `openalex_id` | string | No | OpenAlex record ID. |
| `google_books_rating` | number | No | Google Books average rating. |
| `goodreads_rating` | number | No | Goodreads average rating. |
| `open_syllabus_score` | number | No | Open Syllabus appearance score (proxy for teaching use). |
| `previous_edition_adequate` | boolean | No | AI signal: whether a previous edition is adequate substitute. Stored on AIAssessment in practice; mirrored here as a subtype-specific signal. |
| `companion_url` | string (uri) | No | URL for companion website, supplements, or resources. |
| `has_companion_resources` | boolean | No | Whether companion resources exist. |
| `key_chapters` | string[] | No | AI-identified key chapter titles or numbers for trainees. |

## Notes

- Book also covers `book_chapter` as a sub-record type (~33 fields). Chapter-level fields (`chapter_title`, `chapter_authors`, `chapter_doi`, `start_page`, `end_page`) are stored as a nested object within type_fields when the resource represents a specific chapter.
- `previous_edition_adequate` is tagged as LLM-authored in the matrix — it surfaces on AIAssessment but is mirrored here as a book-specific signal field.
- Cluster F image aliases (`cover_image_url`, `cover_image_small`): canonical thumbnail is `thumbnail_url` on the Resource base; book-specific cover variants are kept here for display richness.
