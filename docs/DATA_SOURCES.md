# DATA_SOURCES — per-type enrichment APIs

**Principle: deterministic-and-API-first, LLM-last.** Pull structured metadata and tool signals before calling Gemini; only use the LLM for what they can't resolve. All external calls go through the existing MCP server (Discovery tool source) or APISIX, never direct from the public repo. Sourced from ENRICHMENT_SPEC §1.3.

| Resource type | Primary sources |
|---|---|
| article | PubMed/E-utilities, CrossRef, OpenAlex, Unpaywall, iCite, Altmetric; Semantic Scholar; self-hosted RobotReviewer (RoB), URSE (GRADE), MedJEx (jargon) |
| book / book_chapter | ISBNdb, Google Books, OpenLibrary, Springer |
| software | GitHub, bio.tools |
| dataset | Zenodo, Figshare, DataCite, protocols.io |
| video / podcast / community | YouTube Data API, podcast RSS, Reddit, Stack Exchange |
| reporting_guideline / web_guide / template / visual_reference | Crawl4AI + SearXNG (discovery), Marker/Docling (extraction) |
| course | provider pages via Crawl4AI; OpenAlex/CrossRef where a DOI exists |
| funding | NIH RePORTER; scheme pages via Crawl4AI |

**Discovery** queries these per (methodology × type) via the MCP server. **Appraisal** consumes the returned signals (study type, citations, RoB/GRADE) before any LLM scoring. Web extraction (Crawl4AI/Marker/Docling) is the fallback for types without a structured API.
