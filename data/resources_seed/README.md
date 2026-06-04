# resources_seed/

Drop a Neo4j/Postgres export of resources to enrich and to load into Vertex AI Search.

- ~30–60 `pending_enrichment` resources **per methodology** (SYN-01, SYN-02, OBS-01, EVAL-01).
- **Span the 14 resource types** so every type's enrichment path is exercised, not just articles.
- Raw metadata only (title, url, source, any structured fields). JSON or CSV.
- This is public research metadata — no patient data, no secrets.

Suggested: one file per methodology (e.g. `syn-01.json`) or a single `resources_seed.json` with a `methodology_code` field per record.
