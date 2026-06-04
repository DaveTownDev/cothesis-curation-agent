# CoThesis Compendium — Complete Field Mapping & Merge Logic: `book` + `book_chapter`

**Types:** Books & Textbooks (`book`) + Book Chapters (`book_chapter`)
**Version:** 1.0
**Date:** April 2026

**Book subtypes:** `textbook`, `handbook`, `edited_collection`, `open_textbook`, `style_guide`, `monograph`
**Book chapter:** No subtypes — inherits context from parent book

**Note:** Book and book_chapter are documented together because chapters inherit extensively from their parent book record and share most enrichment sources. The document clearly separates book-only fields, chapter-only fields, and shared fields.

---

## 1. Architecture

### Book Record

```
book_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── book_source_google_books
  │     ├── book_source_open_library
  │     ├── book_source_crossref
  │     ├── book_source_isbndb
  │     ├── book_source_springer_nature
  │     ├── book_source_openalex
  │     ├── book_source_doab
  │     ├── book_source_oapen
  │     ├── book_source_ncbi_bookshelf
  │     ├── book_source_librarything
  │     ├── book_source_opencitations
  │     ├── book_source_scrape_publisher
  │     ├── book_source_scrape_amazon
  │     ├── book_source_scrape_goodreads
  │     ├── book_source_open_syllabus
  │     ├── book_source_discovery
  │     └── book_ai_assessment
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (authors/editors)
  │     ├── publisher_entity_id
  │     ├── institution_entity_ids[] (for institutional OA textbooks)
  │     └── chapter_resource_ids[] (child book_chapter records)
  │
  ├── Cross-References
  │     ├── previous_edition_id (link to earlier edition book record)
  │     ├── companion_resource_ids[] (worked_examples, datasets from companion site)
  │     └── series_name (tag, not entity)
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

### Book Chapter Record

```
book_chapter_master (golden record)
  │
  ├── Source Sub-Records
  │     ├── chapter_source_crossref (if chapter has own DOI)
  │     ├── chapter_source_springer_nature (chapter-level metadata)
  │     ├── chapter_source_openalex (if indexed as a work)
  │     ├── chapter_source_scopus (chapter-level, if institutional access)
  │     ├── chapter_source_scrape_publisher (chapter page on publisher website)
  │     ├── chapter_source_google_books (TOC extraction)
  │     ├── chapter_source_discovery
  │     └── chapter_ai_assessment
  │
  ├── Inherited from Parent Book
  │     └── parent_book_id → book_master
  │
  ├── Secondary Entity Links
  │     ├── person_entity_ids[] (chapter authors — may differ from book authors)
  │     ├── publisher_entity_id (inherited from parent book)
  │     └── parent_book_id
  │
  └── Metadata
        ├── field_provenance
        ├── golden_record_version
        └── golden_record_hash
```

---

## 2. Source Trust Ranking

| Rank | Source | Code | Tier | Rate Limit | Free? | Rationale |
|------|--------|------|------|-----------|-------|-----------|
| 1 | Google Books API | `google_books` | T1 | 1K req/day | Yes (API key) | Broadest book coverage, structured metadata, TOC previews, cover images |
| 2 | CrossRef | `crossref` | T1 | 50 req/sec | Yes | Authoritative for books/chapters with DOIs — publisher-deposited metadata |
| 3 | Open Library | `open_library` | T1 | 1 req/sec | Yes | 20M+ books, cover images, open editions, community data |
| 4 | Springer Nature Meta API | `springer_nature` | T1 | 100 req/min (free key) | Yes (key required) | 14M+ documents including chapter-level metadata for Springer/BMC books |
| 5 | ISBNdb | `isbndb` | T1 | Plan-dependent | Paid ($15+/mo) | 109M+ books, most comprehensive ISBN-based metadata |
| 6 | OpenAlex | `openalex` | T1 | 100K credits/day | Yes (key) | Books and chapters as "works" — citation counts, author linking, OA status |
| 7 | DOAB | `doab` | T1 | Unknown | Yes | Authoritative registry for open access books |
| 8 | OAPEN | `oapen` | T1 | Standard OAI-PMH | Yes | Open access academic book metadata and full text |
| 9 | NCBI Bookshelf | `ncbi_bookshelf` | T1 | 10 req/sec (key) | Yes | Free medical/health textbooks — NLM curated |
| 10 | LibraryThing | `librarything` | T2 | Fair use | Yes (non-commercial) | Community tags, edition clustering (ThingISBN), related works |
| 11 | OpenCitations | `opencitations` | T2 | 180 req/min | Yes (CC0) | Open citation data for books with DOIs/ISBNs |
| 12 | Amazon | `scrape_amazon` | T2 | N/A (scrape) | Free (scrape) | Pricing, ratings, review count, "Also Bought" |
| 13 | Goodreads | `scrape_goodreads` | T2 | N/A (scrape) | Free (scrape) | Ratings, reviews, shelving data |
| 14 | OpenSyllabus | `open_syllabus` | T2 | Limited | Free (scrape) | Textbook adoption frequency across university syllabi |
| 15 | Publisher website | `scrape_publisher` | T1 | N/A (scrape) | Free | TOC, chapter listings, edition info, companion URL, pricing |
| 16 | Scopus | `scopus` | T2 | Variable | Paid (institutional) | Chapter-level indexing, citations — 150K+ books |
| 17 | Discovery record | `discovery` | — | N/A | N/A | Agent-provided |

**Enrichment tier assignments:**

| Enrichment Tier | Which Books | Sources Called |
|----------------|-------------|---------------|
| Tier 1 (every book) | All | Google Books, Open Library, CrossRef, OpenAlex, publisher scrape, AI assessment |
| Tier 2 (quality enrichment) | Textbooks, handbooks with DOIs | + ISBNdb, Springer Nature (if Springer pub), DOAB/OAPEN (if OA), OpenCitations, LibraryThing |
| Tier 3 (featured/badged) | Editor's Choice, Essential Reference | + Amazon, Goodreads, OpenSyllabus, Scopus |

---

## 3. Source Sub-Record Field Inventories

### 3.1 Google Books API (`book_source_google_books`)

**Lookup key:** ISBN-13, ISBN-10, title+author, or Google Books volume ID
**API endpoint:** `GET https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}` or `GET https://www.googleapis.com/books/v1/volumes/{volumeId}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `google_books_id` | `id` | String | Google Books volume ID |
| `self_link` | `selfLink` | String | API URL for this volume |
| `title` | `volumeInfo.title` | String | Book title |
| `subtitle` | `volumeInfo.subtitle` | String | Book subtitle |
| `authors` | `volumeInfo.authors[]` | Array[String] | Author/editor name list |
| `publisher` | `volumeInfo.publisher` | String | Publisher name |
| `published_date` | `volumeInfo.publishedDate` | String | Publication date (YYYY, YYYY-MM, or YYYY-MM-DD) |
| `description` | `volumeInfo.description` | String (HTML) | Publisher description/synopsis (HTML formatted) |
| `isbn_10` | `volumeInfo.industryIdentifiers[]` (type=ISBN_10) | String | ISBN-10 |
| `isbn_13` | `volumeInfo.industryIdentifiers[]` (type=ISBN_13) | String | ISBN-13 |
| `page_count` | `volumeInfo.pageCount` | Integer | Total pages |
| `print_type` | `volumeInfo.printType` | String | BOOK or MAGAZINE |
| `categories` | `volumeInfo.categories[]` | Array[String] | Subject categories (e.g., "Medical / Research") |
| `average_rating` | `volumeInfo.averageRating` | Float | Mean rating (1.0–5.0) |
| `ratings_count` | `volumeInfo.ratingsCount` | Integer | Number of ratings |
| `language` | `volumeInfo.language` | String | ISO 639-1 language code |
| `preview_link` | `volumeInfo.previewLink` | String | URL to Google Books preview |
| `info_link` | `volumeInfo.infoLink` | String | URL to Google Books info page |
| `canonical_volume_link` | `volumeInfo.canonicalVolumeLink` | String | Canonical URL |
| `thumbnail_small` | `volumeInfo.imageLinks.smallThumbnail` | String | Small cover image URL |
| `thumbnail` | `volumeInfo.imageLinks.thumbnail` | String | Standard cover image URL |
| `image_small` | `volumeInfo.imageLinks.small` | String | Small cover |
| `image_medium` | `volumeInfo.imageLinks.medium` | String | Medium cover |
| `image_large` | `volumeInfo.imageLinks.large` | String | Large cover |
| `image_extra_large` | `volumeInfo.imageLinks.extraLarge` | String | Extra large cover |
| `content_version` | `volumeInfo.contentVersion` | String | Content version string |
| `country` | `saleInfo.country` | String | Country for sale/access info |
| `saleability` | `saleInfo.saleability` | String | FOR_SALE, NOT_FOR_SALE, FREE |
| `is_ebook` | `saleInfo.isEbook` | Boolean | Whether available as ebook |
| `list_price_amount` | `saleInfo.listPrice.amount` | Float | List price |
| `list_price_currency` | `saleInfo.listPrice.currencyCode` | String | Price currency code |
| `retail_price_amount` | `saleInfo.retailPrice.amount` | Float | Retail/sale price |
| `retail_price_currency` | `saleInfo.retailPrice.currencyCode` | String | Retail price currency |
| `buy_link` | `saleInfo.buyLink` | String | Purchase URL |
| `viewability` | `accessInfo.viewability` | String | NO_PAGES, PARTIAL, ALL_PAGES |
| `public_domain` | `accessInfo.publicDomain` | Boolean | Whether in public domain |
| `epub_available` | `accessInfo.epub.isAvailable` | Boolean | Whether EPUB available |
| `pdf_available` | `accessInfo.pdf.isAvailable` | Boolean | Whether PDF available |
| `web_reader_link` | `accessInfo.webReaderLink` | String | URL to web reader |
| `text_snippet` | `searchInfo.textSnippet` | String | Text snippet from search match |

---

### 3.2 Open Library API (`book_source_open_library`)

**Lookup key:** ISBN, LCCN, OCLC, or Open Library ID
**API endpoint:** `GET https://openlibrary.org/isbn/{isbn}.json` or `GET https://openlibrary.org/works/{work_id}.json`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `open_library_id` | `key` | String | Open Library work/edition key (e.g., /works/OL12345W) |
| `title` | `title` | String | Book title |
| `subtitle` | `subtitle` | String | Subtitle |
| `authors` | `authors[].key` | Array[String] | Author keys (resolve via /authors/{key}.json) |
| `publishers` | `publishers[]` | Array[String] | Publisher name(s) |
| `publish_date` | `publish_date` | String | Publication date (various formats) |
| `number_of_pages` | `number_of_pages` | Integer | Page count |
| `isbn_10` | `isbn_10[]` | Array[String] | ISBN-10(s) |
| `isbn_13` | `isbn_13[]` | Array[String] | ISBN-13(s) |
| `lccn` | `lccn[]` | Array[String] | Library of Congress Control Numbers |
| `oclc_numbers` | `oclc_numbers[]` | Array[String] | OCLC numbers |
| `covers` | `covers[]` | Array[Integer] | Cover image IDs (use `https://covers.openlibrary.org/b/id/{id}-L.jpg`) |
| `subjects` | `subjects[]` | Array[String] | Subject headings |
| `subject_places` | `subject_places[]` | Array[String] | Geographic subjects |
| `subject_times` | `subject_times[]` | Array[String] | Temporal subjects |
| `subject_people` | `subject_people[]` | Array[String] | Person subjects |
| `description` | `description` (String or Object) | String/Object | Book description (may be `{type, value}` object) |
| `notes` | `notes` | String/Object | Additional notes |
| `table_of_contents` | `table_of_contents[]` | Array[Object] | TOC entries: `{level, label, title, pagenum}` |
| `series` | `series[]` | Array[String] | Series name(s) |
| `edition_name` | `edition_name` | String | Edition identifier (e.g., "4th ed.") |
| `physical_format` | `physical_format` | String | Hardcover, Paperback, etc. |
| `weight` | `weight` | String | Physical weight |
| `languages` | `languages[].key` | Array[String] | Language keys |
| `classifications` | `classifications` | Object | Various classification systems (Dewey, LC) |
| `links` | `links[]` | Array[Object] | External links `{url, title}` |
| `created` | `created.value` | DateTime | Record creation date |
| `last_modified` | `last_modified.value` | DateTime | Last modification date |

**Open Library Author endpoint** (`GET https://openlibrary.org/authors/{key}.json`):

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `author_name` | `name` | String | Author name |
| `personal_name` | `personal_name` | String | Personal name variant |
| `birth_date` | `birth_date` | String | Birth date |
| `death_date` | `death_date` | String | Death date |
| `bio` | `bio` | String/Object | Biography |
| `alternate_names` | `alternate_names[]` | Array[String] | Name variants |
| `links` | `links[]` | Array[Object] | External links (Wikipedia, etc.) |
| `photos` | `photos[]` | Array[Integer] | Photo IDs |

---

### 3.3 CrossRef (`book_source_crossref`)

**Lookup key:** DOI (if book has a DOI) or ISBN (via filter)
**API endpoint:** `GET https://api.crossref.org/works/{doi}` or `GET https://api.crossref.org/works?filter=isbn:{isbn}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `doi` | `message.DOI` | String | Book DOI |
| `title` | `message.title[0]` | String | Book title |
| `subtitle` | `message.subtitle[0]` | String | Subtitle |
| `type` | `message.type` | String | `book`, `edited-book`, `monograph`, `reference-book` |
| `publisher` | `message.publisher` | String | Publisher |
| `isbn` | `message.ISBN[]` | Array[String] | ISBNs (print and electronic) |
| `authors` | `message.author[]` | Array[Object] | Authors/editors (same structure as article) |
| `editors` | `message.editor[]` | Array[Object] | Editors (separate from authors) |
| `published_print_date` | `message.published-print.date-parts[0]` | Array[Int] | Print publication date |
| `published_online_date` | `message.published-online.date-parts[0]` | Array[Int] | Online publication date |
| `citation_count` | `message.is-referenced-by-count` | Integer | Citations |
| `reference_count` | `message.references-count` | Integer | References |
| `subject` | `message.subject[]` | Array[String] | Subjects |
| `language` | `message.language` | String | Language |
| `license` | `message.license[]` | Array[Object] | License info |
| `url` | `message.URL` | String | DOI URL |
| `resource_url` | `message.resource.primary.URL` | String | Publisher URL |
| `funder` | `message.funder[]` | Array[Object] | Funding bodies |
| `edition_number` | `message.edition-number` | String | Edition |
| `page` | `message.page` | String | Total pages |

---

### 3.4 ISBNdb (`book_source_isbndb`)

**Lookup key:** ISBN-13
**API endpoint:** `GET https://api2.isbndb.com/book/{isbn}` (requires paid API key)

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `title` | `book.title` | String | Title |
| `title_long` | `book.title_long` | String | Full title including subtitle |
| `isbn` | `book.isbn` | String | ISBN-10 |
| `isbn13` | `book.isbn13` | String | ISBN-13 |
| `authors` | `book.authors[]` | Array[String] | Author names |
| `publisher` | `book.publisher` | String | Publisher |
| `edition` | `book.edition` | String | Edition |
| `binding` | `book.binding` | String | Hardcover, Paperback, etc. |
| `pages` | `book.pages` | Integer | Page count |
| `language` | `book.language` | String | Language |
| `date_published` | `book.date_published` | String | Publication date |
| `dimensions` | `book.dimensions` | String | Physical dimensions |
| `dimensions_structured` | `book.dimensions_structured` | Object | `{length, width, height, weight}` with units |
| `image` | `book.image` | String | Cover image URL |
| `msrp` | `book.msrp` | Float | Manufacturer's suggested retail price |
| `subjects` | `book.subjects[]` | Array[String] | Subject classifications |
| `synopsis` | `book.synopsis` | String | Book synopsis |
| `overview` | `book.overview` | String | Book overview |
| `dewey_decimal` | `book.dewey_decimal` | String | Dewey Decimal number |
| `related` | `book.related` | Object | Related ISBNs (other editions) |
| `other_isbns` | `book.other_isbns[]` | Array[Object] | Other edition ISBNs with binding type |

---

### 3.5 Springer Nature Meta API (`book_source_springer_nature`)

**Lookup key:** ISBN or DOI
**API endpoint:** `GET https://api.springernature.com/meta/v2/json?q=isbn:{isbn}&api_key={key}`
**Note:** Returns both book-level and chapter-level records. Filter by `contentType` to distinguish.

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `identifier` | `records[].identifier` | String | DOI (e.g., "doi:10.1007/978-3-031-63498-7") |
| `content_type` | `records[].contentType` | String | `Book`, `Chapter`, `Article` |
| `title` | `records[].title` | String | Book or chapter title |
| `creators` | `records[].creators[].creator` | Array[String] | Author names |
| `publication_name` | `records[].publicationName` | String | Book title (for chapters, this is the parent book) |
| `isbn` | `records[].isbn` | String | Print ISBN |
| `electronic_isbn` | `records[].electronicIsbn` | String | Electronic ISBN |
| `issn` | `records[].issn` | String | ISSN (for book series) |
| `doi` | `records[].doi` | String | DOI |
| `publisher` | `records[].publisher` | String | Publisher |
| `publication_date` | `records[].publicationDate` | String | Publication date |
| `online_date` | `records[].onlineDate` | String | Online publication date |
| `print_date` | `records[].printDate` | String | Print date |
| `volume` | `records[].volume` | String | Volume number |
| `number` | `records[].number` | String | Issue/chapter number |
| `starting_page` | `records[].startingPage` | String | Starting page |
| `ending_page` | `records[].endingPage` | String | Ending page |
| `open_access` | `records[].openaccess` | String | "true" or "false" |
| `abstract` | `records[].abstract` | String | Abstract |
| `subjects` | `records[].subjects[]` | Array[String] | Subject classifications |
| `urls` | `records[].url[].value` | Array[Object] | URLs with format types |
| `copyright` | `records[].copyright` | String | Copyright holder |

**Chapter-level records** share the same structure but have `contentType: "Chapter"` and include `startingPage`/`endingPage` and chapter-specific `title`/`creators`.

---

### 3.6 OpenAlex (`book_source_openalex`)

**Lookup key:** DOI, ISBN (via filter), or OpenAlex ID
**API endpoint:** `GET https://api.openalex.org/works?filter=doi:{doi}` or `filter=isbn:{isbn}`

| Field | JSON Path | Data Type | Description |
|-------|-----------|-----------|-------------|
| `openalex_id` | `id` | String | OpenAlex work ID |
| `doi` | `doi` | String | DOI |
| `title` | `title` | String | Title |
| `publication_date` | `publication_date` | Date | Publication date |
| `publication_year` | `publication_year` | Integer | Year |
| `type` | `type` | String | `book`, `book-chapter`, etc. |
| `is_oa` | `open_access.is_oa` | Boolean | Whether OA |
| `oa_status` | `open_access.oa_status` | String | OA status |
| `oa_url` | `open_access.oa_url` | String | Best OA URL |
| `cited_by_count` | `cited_by_count` | Integer | Citation count |
| `fwci` | `fwci` | Float | Field-weighted citation impact |
| `authorships` | `authorships[]` | Array[Object] | Authors with institutions (same structure as article) |
| `topics` | `topics[]` | Array[Object] | Topic assignments |
| `referenced_works` | `referenced_works[]` | Array[String] | Cited works |
| `related_works` | `related_works[]` | Array[String] | Related works |
| `language` | `language` | String | ISO language code |
| `primary_location` | `primary_location` | Object | Source, license, landing page |
| `locations` | `locations[]` | Array[Object] | All available locations |

---

### 3.7 DOAB (`book_source_doab`)

**Lookup key:** ISBN or DOAB record ID
**API endpoint:** DOAB API or OAI-PMH harvest
**Coverage:** Open access academic books only

| Field | Type | Description |
|-------|------|-------------|
| `doab_id` | String | DOAB record identifier |
| `title` | String | Book title |
| `authors` | Array[String] | Author names |
| `publisher` | String | Publisher |
| `isbn` | Array[String] | ISBNs |
| `doi` | String | DOI |
| `language` | String | Language |
| `subjects` | Array[String] | Subject classifications |
| `description` | Text | Description |
| `license` | String | License (CC-BY, CC-BY-NC, etc.) |
| `download_url` | String | Direct download URL |
| `year` | Integer | Publication year |
| `pages` | Integer | Page count |
| `doab_url` | String | DOAB record URL |

---

### 3.8 OAPEN (`book_source_oapen`)

**Lookup key:** ISBN or DOI
**Access:** OAI-PMH endpoint or REST API
**Coverage:** Open access academic books

| Field | Type | Description |
|-------|------|-------------|
| `oapen_id` | String | OAPEN handle |
| `title` | String | Book title |
| `authors` | Array[String] | Authors |
| `publisher` | String | Publisher |
| `isbn` | Array[String] | ISBNs |
| `doi` | String | DOI |
| `language` | String | Language |
| `subjects` | Array[String] | Subjects |
| `description` | Text | Description |
| `license` | String | License |
| `download_url` | String | Full text download URL |
| `format` | String | PDF, EPUB, etc. |
| `year` | Integer | Publication year |
| `pages` | Integer | Page count |
| `collection` | String | OAPEN collection |
| `grant_info` | Object | Funding information |

---

### 3.9 NCBI Bookshelf (`book_source_ncbi_bookshelf`)

**Lookup key:** Bookshelf ID or search
**API endpoint:** NCBI E-utilities (`esearch` + `efetch` with `db=books`)
**Coverage:** Free medical/health textbooks on NCBI

| Field | Type | Description |
|-------|------|-------------|
| `bookshelf_id` | String | NCBI Bookshelf ID |
| `title` | String | Book title |
| `authors` | Array[String] | Authors/editors |
| `publisher` | String | Publisher |
| `year` | Integer | Publication year |
| `isbn` | String | ISBN if available |
| `pmid` | String | PMID if available |
| `abstract` | Text | Summary/abstract |
| `toc` | Array[Object] | Table of contents with chapter titles and IDs |
| `full_text_url` | String | URL to full text on Bookshelf |
| `sections` | Array[Object] | Book sections/parts structure |
| `copyright` | String | Copyright statement |

---

### 3.10 LibraryThing (`book_source_librarything`)

**Lookup key:** ISBN
**API endpoint:** `GET https://www.librarything.com/services/rest/1.1/?method=librarything.ck.getwork&isbn={isbn}&apikey={key}`
**Note:** Also provides ThingISBN for edition clustering

| Field | Type | Description |
|-------|------|-------------|
| `librarything_work_id` | String | LibraryThing work ID |
| `title` | String | Title |
| `author` | String | Author |
| `rating` | Float | Community average rating |
| `rating_count` | Integer | Number of ratings |
| `review_count` | Integer | Number of reviews |
| `tags` | Array[Object] | Community-generated tags with counts |
| `related_isbns` | Array[String] | ThingISBN — all ISBNs for all editions of this work |
| `common_knowledge` | Object | Series, original publication date, canonical title, awards |

---

### 3.11 OpenCitations (`book_source_opencitations`)

**Lookup key:** DOI or ISBN
**API endpoint:** `GET https://opencitations.net/index/coci/api/v1/citations/{doi}`

| Field | Type | Description |
|-------|------|-------------|
| `citation_count` | Integer | Number of open citations |
| `citations` | Array[Object] | Citing work DOIs with dates |
| `references` | Array[Object] | Referenced work DOIs |

---

### 3.12 Publisher Website Scrape (`book_source_scrape_publisher`)

**Source:** Publisher catalogue page for this book

| Field | Type | Description |
|-------|------|-------------|
| `publisher_url` | String | Publisher's page for this book |
| `current_price` | Float | Current retail price |
| `price_currency` | String | Currency code |
| `edition` | String | Edition statement |
| `edition_number` | Integer | Numeric edition (e.g., 4) |
| `format_available` | Array[String] | Hardcover, paperback, ebook, online |
| `table_of_contents` | Array[Object] | Chapter titles, authors (for edited collections), page ranges |
| `companion_url` | String | URL to companion website with supplementary resources |
| `series_name` | String | Series name (e.g., "Oxford Handbooks") |
| `series_url` | String | URL to series page |
| `related_titles` | Array[Object] | Publisher's "related books" suggestions |
| `publication_date` | String | Publication date from publisher |
| `available_formats` | Array[Object] | Format, ISBN, price for each format |
| `imprint` | String | Publisher imprint |

---

### 3.13 Amazon Scrape (`book_source_scrape_amazon`)

**Source:** Amazon product page (scrape — respect robots.txt)

| Field | Type | Description |
|-------|------|-------------|
| `amazon_url` | String | Amazon product URL |
| `amazon_asin` | String | Amazon Standard Identification Number |
| `amazon_rating` | Float | Average rating (1–5) |
| `amazon_rating_count` | Integer | Number of ratings |
| `amazon_review_count` | Integer | Number of text reviews |
| `amazon_price` | Float | Current Amazon price |
| `amazon_price_currency` | String | Currency |
| `amazon_bestseller_rank` | Object | Bestseller rank in categories |
| `customers_also_bought` | Array[String] | ASINs of "Customers Also Bought" books |
| `format_options` | Array[Object] | Available formats with prices (Kindle, Hardcover, Paperback) |

---

### 3.14 Goodreads Scrape (`book_source_scrape_goodreads`)

**Source:** Goodreads book page (scrape)

| Field | Type | Description |
|-------|------|-------------|
| `goodreads_url` | String | Goodreads page URL |
| `goodreads_id` | String | Goodreads book ID |
| `goodreads_rating` | Float | Average rating (1–5) |
| `goodreads_rating_count` | Integer | Number of ratings |
| `goodreads_review_count` | Integer | Number of text reviews |
| `goodreads_shelves` | Array[Object] | Most common shelves with counts (e.g., "statistics": 234, "research-methods": 189) |

---

### 3.15 OpenSyllabus (`book_source_open_syllabus`)

**Source:** OpenSyllabus.org (scrape or API if available)

| Field | Type | Description |
|-------|------|-------------|
| `open_syllabus_score` | Float | OpenSyllabus teaching score |
| `syllabus_count` | Integer | Number of university syllabi featuring this book |
| `top_institutions` | Array[String] | Institutions most frequently assigning this book |
| `top_fields` | Array[String] | Academic fields where most assigned |

---

### 3.16 Discovery Record (`book_source_discovery`)

Same structure as article discovery record.

| Field | Type | Description |
|-------|------|-------------|
| `discovered_url` | String | URL where book was found |
| `discovered_at` | DateTime | When discovered |
| `discovered_by` | String | Agent name or "manual" |
| `discovery_source_name` | String | Source website/database name |
| `discovery_source_url` | String | URL of discovery page |
| `discovery_context` | Text | How the source described this book |
| `agent_assigned_type` | String | Resource type from 46-type list |
| `agent_description` | Text | Agent-written description |
| `agent_methodology_relevance` | Text | Methodology relevance assessment |
| `agent_access_type` | String | free, freemium, paid, subscription, institutional |

---

### 3.17 AI Assessment Record (`book_ai_assessment`)

Same structure as article AI assessment.

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Overall quality score |
| `quality_dimensions` | Object | `{authority, currency, relevance, accuracy, pedagogy}` |
| `confidence` | Float (0–1) | AI confidence |
| `methodology_tags` | Array[String] | From 162-methodology taxonomy |
| `thesis_stages` | Array[String] | THESIS stage tags |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `specialty_tags` | Array[String] | Medical specialty relevance |
| `subtype_classification` | String | textbook, handbook, edited_collection, open_textbook, style_guide, monograph |
| `editorial_description` | Text | Original 1–2 sentence description |
| `editorial_description_long` | Text | Extended 3–5 sentence description |
| `editorial_badges` | Array[String] | Recommended badges (max 3) |
| `key_chapters` | Array[Object] | AI-identified key chapters with methodology relevance: `{chapter, title, relevant_for}` |
| `previous_edition_adequate` | Boolean | Whether an older/cheaper edition covers the same content |
| `assessed_at` | DateTime | Assessment timestamp |
| `model_used` | String | AI model identifier |
| `requires_human_review` | Boolean | Below confidence threshold |

---

## 4. Book Chapter Source Sub-Records

### 4.1 CrossRef — Chapter Level (`chapter_source_crossref`)

Only available for chapters with their own DOI. Same field structure as `book_source_crossref` but with `type: "book-chapter"`.

**Additional chapter-specific fields:**

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `container_title` | `message.container-title[0]` | String | Parent book title |
| `page` | `message.page` | String | Chapter page range |
| `chapter_number` | `message.chapter-number` | String | Chapter number |

---

### 4.2 Springer Nature — Chapter Level (`chapter_source_springer_nature`)

Same API as book-level but filtered to `contentType: "Chapter"`.

| Field | JSON Path | Type | Description |
|-------|-----------|------|-------------|
| `identifier` | `records[].identifier` | String | Chapter DOI |
| `title` | `records[].title` | String | Chapter title |
| `creators` | `records[].creators[].creator` | Array[String] | Chapter authors |
| `publication_name` | `records[].publicationName` | String | Parent book title |
| `starting_page` | `records[].startingPage` | String | Start page |
| `ending_page` | `records[].endingPage` | String | End page |
| `abstract` | `records[].abstract` | String | Chapter abstract |
| `doi` | `records[].doi` | String | Chapter DOI |
| `subjects` | `records[].subjects[]` | Array[String] | Chapter subjects |

---

### 4.3 OpenAlex — Chapter Level (`chapter_source_openalex`)

Same API as book-level. Chapters indexed as `type: "book-chapter"`.

Fields identical to book_source_openalex but represent the chapter, not the whole book. Citation count, authorships, topics are chapter-specific.

---

### 4.4 Scopus — Chapter Level (`chapter_source_scopus`)

**Requires:** Institutional API access (Elsevier Developer Portal)

| Field | Type | Description |
|-------|------|-------------|
| `scopus_id` | String | Scopus document ID |
| `eid` | String | Scopus EID |
| `title` | String | Chapter title |
| `authors` | Array[Object] | Chapter authors with Scopus author IDs |
| `abstract` | Text | Chapter abstract |
| `citation_count` | Integer | Chapter citation count |
| `page_range` | String | Page range |
| `doi` | String | Chapter DOI |
| `affiliation` | Array[Object] | Author affiliations |
| `subject_areas` | Array[Object] | Scopus subject area classifications |

---

### 4.5 Publisher Website — Chapter Page (`chapter_source_scrape_publisher`)

| Field | Type | Description |
|-------|------|-------------|
| `chapter_url` | String | Publisher's page for this chapter |
| `chapter_title` | String | Chapter title |
| `chapter_number` | String | Chapter number/identifier |
| `chapter_authors` | Array[String] | Chapter-specific authors |
| `page_start` | Integer | Starting page |
| `page_end` | Integer | Ending page |
| `abstract` | Text | Chapter abstract |
| `has_preview` | Boolean | Whether chapter preview is available |

---

### 4.6 Google Books TOC Extraction (`chapter_source_google_books`)

| Field | Type | Description |
|-------|------|-------------|
| `chapter_title` | String | Chapter title from TOC |
| `page_number` | Integer | Page number from TOC |
| `toc_position` | Integer | Position in table of contents |

**Note:** Google Books TOC extraction is limited — not all books have digitized TOCs. Best for confirming chapter existence and page numbers, not for rich metadata.

---

### 4.7 Chapter AI Assessment (`chapter_ai_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | Float (0–1) | Chapter quality |
| `quality_dimensions` | Object | `{authority, currency, relevance, accuracy, pedagogy}` |
| `confidence` | Float (0–1) | AI confidence |
| `methodology_tags` | Array[String] | Methodology tags (narrower than parent book) |
| `thesis_stages` | Array[String] | THESIS stages |
| `difficulty_level` | String | beginner, intermediate, advanced |
| `editorial_description` | Text | What this chapter covers and why it's useful |
| `assessed_at` | DateTime | Assessment timestamp |
| `model_used` | String | AI model |
| `requires_human_review` | Boolean | Below threshold |

---

## 5. Secondary Entity Links

### 5.1 Person (Author/Editor)

**Relationship:** `book -[AUTHORED_BY {role}]-> person` where role = `author` or `editor`
**Cardinality:** Many-to-many
**Resolution:** Match via ORCID (if available in CrossRef/OpenAlex data), then name + publisher fuzzy match.
**Book-specific relationship fields:**
- `role`: `author`, `editor`, `chapter_author` (for edited collections)
- `contribution_type`: sole_author, co_author, editor, chapter_contributor

### 5.2 Publisher

**Relationship:** `book -[PUBLISHED_BY]-> publisher`
**Cardinality:** Many-to-one
**Resolution:** Match via CrossRef member ID, or publisher name fuzzy match.
**Entity data sources:** CrossRef Members API, OpenAlex Publishers, publisher website scrape

### 5.3 Institution (for institutional OA textbooks)

**Relationship:** `book -[PRODUCED_BY]-> institution`
**Cardinality:** Many-to-one (optional — only for institutional publications like WHO manuals, university press OA texts)
**Resolution:** Via ROR from OpenAlex or publisher name match

### 5.4 Book → Chapter Relationship

**Relationship:** `book_chapter -[PART_OF]-> book` and `book -[CONTAINS]-> book_chapter`
**Cardinality:** One-to-many (one book has many chapters)
**Fields on relationship:** `chapter_number`, `position_in_toc`

---

## 6. Golden Record Merge Rules — Book

### 6.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `isbn_13` | String | V | ISBNdb → Google Books → CrossRef → Open Library → Springer Nature | Primary identifier. Normalise to 13-digit format. |
| `isbn_10` | String | V | ISBNdb → Google Books → Open Library | Derive from ISBN-13 if absent. |
| `doi` | String | V | CrossRef → Springer Nature → OpenAlex | Many books lack DOIs — null is acceptable. |
| `google_books_id` | String | V | Google Books | Single source. |
| `open_library_id` | String | V | Open Library | Single source. |
| `openalex_id` | String | V | OpenAlex | Single source. |
| `isbndb_id` | String | V | ISBNdb | Single source. |
| `doab_id` | String | V | DOAB | Single source (OA books only). |
| `ncbi_bookshelf_id` | String | V | NCBI Bookshelf | Single source (free medical texts only). |
| `url` | String | D | Derived | Publisher URL (from scrape) → DOI URL → Google Books URL → Open Library URL. |

### 6.2 Bibliographic Core

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `title` | String | V | ISBNdb (`title_long`) → Google Books → CrossRef → Open Library → Springer Nature | Use longest non-null title (ISBNdb `title_long` includes subtitle). |
| `subtitle` | String | V | Google Books → CrossRef → Open Library | First non-null. |
| `authors` | Array[String] | D | Merge CrossRef `author[]` + Google Books `authors[]` + Open Library (resolved) + ISBNdb | Deduplicate by name similarity. CrossRef provides structured given/family; Google Books provides display names. |
| `editors` | Array[String] | V | CrossRef `editor[]` → scrape_publisher | CrossRef distinguishes authors from editors. |
| `publisher` | String | V | CrossRef → ISBNdb → Google Books → Open Library → Springer Nature | CrossRef is publisher-deposited. |
| `publisher_entity_id` | String | D | Resolved via publisher name match to Publisher entity | |
| `publication_date` | Date | D | Derived | CrossRef `published-print` → Google Books `publishedDate` → ISBNdb `date_published` → Open Library `publish_date`. Normalise to ISO 8601. |
| `publication_date_precision` | String | D | Derived | `day`, `month`, or `year`. |
| `publication_year` | Integer | D | Derived from `publication_date` | |
| `edition` | String | V | CrossRef `edition-number` → ISBNdb `edition` → scrape_publisher → Open Library `edition_name` | |
| `edition_number` | Integer | D | Derived | Parse numeric from edition string (e.g., "4th Edition" → 4). |
| `page_count` | Integer | V | ISBNdb → Google Books → Open Library → Springer Nature | First non-null. |
| `language` | String | V | Google Books → CrossRef → Open Library → ISBNdb | Normalise to ISO 639-1. |
| `description` | Text | V | Google Books (strip HTML) → ISBNdb `synopsis` → Open Library → DOAB | Strip HTML tags from Google Books. **Note: this is the publisher description — the editorial_description is AI-authored and different.** |
| `table_of_contents` | Array[Object] | V | scrape_publisher → Open Library `table_of_contents` → Google Books (TOC from preview) | Publisher scrape is richest (has authors for edited collections). |

### 6.3 Physical & Format

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `binding` | String | V | ISBNdb → scrape_publisher | Hardcover, Paperback, etc. |
| `formats_available` | Array[Object] | D | Merge scrape_publisher `available_formats` + ISBNdb `other_isbns` + Google Books `epub/pdf` flags | Each: `{format, isbn, price, currency}`. |
| `is_ebook_available` | Boolean | D | Derived | `true` if any format is ebook/epub/pdf. |
| `dimensions` | Object | V | ISBNdb `dimensions_structured` | Physical dimensions with units. |

### 6.4 Cover Images

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `cover_image_url` | String | D | Derived | ISBNdb `image` → Google Books `imageLinks.large` → Open Library `covers` (construct URL) → OAPEN. **Choose highest resolution available.** |
| `cover_image_small` | String | V | Google Books `imageLinks.thumbnail` → Open Library (small) | For card display. |
| `cover_image_large` | String | V | Google Books `imageLinks.extraLarge` → ISBNdb `image` → Open Library (large) | For detail page. |

### 6.5 Pricing

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `price` | Float | V | scrape_publisher → Google Books `retailPrice` → ISBNdb `msrp` → scrape_amazon | Use publisher price as primary; Amazon as fallback. |
| `price_currency` | String | V | Same as price source | |
| `amazon_price` | Float | V | scrape_amazon | Separate field for comparison. |
| `is_free` | Boolean | D | Derived | `true` if DOAB/OAPEN/NCBI Bookshelf record exists OR Google Books `saleability == "FREE"` OR `publicDomain == true`. |

### 6.6 Ratings & Adoption

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `goodreads_rating` | Float | V | scrape_goodreads | |
| `goodreads_rating_count` | Integer | V | scrape_goodreads | |
| `amazon_rating` | Float | V | scrape_amazon | |
| `amazon_rating_count` | Integer | V | scrape_amazon | |
| `google_books_rating` | Float | V | Google Books `averageRating` | |
| `google_books_rating_count` | Integer | V | Google Books `ratingsCount` | |
| `librarything_rating` | Float | V | LibraryThing | |
| `librarything_tags` | Array[Object] | V | LibraryThing `tags` | Community tags with counts. |
| `open_syllabus_score` | Float | V | OpenSyllabus | Teaching adoption score. |
| `syllabus_count` | Integer | V | OpenSyllabus | Number of syllabi featuring this book. |

### 6.7 Citation Metrics

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `citation_count` | Integer | V | OpenAlex `cited_by_count` | Priority source. |
| `citation_count_max` | Integer | D | max(OpenAlex, CrossRef, OpenCitations) | Store with source. |
| `citation_count_max_source` | String | D | Whichever provided max | |
| `fwci` | Float | V | OpenAlex | If available. |

### 6.8 Open Access

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `is_open_access` | Boolean | D | Derived | `true` if DOAB record exists OR OAPEN record exists OR NCBI Bookshelf record exists OR OpenAlex `is_oa` OR Google Books `publicDomain`. |
| `oa_status` | String | V | OpenAlex → DOAB (presence = gold) | |
| `oa_download_url` | String | V | DOAB → OAPEN → NCBI Bookshelf → OpenAlex | Direct download link for OA books. |
| `oa_format` | String | V | DOAB → OAPEN | PDF, EPUB, HTML. |
| `oa_license` | String | V | DOAB → OAPEN → OpenAlex | CC-BY, CC-BY-NC, etc. |

### 6.9 Subjects & Classification

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `subjects` | Array[String] | D | Merge Google Books `categories` + ISBNdb `subjects` + Open Library `subjects` + CrossRef `subject` + DOAB `subjects` + Springer Nature `subjects` | Deduplicate, normalise casing. |
| `dewey_decimal` | String | V | ISBNdb → Open Library `classifications.dewey_decimal_class` | |
| `topics_openalex` | Array[Object] | V | OpenAlex `topics` | OpenAlex topic assignments with scores. |

### 6.10 Series & Editions

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `series_name` | String | V | scrape_publisher → Open Library `series` → Springer Nature `issn` context | Tag field, not entity. |
| `related_isbns` | Array[String] | V | LibraryThing ThingISBN → ISBNdb `other_isbns` | All ISBNs for all editions/formats. Used for edition clustering. |
| `previous_edition_id` | String | D | Entity resolution | Link to earlier edition book record in directory (if it exists). |
| `previous_edition_adequate` | Boolean | L | AI Assessment | Whether older/cheaper edition covers the same content. |

### 6.11 Companion Resources

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `companion_url` | String | V | scrape_publisher | URL to companion website. |
| `has_companion_resources` | Boolean | D | Derived | `true` if `companion_url` is non-null. |
| `companion_resource_ids` | Array[String] | D | Entity resolution | Links to worked_example, dataset, video_tutorial resources discovered from companion site. |

### 6.12 LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Generation Notes |
|-------------|------|-----|--------------|-----------------|
| `editorial_description` | Text (1–2 sentences) | L | Title, authors, publisher, subjects, edition, description | Original. Never copy publisher description. Written for medical trainee audience. E.g., "The definitive handbook for systematic review methodology, updated to its 6th edition. Covers everything from protocol writing to meta-analysis interpretation." |
| `editorial_description_long` | Text (3–5 sentences) | L | All source data | Extended description for detail page. |
| `methodology_tags` | Array[String] | L | Title, subjects, TOC, description | From 162-methodology taxonomy. |
| `thesis_stages` | Array[String] | L | Content analysis | THESIS stage tags. |
| `difficulty_level` | String | L | Publisher, content depth, target audience | beginner, intermediate, advanced. |
| `specialty_tags` | Array[String] | L | Subjects, description | Medical specialty relevance. |
| `article_subtype` | String | L | Content analysis | textbook, handbook, edited_collection, open_textbook, style_guide, monograph. |
| `editorial_badges` | Array[String] | L | Quality, ratings, OA status, adoption | Max 3. AI recommends, human confirms. |
| `quality_score` | Float (0–1) | L | All source data | Multi-dimensional: authority, currency, relevance, accuracy, pedagogy. |
| `quality_dimensions` | Object | L | All source data | `{authority, currency, relevance, accuracy, pedagogy}` |
| `key_chapters` | Array[Object] | L | TOC + methodology analysis | `{chapter_number, title, relevant_for_methodology}` — which chapters are most relevant. |
| `previous_edition_adequate` | Boolean | L | Edition history, publication dates | Whether an older/cheaper edition covers essentially the same content. |

### 6.13 Entity Links

| Golden Field | Type | Cat | Merge Rule |
|-------------|------|-----|------------|
| `author_entity_ids` | Array[String] | D | Entity resolution via ORCID → name match to Person entity. |
| `editor_entity_ids` | Array[String] | D | Same resolution for editors. |
| `publisher_entity_id` | String | D | CrossRef member ID → publisher name match to Publisher entity. |
| `institution_entity_ids` | Array[String] | D | For institutional OA texts — match via ROR. |
| `chapter_resource_ids` | Array[String] | D | IDs of child book_chapter records in the directory. |

---

## 7. Golden Record Merge Rules — Book Chapter

Book chapters inherit many fields from their parent book. The merge rules below only cover chapter-specific fields and inherited field overrides.

### 7.1 Identifiers

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `doi` | String | V | CrossRef → Springer Nature → OpenAlex | Many chapters lack DOIs. Null is acceptable. |
| `parent_book_id` | String | D | Internal | Link to parent book record. |
| `parent_book_isbn` | String | D | Inherited from parent book | |
| `openalex_id` | String | V | OpenAlex | Single source. |
| `scopus_id` | String | V | Scopus | Single source (if institutional access). |

### 7.2 Chapter-Specific Bibliographic

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `chapter_title` | String | V | Springer Nature → CrossRef → scrape_publisher → Google Books TOC | First non-null. |
| `chapter_number` | String | V | CrossRef `chapter-number` → scrape_publisher → Google Books TOC position | |
| `chapter_authors` | Array[String] | V | CrossRef `author[]` → Springer Nature `creators` → scrape_publisher → OpenAlex `authorships` | Chapter authors may differ from book authors (especially in edited collections). |
| `page_start` | Integer | V | Springer Nature `startingPage` → CrossRef `page` (parse) → scrape_publisher | |
| `page_end` | Integer | V | Springer Nature `endingPage` → CrossRef `page` (parse) → scrape_publisher | |
| `page_count` | Integer | D | Derived | `page_end - page_start + 1`. |
| `abstract` | Text | V | Springer Nature `abstract` → CrossRef `abstract` → Scopus `abstract` | Many chapters lack abstracts. |

### 7.3 Inherited from Parent Book

These fields are copied from the parent book record, not sourced independently:

| Golden Field | Source | Notes |
|-------------|--------|-------|
| `parent_book_title` | Parent book `title` | Denormalised for display. |
| `parent_book_authors` | Parent book `authors` | For attribution. |
| `publisher` | Parent book `publisher` | |
| `publisher_entity_id` | Parent book `publisher_entity_id` | |
| `publication_date` | Parent book `publication_date` | |
| `publication_year` | Parent book `publication_year` | |
| `isbn_13` | Parent book `isbn_13` | |
| `edition` | Parent book `edition` | |
| `cover_image_url` | Parent book `cover_image_url` | Same cover as parent book. |
| `price` | Parent book `price` | Book-level price (chapter not sold separately unless ebook). |
| `is_open_access` | Parent book `is_open_access` | |
| `language` | Parent book `language` | |

### 7.4 Chapter Citation Metrics

| Golden Field | Type | Cat | Source Priority | Merge Rule |
|-------------|------|-----|----------------|------------|
| `citation_count` | Integer | V | OpenAlex → Scopus → OpenCitations | Chapter-specific citations (not book-level). |
| `citation_count_max` | Integer | D | max across sources | |
| `citation_count_max_source` | String | D | Whichever provided max | |

### 7.5 Chapter LLM-Authored Fields

| Golden Field | Type | Cat | Input Sources | Notes |
|-------------|------|-----|--------------|-------|
| `editorial_description` | Text | L | Chapter title, abstract, parent book context, methodology | What this chapter covers and why a trainee should read it specifically. |
| `methodology_tags` | Array[String] | L | Chapter title, abstract | Narrower than parent book tags. |
| `thesis_stages` | Array[String] | L | Content analysis | |
| `difficulty_level` | String | L | Content depth | |
| `quality_score` | Float (0–1) | L | All chapter data + parent book quality | |
| `author_entity_ids` | Array[String] | D | Entity resolution | Chapter authors linked to Person entities. |

---

## 8. Field Provenance

Same structure as article type. Every golden record carries a `field_provenance` JSON logging source and timestamp per field.

---

## 9. Golden Record Versioning

Same structure as article type. Hash-based rebuild detection.

---

## 10. Refresh Tiers

| Tier | Books | Frequency | Sources Refreshed |
|------|-------|-----------|-------------------|
| **Hot** | New editions detected, or flagged for review | Monthly | Google Books, CrossRef, OpenAlex, publisher scrape, link check |
| **Warm** | Published < 5 years ago, or citation_count > 50 | Quarterly | Google Books, OpenAlex, Goodreads/Amazon ratings, link check |
| **Cold** | Published > 5 years ago, not badged | Biannually | OpenAlex (citations), link check |
| **Archive** | Published > 15 years ago, citation < 10, not badged | Annually | Link check only |

**Books refresh more slowly than articles** — book metadata is more stable. The key signals to monitor are: new editions (publisher scrape), rating changes (Amazon/Goodreads), and OA status changes (DOAB/OAPEN additions).

---

## 11. Data Freshness Expectations

| Data | Source | Refresh Rationale |
|------|--------|-------------------|
| Edition status | Publisher scrape | New editions may supersede existing record |
| Pricing | Amazon scrape, publisher | Prices change; student editions may appear |
| Ratings | Goodreads, Amazon | Accumulate gradually |
| Citation counts | OpenAlex | Books accumulate citations slowly |
| OA status | DOAB, OAPEN | Books may become OA years after publication |
| Companion resources | Publisher scrape | Companion sites may be updated or removed |
| Syllabus adoption | OpenSyllabus | Updated annually |
| Link status | Link checker | Publisher URLs may change |
| TOC / chapter list | Publisher scrape, Google Books | Stable after publication |

---

## 12. Field Summary

### Book

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim with priority (V) | ~40 | title, authors, publisher, isbn, description, ratings, price, TOC |
| Derived / computed (D) | ~18 | url, publication_year, is_free, is_ebook_available, cover selection, citation max |
| LLM-authored (L) | ~12 | editorial_description, methodology_tags, thesis_stages, quality_score, badges, key_chapters |
| **Total book golden record fields** | **~70** | |

### Book Chapter

| Category | Count | Examples |
|----------|-------|---------|
| Verbatim with priority (V) | ~10 | chapter_title, chapter_number, chapter_authors, page_start, page_end, abstract |
| Inherited from parent book (I) | ~12 | parent_book_title, publisher, publication_date, isbn, edition, cover, price, language |
| Derived / computed (D) | ~5 | page_count, url, citation_count_max |
| LLM-authored (L) | ~6 | editorial_description, methodology_tags, thesis_stages, quality_score, difficulty |
| **Total chapter golden record fields** | **~33** | |

---

## 13. Source Coverage Heatmap — Book

| Field Category | GBooks | OLib | CR | ISBNdb | SprNat | OAlex | DOAB | OAPEN | NCBI | LThng | OCtns | PubScr | Amz | GR | OSyll |
|---------------|--------|------|----|--------|--------|-------|------|-------|------|-------|-------|--------|-----|----|------|
| **Identifiers** | ●●● | ●●○ | ●●○ | ●●● | ●●○ | ●●○ | ●○○ | ●○○ | ●○○ | ●○○ | — | — | ●○○ | ●○○ | — |
| **Bibliographic** | ●●● | ●●○ | ●●● | ●●● | ●●○ | ●○○ | ●●○ | ●●○ | ●●○ | ●○○ | — | ●●● | — | — | — |
| **Authors** | ●○○ | ●●○ | ●●● | ●○○ | ●●○ | ●●● | ●○○ | ●○○ | ●○○ | ●○○ | — | ●●○ | — | — | — |
| **Cover images** | ●●● | ●●○ | — | ●●○ | — | — | — | — | — | — | — | ●○○ | ●○○ | — | — |
| **Pricing** | ●●○ | — | — | ●●○ | — | — | — | — | — | — | — | ●●● | ●●● | — | — |
| **Ratings** | ●●○ | — | — | — | — | — | — | — | — | ●●○ | — | — | ●●● | ●●● | — |
| **Citations** | — | — | ●○○ | — | — | ●●● | — | — | — | — | ●●○ | — | — | — | — |
| **OA/Free access** | ●○○ | ●○○ | — | — | ●○○ | ●●○ | ●●● | ●●● | ●●● | — | — | — | — | — | — |
| **TOC/Chapters** | ●○○ | ●●○ | — | — | ●●● | — | — | — | ●●○ | — | — | ●●● | — | — | — |
| **Subjects** | ●●○ | ●●● | ●○○ | ●●○ | ●●○ | ●●● | ●●○ | ●○○ | — | ●●● | — | — | — | — | — |
| **Adoption** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ●●● |
| **Editions** | — | ●○○ | ●○○ | ●●● | — | — | — | — | — | ●●● | — | ●●○ | — | — | — |

GBooks=Google Books, OLib=Open Library, CR=CrossRef, SprNat=Springer Nature, OAlex=OpenAlex, LThng=LibraryThing, OCtns=OpenCitations, PubScr=Publisher Scrape, Amz=Amazon, GR=Goodreads, OSyll=OpenSyllabus

## 14. Source Coverage Heatmap — Book Chapter

| Field Category | CR | SprNat | OAlex | Scopus | PubScr | GBooks |
|---------------|-----|--------|-------|--------|--------|--------|
| **Chapter identifiers** | ●●● | ●●● | ●●○ | ●●○ | — | — |
| **Chapter title/number** | ●●● | ●●● | ●●○ | ●●○ | ●●● | ●○○ |
| **Chapter authors** | ●●● | ●●○ | ●●● | ●●○ | ●●○ | — |
| **Page range** | ●●● | ●●● | — | ●○○ | ●●○ | ●○○ |
| **Chapter abstract** | ●○○ | ●●● | — | ●●○ | ●○○ | — |
| **Chapter citations** | ●○○ | — | ●●● | ●●● | — | — |
| **Chapter subjects** | — | ●●○ | ●●● | ●●● | — | — |

CR=CrossRef (chapter DOI), SprNat=Springer Nature Meta API, OAlex=OpenAlex, PubScr=Publisher website scrape, GBooks=Google Books TOC
