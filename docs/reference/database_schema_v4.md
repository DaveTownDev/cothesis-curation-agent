# CoThesis Compendium — Database Schema v4 (as built)

**Version:** 4.1 (updated May 2026 to reflect what was actually built)
**Supersedes:** v4.0 (April 2026 design intent)
**Key corrections from v4.0:**
- Neo4j uses HTTP Transaction API, not Bolt (Bolt port unreachable on Railway private network)
- Public URL structure changed: `/resources/*` → `/library/*`, `/guides/*` → `/blog/lists/*`
- Two additional globals: `Footer`, `SiteHeader`
- `Comments` collection added
- Parts 1 and 2 now include actual schemas (previously referenced missing v3 doc)
- All `neo4j-driver` / Bolt code examples removed and replaced with HTTP API pattern

---

## Architecture Overview

Two Next.js deployments, five data stores, one shared auth layer:

```
compendium.cothesis.com  (or cothesis.ai)
  └── Cloudflare CDN
        └── Railway (persistent Node container)
              ├── Next.js 15 + Payload CMS (standalone build)
              ├── NEO4J via HTTP Transaction API (not Bolt)
              ├── PostgreSQL: payload.* + compendium.*
              ├── Redis: BullMQ queues
              └── Qdrant, LiteLLM, Langfuse (internal)

app.cothesis.ai
  └── Vercel (serverless)
        ├── Next.js 15
        ├── Convex (real-time app data)
        └── WorkOS (same environment as Compendium)
```

**Data responsibility split:**

| Data | Store | Accessed By |
|------|-------|-------------|
| Resource golden records | Neo4j | Compendium (HTTP Transaction API) |
| Resource editorial enrichments | Payload (`resource-editorial`) | Compendium (Local API) |
| Blog posts, pages, listicles | Payload (collections) | Compendium (Local API) |
| Import review queue | Payload (`import-candidates`) | Payload admin UI |
| Pipeline state | PostgreSQL (`compendium.*`) | BullMQ workers |
| Resource display cards (app) | Convex (synced) | CoThesis app on Vercel |
| Users, subscriptions | Convex + WorkOS | CoThesis app |
| SEO, navigation, site settings | Payload (Globals) | Compendium (Local API) |
| Vector embeddings | Qdrant | Compendium semantic search |
| User saved resources | Payload (`resource-usage`) | Compendium (Local API) |

---

# PART 1: NEO4J — GRAPH DATA

## Critical: HTTP Transaction API only

The Bolt port (`7687`) is not reachable within Railway's private network. All Neo4j queries use the **HTTP Transaction API**:

```
POST https://neo4j-production-98cf.up.railway.app/db/neo4j/tx/commit
Authorization: Basic base64(username:password)
Content-Type: application/json

{ "statements": [{ "statement": "MATCH (r:CompendiumResource) ...", "parameters": { ... } }] }
```

The `neo4j-driver` npm package is **not used** for frontend or pipeline queries. The helper `neo4jQuery(cypher, params)` in `src/pipeline/lib/neo4j.ts` handles this.

**Important HTTP API behaviours:**
- Node properties are returned as a flat object directly (not wrapped in `{properties: {}}`)
- All params must be plain JS numbers/strings — `neo4j.int()` objects do not serialise correctly over HTTP
- Use `toInteger($param)` in Cypher for `SKIP` and `LIMIT` clauses
- Fetches use Next.js `{ next: { revalidate: 3600 } }` for ISR-aware caching

## Environment variables

```
NEO4J_HTTP_URL=https://neo4j-production-98cf.up.railway.app
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<password>
```

Do not set `NEO4J_URI` (Bolt) — it is unused.

## 1.1 CompendiumResource node

Primary resource golden record. One node per resource. `resource_id` is the join key across all systems.

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (r:CompendiumResource)
  REQUIRE r.resource_id IS UNIQUE;

CREATE INDEX IF NOT EXISTS FOR (r:CompendiumResource) ON (r.resource_type);
CREATE INDEX IF NOT EXISTS FOR (r:CompendiumResource) ON (r.status);
CREATE INDEX IF NOT EXISTS FOR (r:CompendiumResource) ON (r.quality_score);
```

| Property | Type | Notes |
|----------|------|-------|
| `resource_id` | string (UUID) | Primary key. Join key across Neo4j, PostgreSQL, Payload, Convex, Qdrant. |
| `resource_type` | string | One of 14 values — see §1.4 |
| `subtype` | string \| null | Per-type subtype |
| `title` | string | Canonical title |
| `url` | string \| null | Primary URL |
| `status` | string | `enriched` \| `pending_enrichment` \| `draft` |
| `methodology_tags` | string[] | Methodology codes (e.g. `thematic_analysis`, `rct`) |
| `thesis_stages` | string[] | THESIS stages: `theory` \| `history` \| `evaluate` \| `study` \| `interpret` \| `share` |
| `doi` | string \| null | Digital Object Identifier |
| `isbn` | string \| null | |
| `pmid` | string \| null | PubMed ID |
| `quality_score` | integer 0–100 \| null | Set by enrichment + AI assessment. Cards show 5-segment bar if ≥60. |
| `badges` | string[] | `essential` \| `editors_choice` \| `best_free` \| `best_beginners` |
| `access_type` | string \| null | `free` \| `freemium` \| `paid` \| `subscription` \| `institutional` |
| `description` | string \| null | Set by enrichment worker |
| `author_names` | string[] \| null | Set by enrichment worker |
| `year` | integer \| null | Publication year |
| `journal_name` | string \| null | |
| `institution` | string \| null | |
| `citation_count` | integer \| null | |
| `is_open_access` | boolean \| null | |
| `pdf_url` | string \| null | |
| `image_url` | string \| null | Thumbnail / cover image |
| `embed_url` | string \| null | YouTube embed URL for video resources |
| `compendium_created_at` | datetime | When the node was first created |

Resources with `status IN ['enriched', 'pending_enrichment']` are shown publicly. `draft` nodes are pipeline-only.

## 1.2 Taxonomy nodes

### Specialty

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Specialty) REQUIRE s.code IS UNIQUE;
CREATE INDEX IF NOT EXISTS FOR (s:Specialty) ON (s.slug);
```

| Property | Type | Notes |
|----------|------|-------|
| `code` | string | Unique specialty code (e.g. `PSY`, `CARD`) |
| `name` | string | Display name |
| `shortName` | string \| null | Abbreviated display name |
| `slug` | string | URL slug (e.g. `psychiatry`) |
| `category` | string \| null | Specialty category grouping |
| `phase` | string \| null | Training phase relevance |
| `displayOrder` | integer \| null | Sort order for UI |
| `researchIntensity` | string \| null | `low` \| `medium` \| `high` |

### CompendiumMethodology

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (m:CompendiumMethodology) REQUIRE m.code IS UNIQUE;
CREATE INDEX IF NOT EXISTS FOR (m:CompendiumMethodology) ON (m.slug);
```

| Property | Type | Notes |
|----------|------|-------|
| `code` | string | Unique methodology code (e.g. `THEMATIC_ANALYSIS`) |
| `title` | string | Display name |
| `slug` | string | URL slug |
| `description` | string \| null | |
| `type` | string \| null | Methodology category |
| `tier` | string \| null | `core` \| `advanced` |
| `categoryCode` | string \| null | Parent category code |

### CrossSpecialtyDomain

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (d:CrossSpecialtyDomain) REQUIRE d.code IS UNIQUE;
CREATE INDEX IF NOT EXISTS FOR (d:CrossSpecialtyDomain) ON (d.slug);
```

| Property | Type | Notes |
|----------|------|-------|
| `code` | string | Unique domain code |
| `name` | string | Display name |
| `shortName` | string \| null | |
| `slug` | string | URL slug |
| `description` | string \| null | |
| `phase` | string \| null | |
| `displayOrder` | integer \| null | |

## 1.3 Relationships

| Relationship | From → To | Meaning |
|-------------|----------|---------|
| `TARGETS_SPECIALTY` | CompendiumResource → Specialty | Resource is relevant to this specialty |
| `USES_METHODOLOGY` | CompendiumResource → CompendiumMethodology | Resource uses this methodology |
| `ADDRESSES_DOMAIN` | CompendiumResource → CrossSpecialtyDomain | Resource addresses this cross-specialty domain |

## 1.4 Resource type values

14 valid values for `resource_type`:

`article` · `book` · `book_chapter` · `video` · `podcast` · `software` · `reporting_guideline` · `course` · `web_guide` · `template` · `visual_reference` · `dataset` · `community` · `funding`

## 1.5 Neo4j query pattern

All queries go through `neo4jQuery<T>(cypher, params)` in `src/pipeline/lib/neo4j.ts`:

```typescript
// Returns T[] where T is the shape of the return row
const records = await neo4jQuery<{ r: Record<string, unknown> }>(
  `MATCH (r:CompendiumResource)
   WHERE r.status IN ['enriched', 'pending_enrichment']
   RETURN r
   ORDER BY r.quality_score DESC
   LIMIT toInteger($limit)`,
  { limit: 24 },
)
// Access node properties directly: records[0].r.title (NOT records[0].r.properties.title)
```

---

# PART 2: POSTGRESQL — `compendium.*` SCHEMA (Pipeline State)

Managed separately from Payload. Created by running `pnpm pipeline:seed-schema` (executes `src/pipeline/schema.sql`).

```
Internal address: postgres.railway.internal:5432
Schema: compendium (separate from payload.*)
```

## compendium.import_batches

Tracks each import run end-to-end.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `source_file` | varchar(500) | Original filename |
| `source_tool` | varchar(50) | `gemini` \| `claude` \| `manus` \| `manual` \| `discovery_prompt` |
| `file_format` | varchar(10) | `json` \| `csv` \| `md` |
| `imported_at` | timestamp | |
| `imported_by` | varchar(100) | WorkOS user ID or `system` |
| `batch_name` | varchar(255) | Optional human label |
| `total_candidates` | integer | |
| `parsed_count` | integer | |
| `duplicate_count` | integer | |
| `auto_accepted_count` | integer | |
| `auto_excluded_count` | integer | |
| `review_needed_count` | integer | |
| `human_accepted_count` | integer | |
| `human_rejected_count` | integer | |
| `enrichment_queued_count` | integer | |
| `enriched_count` | integer | |
| `status` | varchar(20) | `processing` \| `complete` \| `failed` |
| `completed_at` | timestamp \| null | |
| `error_log` | text \| null | |

## compendium.import_candidates

One row per resource found in an import batch. Source of truth for pipeline state. Mirrored in the Payload `import-candidates` collection for human review UI.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `import_batch_id` | UUID FK → import_batches | |
| `source_file` | varchar(500) | |
| `source_tool` | varchar(50) | |
| `imported_at` | timestamp | |
| `raw_data` | JSONB | Original parsed input |
| `url` | text \| null | |
| `normalised_url` | text \| null | Canonicalised for dedup (UTM stripped, trailing slash normalised) |
| `title` | text \| null | |
| `description` | text \| null | |
| `doi` | varchar(100) \| null | |
| `isbn` | varchar(20) \| null | |
| `pmid` | varchar(20) \| null | |
| `classified_type` | varchar(30) \| null | One of 14 resource types |
| `classified_subtype` | varchar(50) \| null | |
| `methodology_tags` | text[] \| null | |
| `thesis_stages` | text[] \| null | |
| `relevance_score` | float \| null | 0–1. ≥0.6 + confidence ≥0.8 = auto-accept |
| `relevance_reasoning` | text \| null | LLM explanation |
| `classification_confidence` | float \| null | 0–1 |
| `access_type` | varchar(20) \| null | |
| `skip_reason` | text \| null | Set if not a discrete citable resource |
| `status` | varchar(30) | See pipeline status flow below |
| `duplicate_of` | UUID \| null | `resource_id` of existing resource |
| `duplicate_type` | varchar(30) \| null | `exact_url` \| `normalised_url` \| `doi` \| `isbn` \| `title_match` \| `cross_type_duplicate` |
| `review_notes` | text \| null | |
| `reviewed_by` | varchar(100) \| null | Admin identifier |
| `reviewed_at` | timestamp \| null | |
| `review_overrides` | JSONB \| null | Human corrections to LLM classification |
| `resource_id` | UUID \| null | Set when accepted → Neo4j node created |
| `classifier_model` | varchar(50) \| null | LLM model used |
| `classifier_trace_id` | varchar(100) \| null | Langfuse trace ID |

**Status flow:**
```
parsed → dedup_checking → classifying → classified →
  ├── auto_accepted → enrichment_queued → enriched
  ├── review_needed → human_accepted → enrichment_queued → enriched
  ├── review_needed → human_rejected
  ├── auto_excluded
  └── duplicate
```

## compendium.discovery_records

One row per accepted resource. Created when a candidate transitions to `auto_accepted` or `human_accepted`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `resource_id` | UUID UNIQUE | Matches Neo4j CompendiumResource.resource_id |
| `discovered_url` | text | Original URL from source |
| `discovered_by` | varchar(50) | Source tool |
| `discovery_context` | text \| null | Context sentence from discovery document |
| `agent_assigned_type` | varchar(30) \| null | Type the source tool assigned |
| `import_candidate_id` | UUID FK → import_candidates | |
| `created_at` | timestamp | |
| `enrichment_completed_at` | timestamp \| null | Set when enrichment finishes |
| `enriched_fields` | JSONB \| null | Snapshot of fields written by enrichment |

## compendium.excluded_resources

Permanently excluded URLs/DOIs — never re-import.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `url` | text | |
| `normalised_url` | text \| null | |
| `doi` | varchar(100) \| null | |
| `isbn` | varchar(20) \| null | |
| `excluded_at` | timestamp | |
| `excluded_by` | varchar(100) | |
| `reason` | text \| null | |

## compendium.enrichment_queue

Tracks enrichment worker state per resource.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `resource_id` | UUID | |
| `resource_type` | varchar(30) | Determines which enricher runs |
| `priority` | integer | Lower = higher priority |
| `status` | varchar(20) | `pending` \| `processing` \| `complete` \| `failed` |
| `job_id` | varchar(100) \| null | BullMQ job ID |
| `enqueued_at` | timestamp | |
| `started_at` | timestamp \| null | |
| `completed_at` | timestamp \| null | |
| `attempts` | integer | |
| `last_error` | text \| null | |

---

# PART 3: PAYLOAD CMS

**Location:** Same Railway service as the Next.js frontend (`compendium-web`)
**Database:** `payload` schema in Railway PostgreSQL
**Admin panel:** `/admin`, protected by Payload's own auth (separate from WorkOS)
**Media storage:** Vercel Blob (`@payloadcms/storage-vercel-blob`)

## Environment variables

```
DATABASE_URL=${{Postgres.DATABASE_URL}}?schema=payload
PAYLOAD_SECRET=<random string, min 32 chars>
BLOB_READ_WRITE_TOKEN=<vercel blob token>
NEXT_PUBLIC_SERVER_URL=https://cothesis.ai
```

## 3.1 payload.config.ts (as built)

```typescript
export default buildConfig({
  admin: {
    user: 'admins',
    meta: { titleSuffix: '— CoThesis Compendium' },
  },
  db: postgresAdapter({
    pool: { connectionString: process.env.DATABASE_URL },
    schemaName: 'payload',
  }),
  collections: [
    Admins,
    BlogPosts, Comments, Pages, Listicles, Media,
    ResourceEditorial, ImportCandidates,
    ResourceSuggestions, ResourceUsage,
  ],
  globals: [Navigation, SiteSettings, DirectorySettings, Footer, SiteHeader],
  plugins: [
    ...plugins,
    vercelBlobStorage({ token: process.env.BLOB_READ_WRITE_TOKEN, collections: { media: true } }),
  ],
  cors: ['https://cothesis.ai', 'https://app.cothesis.com'],
})
```

## 3.2 Collections

### admins (slug: `admins`)

CMS auth user. Not WorkOS — entirely separate from public user auth.

| Field | Type | Notes |
|-------|------|-------|
| `name` | text \| null | |
| `role` | select \| null | `super-admin` \| `editor` \| `reviewer` |
| `email` | text | Payload auth field (required) |
| `password` | text | Payload auth field |

---

### blog-posts (slug: `blog-posts`)

Drafts enabled (autosave). Published via `_status = 'published'`.

| Field | Type | Notes |
|-------|------|-------|
| `title` | text | Required |
| `excerpt` | text \| null | 1–2 sentence summary for listing cards |
| `coverImage` | relationship → media \| null | |
| `content` | Lexical rich text | Required |
| `meta.title` | text \| null | SEO override |
| `meta.image` | relationship → media \| null | OG image |
| `meta.description` | text \| null | SEO meta description |
| `authors` | relationship[] → admins \| null | |
| `publishedAt` | date \| null | |
| `slug` | text \| null | Auto-generated from title |
| `_status` | `draft` \| `published` | Drafts field |

Hook: `revalidateBlogPost` — calls `revalidatePath('/blog')` and `revalidatePath('/blog/{slug}')` on publish.

---

### comments (slug: `comments`)

Blog post comments. Require approval before appearing publicly.

| Field | Type | Notes |
|-------|------|-------|
| `content` | text | Required |
| `author.name` | text | Required |
| `author.email` | text | Required |
| `post` | relationship → blog-posts | Required |
| `isApproved` | boolean \| null | Must be true to show publicly |
| `publishedAt` | date \| null | |

---

### pages (slug: `pages`)

Static/marketing pages. Drafts enabled. Block-based layout.

| Field | Type | Notes |
|-------|------|-------|
| `title` | text | Required |
| `hero.type` | select | `none` \| `highImpact` \| `mediumImpact` \| `lowImpact` |
| `hero.richText` | Lexical \| null | |
| `hero.links` | array \| null | CTA links |
| `hero.media` | relationship → media \| null | |
| `layout` | blocks | `CallToActionBlock` \| `ContentBlock` \| `MediaBlock` |
| `meta.title` | text \| null | |
| `meta.image` | relationship → media \| null | |
| `meta.description` | text \| null | |
| `publishedAt` | date \| null | |
| `slug` | text \| null | |
| `_status` | `draft` \| `published` | |

Hook: `revalidatePage` — calls `revalidatePath('/{slug}')` on publish.
Route: `src/app/(frontend)/[slug]/page.tsx` catches all published page slugs.

---

### listicles (slug: `listicles`)

"Best of" curated lists linking to Neo4j resources. Drafts enabled.

| Field | Type | Notes |
|-------|------|-------|
| `title` | text | Required |
| `subtitle` | text \| null | Shown in listing cards |
| `coverImage` | relationship → media \| null | |
| `intro` | Lexical \| null | Text before the resource list |
| `resourceIds` | array \| null | Each item: `resourceId` (UUID → Neo4j), `annotation` (text) |
| `outro` | Lexical \| null | Text after the resource list |
| `meta.title` | text \| null | |
| `meta.image` | relationship → media \| null | |
| `meta.description` | text \| null | |
| `resourceType` | select \| null | One of 14 types — filters display |
| `publishedAt` | date \| null | |
| `slug` | text \| null | |
| `_status` | `draft` \| `published` | |

Hook: `revalidateListicle` — revalidates `/blog/lists` and `/blog/lists/{slug}`.
Detail page fetches each `resourceId` from Neo4j to render the full resource card.

---

### resource-editorial (slug: `resource-editorial`)

One record per resource. Holds AI assessment + human editorial content. No Payload drafts — uses its own `status` field.

**Rule: once `status = published`, pipeline must never overwrite `editorialDescription`, `badges`, or `qualityScore`.**

| Field | Type | Notes |
|-------|------|-------|
| `resourceId` | text (indexed) | UUID — join key to Neo4j, PostgreSQL, Convex |
| `resourceTitle` | text | Pipeline-managed. May be refreshed. |
| `resourceUrl` | text | Pipeline-managed. May be refreshed. |
| `resourceType` | select | One of 14 types |
| `editorialDescription` | textarea \| null | Human-written prose. Never overwritten once published. |
| `badges` | array \| null | Each item: `badge` (text) |
| `highlightedFeatures` | array \| null | Each item: `feature` (text) |
| `reviewNotes` | textarea \| null | Internal only, not displayed |
| `methodologyTags` | array \| null | Each item: `tag` (text) |
| `thesisStages` | multiselect \| null | `theory` \| `history` \| `evaluate` \| `study` \| `interpret` \| `share` |
| `accessType` | select \| null | `free` \| `freemium` \| `paid` \| `subscription` \| `institutional` |
| `isFree` | checkbox | |
| `qualityScore` | number 0–100 \| null | AI-assigned. Human may override. |
| `aiDraftDescription` | textarea \| null | AI draft — starting point for human editing |
| `aiAssessmentNotes` | textarea \| null | AI reasoning |
| `assessorModel` | text \| null | e.g. `glm-4.7` |
| `assessedAt` | date \| null | |
| `status` | select | `ai_draft` \| `review_ready` \| `published` \| `archived` |
| `reviewedBy` | relationship → admins \| null | |
| `publishedAt` | date \| null | |

Hook: `revalidateResourceEditorial` — revalidates `/library/resources/{resourceId}`.

Frontend merge: `getEditorialOverride(resource_id)` fetches via REST, merges over Neo4j fields. Editorial `description`, `badges`, and `qualityScore` take priority where present.

---

### import-candidates (slug: `import-candidates`)

Admin-only review queue for the import pipeline. Mirrors `compendium.import_candidates` in PostgreSQL.

| Field | Type | Notes |
|-------|------|-------|
| `importBatchId` | text (indexed) | UUID of import batch |
| `sourceFile` | text \| null | |
| `sourceTool` | select \| null | `manus` \| `gemini` \| `claude` \| `discovery_prompt` \| `manual` |
| `importedAt` | date \| null | |
| `url` | text \| null | |
| `title` | text \| null | |
| `description` | textarea \| null | |
| `doi` | text \| null | |
| `isbn` | text \| null | |
| `pmid` | text \| null | |
| `classifiedType` | select \| null | One of 14 resource types |
| `classifiedSubtype` | text \| null | |
| `methodologyTags` | array \| null | Each item: `tag` (text) |
| `relevanceScore` | number 0–1 \| null | ≥0.6 + confidence ≥0.8 = auto-accept |
| `relevanceReasoning` | textarea \| null | |
| `classificationConfidence` | number 0–1 \| null | |
| `accessType` | select \| null | |
| `skipReason` | text \| null | Why this isn't a discrete resource |
| `classifierModel` | text \| null | |
| `duplicateOf` | text \| null | `resource_id` of existing resource |
| `duplicateType` | select \| null | `exact_url` \| `normalised_url` \| `doi` \| `isbn` \| `title_match` \| `cross_type_duplicate` |
| `reviewNotes` | textarea \| null | |
| `reviewedBy` | relationship → admins \| null | |
| `reviewedAt` | date \| null | |
| `reviewOverrides` | json \| null | Human corrections to LLM classification |
| `resourceId` | text \| null | Set when accepted and linked to Neo4j |
| `status` | select (indexed) | 11 statuses — see pipeline flow |

Custom API endpoints:
- `POST /api/import-candidates/:id/approve` — sets `human_accepted`, enqueues BullMQ accept job
- `POST /api/import-candidates/:id/reject` — sets `human_rejected`

---

### resource-suggestions (slug: `resource-suggestions`)

User-submitted resource suggestions. Public create, admin read/update.

| Field | Type | Notes |
|-------|------|-------|
| `url` | text | Required |
| `title` | text \| null | |
| `resourceType` | text \| null | Unvalidated user suggestion |
| `description` | textarea \| null | |
| `submittedByWorkosId` | text \| null | WorkOS user ID |
| `submittedByEmail` | text \| null | |
| `status` | select \| null | `pending` \| `accepted` \| `rejected` \| `duplicate` |
| `reviewedBy` | relationship → admins \| null | |
| `reviewNotes` | textarea \| null | |

---

### resource-usage (slug: `resource-usage`)

"I use this" / saved resource markers. One record per user per resource. Powers the `/library/saved` page.

| Field | Type | Notes |
|-------|------|-------|
| `resourceId` | text (indexed) | UUID matching Neo4j CompendiumResource node |
| `workosUserId` | text | WorkOS user ID |
| `markedAt` | date | When the user saved the resource |

---

### media (slug: `media`)

Vercel Blob storage. Standard Payload media collection.

| Field | Type | Notes |
|-------|------|-------|
| `alt` | text \| null | |
| `caption` | Lexical \| null | |
| `url` | text | Vercel Blob CDN URL |
| `filename` | text | |
| `mimeType` | text | |
| `filesize` | number | |
| `width` | number \| null | |
| `height` | number \| null | |
| `sizes` | object | Resized variants: thumbnail, square, small, medium, large, xlarge |

## 3.3 Globals

| Global | Slug | Purpose |
|--------|------|---------|
| Navigation | `navigation` | Top nav links (currently hardcoded in `CompendiumNav` — global unused) |
| SiteSettings | `site-settings` | Site name, default SEO title/description, analytics IDs |
| DirectorySettings | `directory-settings` | Default sort order, featured resource types, max results per page |
| Footer | `footer` | Footer nav columns, social links |
| SiteHeader | `site-header` | Announcement bar text, maintenance mode flag |

## 3.4 ISR revalidation pattern

Each collection has an `afterChange` hook that triggers Next.js ISR revalidation:

```typescript
// example: revalidateBlogPost.ts
import { revalidatePath } from 'next/cache'

export const revalidateBlogPost: CollectionAfterChangeHook = async ({ doc, req: { payload } }) => {
  if (doc._status === 'published') {
    revalidatePath('/blog')
    revalidatePath(`/blog/${doc.slug}`)
  }
}
```

---

# PART 4: CONVEX — CoThesis APP DATA (not used by Compendium site)

Convex runs only in the CoThesis app on Vercel. The Compendium site on Railway does **not** use Convex.

## Convex schema (relevant tables)

```typescript
// The Compendium site does not read from Convex.
// The pipeline syncs minimal resource cards to Convex for the AI mentor to reference.

users: defineTable({
  workosUserId: v.string(),       // join key with WorkOS + Payload resource-usage
  email: v.string(),
  name: v.optional(v.string()),
  role: v.string(),
  institution: v.optional(v.string()),
  specialty: v.optional(v.string()),
  trainingProgramme: v.optional(v.string()),
  country: v.optional(v.string()),
  createdAt: v.number(),
  lastLoginAt: v.optional(v.number()),
  isActive: v.boolean(),
}).index("by_workosUserId", ["workosUserId"]),

// Minimal resource cards synced from pipeline — for AI mentor cross-references
resources: defineTable({
  resourceId: v.string(),           // UUID — join key
  resourceType: v.string(),
  title: v.string(),
  url: v.string(),
  editorialDescription: v.string(),
  methodologyTags: v.array(v.string()),
  qualityScore: v.optional(v.number()),
  isFree: v.boolean(),
  syncedAt: v.number(),
}).index("by_resourceId", ["resourceId"])
 .index("by_type", ["resourceType"])
 .searchIndex("search_resources", {
   searchField: "title",
   filterFields: ["resourceType", "isFree"],
 }),
```

## Sync flow

```
Pipeline: enrichment + assessment complete
  1. Write/update CompendiumResource node in Neo4j
  2. Create/update resource-editorial in Payload (Local API — same Railway network)
  3. Sync minimal card to Convex (HTTP mutation — external call)
  4. Embed to Qdrant (compendium_resources collection)

Payload afterChange (resource-editorial publish):
  1. Trigger ISR revalidation for /library/resources/{resourceId}
  2. If editorialDescription changed → sync updated card to Convex
```

---

# PART 5: BULLMQ WORKERS

All workers run as part of the `compendium-web` Railway service, connecting to Redis on `redis.railway.internal`.

| Worker | Queue | Job type | What it does |
|--------|-------|----------|-------------|
| parse | `compendium-import` | `import.parse` | Auto-detect format (JSON/CSV/MD), parse to import_candidates in PG |
| dedup | `compendium-import` | `import.dedup` | Check URL, DOI, ISBN, title similarity against Neo4j + PG |
| classify | `compendium-import` | `import.classify` | LLM call → relevance score + type classification → route to accept/review/exclude |
| accept | `compendium-import` | `import.accept` | Create Neo4j node (status: pending_enrichment), enqueue enrichment |
| enrichment | `compendium-enrichment` | `enrich.{type}` | Per-type API calls → update Neo4j node |
| assessment | `compendium-assessment` | `assess` | LLM quality scoring → create/update Payload resource-editorial |
| sync | `compendium-sync` | `sync.convex` | Sync minimal card to Convex + trigger ISR revalidation |
| embed | `compendium-embed` | `embed` | Generate Gemini embedding → upsert to Qdrant |
| linkcheck | `compendium-linkcheck` | `linkcheck` | Periodic URL validity checks |

## Import pipeline routing thresholds (env vars)

```
IMPORT_RELEVANCE_AUTO_ACCEPT=0.6    # relevance score to auto-accept (with confidence ≥ 0.8)
IMPORT_RELEVANCE_AUTO_EXCLUDE=0.3   # relevance score to auto-exclude (with confidence ≥ 0.8)
IMPORT_CONFIDENCE_AUTO_ACCEPT=0.8   # confidence threshold for auto decisions
IMPORT_CONFIDENCE_REVIEW=0.5        # below this → always to review queue
IMPORT_CLASSIFY_CONCURRENCY=4       # parallel LLM calls in classify worker
```

---

# PART 6: QDRANT — VECTOR STORE

**Collection:** `compendium_resources`
**Dimensions:** 3072 (Gemini text-embedding-004)
**Internal URL:** `http://qdrant.railway.internal:6333`

One point per enriched resource. Point ID = `resource_id` (UUID). Payload: `{ resource_type, quality_score, thesis_stages[], is_free }` for filtered semantic search.

---

# PART 7: AUTH

## Payload admin auth

`/admin` uses Payload's built-in session auth with the `admins` collection. Email + password. No WorkOS involvement. Sessions stored in `payload.payload_preferences`.

## Public user auth (WorkOS)

WorkOS handles SSO for both `compendium.cothesis.com` and `app.cothesis.ai` via shared session cookies. A user registered on either site is the same user everywhere.

The Next.js middleware (`src/middleware.ts`) gates protected Compendium routes:
- `/library/saved` — requires WorkOS session; unauthenticated users see a placeholder page with sign-in CTA
- Future: premium resource content gating

`resource-usage` records use `workosUserId` to identify users without needing a Payload `users` collection.

---

# PART 8: KEY INVARIANTS

These must never be violated:

1. **`resource_id` is the universal join key.** UUID string. Links Neo4j, `compendium.*` PG, Payload `resource-editorial.resourceId`, Convex `resources.resourceId`, Qdrant point ID.

2. **Neo4j via HTTP only.** `bolt://neo4j.railway.internal:7687` is unreachable. Use `neo4jQuery()`, not `neo4j-driver`.

3. **`toInteger()` in Cypher for SKIP/LIMIT.** Params are plain JS numbers — `neo4j.int()` does not work over HTTP.

4. **HTTP API returns flat properties.** `rec.r.title` not `rec.r.properties.title`.

5. **Pipeline never overwrites editorial content on published records.** Once `resource-editorial.status = 'published'`, only `resourceTitle` and `resourceUrl` may be updated by pipeline workers.

6. **Payload collection slugs are exact.** `blog-posts`, `listicles`, `pages`, `resource-editorial`, `import-candidates`, `resource-suggestions`, `resource-usage`, `admins`, `media`, `comments`. Never `posts`, `articles`, or bare plurals.

7. **`BLOB_READ_WRITE_TOKEN` is required to run `payload generate:types` locally.** Without it, Payload config throws during initialisation. Set it to any dummy `vercel_blob_rw_*` format string for local type generation.
