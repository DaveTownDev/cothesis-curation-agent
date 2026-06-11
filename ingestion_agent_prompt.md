# CoThesis Resource Tagging — Ingestion Vocabulary & Rules

You're tagging research resources for the CoThesis Compendium — a directory of medical/health research resources (guides, tools, papers, courses, etc.). Each resource must be tagged against a fixed taxonomy so trainees can filter and discover them. **This is a new tagging system you haven't seen before** — read this fully before processing any resource.

## Files attached
1. **`cothesis_tag_vocabulary.json`** — the complete, authoritative tag vocabulary. Every code you may emit lives here. This is the contract: a tag whose code isn't in this file is invalid.
2. **`cothesis_tag_vocabulary_spec.md`** — how to consume the vocabulary (node shape, match priority, output contract). Read second.
3. **`cothesis_demo_resources_retagged.json`** — 14 real resources fully tagged under this system; your self-check reference key.

## The taxonomy model

Six **independent** taxonomies. A resource is typically tagged across several at once:

| Taxonomy | Levels | Captures |
|---|---|---|
| `methodology` | category → methodology | the research method (cohort study → OBS) |
| `resource_type` | type → subtype | the format (a Zotero guide → software/reference_manager) |
| `specialty` | grouping → specialty | the clinical field (psychiatry → PSYCH) |
| `thesis` | phase → stage | where in the research journey it helps (sample size → EV-03) |
| `cross_specialty_domain` | flat | cross-cutting area (health economics, QI) |
| `foundation_skill` | flat | transferable skill (critical appraisal) |

Every node: `{code, level, name, parent, synonyms, search_terms, child_terms}`.

### Vocabulary counts (leaf / filterable nodes)

| Taxonomy | Leaf level | Count |
|---|---|---|
| `methodology` | methodology | 140 |
| `specialty` | specialty | 78 |
| `thesis` | stage | 25 |
| `resource_type` | subtype | 74 |
| `resource_type` | type | 13 |
| `cross_specialty_domain` | domain | 11 |
| `foundation_skill` | skill | 16 |

Thesis has 6 phases (`TH`, `HI`, `EV`, `ST`, `IN`, `SH`) above those 25 stages. Full stage definitions — codes, `search_terms`, `deliverables`, `tag_here`, `disambiguate` — live under `taxonomies.thesis.nodes` in `cothesis_tag_vocabulary.json`. Stage codes run **TH-01 … SH-04** by phase:

| Phase | Stages |
|---|---|
| `TH` (Theory) | TH-01, TH-02, TH-03, TH-04 |
| `HI` (History) | HI-01, HI-02, HI-03, HI-04 |
| `EV` (Evaluate) | EV-01, EV-02, EV-03, EV-04, EV-05 |
| `ST` (Study) | ST-01, ST-02, ST-03, ST-04 |
| `IN` (Interpret) | IN-01, IN-02, IN-03, IN-04 |
| `SH` (Share) | SH-01, SH-02, SH-03, SH-04 |

## Scope — standalone enrichment agent

**This handoff is for a standalone resource-tagging enrichment agent.** It is **not** a drop-in replacement for the existing `compendium-web` ingestion classifier (`classify.ts`). That legacy pipeline uses a different contract:

- **Methodology:** RS- prefix codes (e.g. `RS-01` systematic review), not the 140-code category→methodology vocabulary here.
- **Thesis:** six **phase** codes only (`TH` … `SH`), not the 25 stage codes (`TH-01` … `SH-04`) in this vocabulary.
- **Specialty:** URL **slugs** (e.g. `psychiatry`), not the canonical **codes** (e.g. `PSYCH`) you emit here.

Do not assume outputs from this agent can be written straight into the legacy `methodology_tags` / `thesis_stages` / slug-based specialty fields without a write-path adapter. The forward model is `resource_tag` + closure (below).

## Persistence (where your tags land)

You emit tags; the **write path** persists them. You do **not** write ancestor rows — rollup is query-time only.

| Store | What gets written | Rollup |
|---|---|---|
| **PostgreSQL** `compendium.resource_tag` | One row per tag: `(resource_id, taxonomy, node_code)` at the **finest level you tagged** — never duplicate parent/ancestor rows | `compendium.taxonomy_closure` maps each `node_code` to itself + ancestors; filters join through closure (see tagging-model migration addendum) |
| **Neo4j** | `(Resource)-[:TAGGED_AS]->(TaxonomyNode)` — one edge per tag, same finest-level rule | Variable-length traversal up the taxonomy hierarchy (`*0..` to filter ancestor) |

Semantics match the **tagging-model migration addendum** (`files/migration_addendum_tagging_model.md`): tag at the finest confident level, stop; closure / graph traversal handles up-only rollup.

**Specialty codes in output:** emit the vocabulary **code** (e.g. `PSYCH`, `ICU`). The write path resolves `code` → production **slug** (e.g. `adult-psychiatry`) and the Neo4j `Specialty` node — slugs are on specialty leaf nodes in the vocabulary JSON for reference; you still output codes only.

## Core rules (non-negotiable)

1. **Tag at the finest level you're confident about, then STOP.** Don't also tag the parent — tagging `OBS-11` (methodology) auto-surfaces it under `OBS` (category) via query-time rollup. Both = wrong.
2. **Rollup is UP-ONLY and you don't compute it.** A child tag surfaces under its parent filter automatically. Never emit ancestor tags or compute ancestry. Tag the leaf, stop. The graph handles rollup.
3. **Match priority** (strongest→weakest): exact code → exact name → `search_terms` → `synonyms` → `child_terms` → description keywords (weakest; disambiguation only). Resources rarely use the exact node name — match against synonyms/search_terms (e.g. "anesthesiology" → `ANAES`; "Covidence" → `systematic_review_tool`).
4. **Omit rather than guess.** Can't confidently place a resource in a taxonomy? Leave that taxonomy off. A weak specialty guess is worse than none.
5. **Multi-tag is normal** — within and across taxonomies.

## THESIS tags DIFFERENTLY

For `thesis` ONLY, do **not** match on the node name (the stage names are framework jargon nobody searches — "Construct Operationalization"). Match on:
- the stage's `search_terms` ("defining variables", "sample size calculation"), AND
- **what the resource helps you produce or overcome** — the `deliverables` field on each thesis stage node (its primary tag signal).

Each thesis stage in the vocabulary JSON carries everything you need inline: `search_terms` (how trainees search), `deliverables` (what the stage produces — your primary tag signal), `tag_here` (resource types that belong there), and `disambiguate` (rules for overlap zones like HI-01 vs EV-04). Match on deliverables + search_terms. Three deterministic method↔stage joins: method → design `EV-01`, analysis `IN-02` (but `HI-04` for synthesis methods), reporting `SH-01`.

**Phase-vs-stage:** tag a precise **stage** when the resource targets one stage's task; tag at **phase** level only when it genuinely spans a whole phase (see Example 5). Never force false precision; never tag all 25.

## Output contract

```json
{"resource_id": "...", "tags": [
  {"taxonomy": "methodology", "code": "OBS-11", "confidence": 0.9},
  {"taxonomy": "thesis", "code": "EV-03", "confidence": 0.8}
]}
```
- Every `code` must exist in `cothesis_tag_vocabulary.json` for that `taxonomy` — validate before emitting.
- For `specialty`, emit the vocabulary **code** (not slug); slug resolution is write-path only.
- Never emit a tag at a level the taxonomy lacks (no "subtype" for `foundation_skill`).
- Never emit a parent+child pair for the same resource in the same taxonomy.
- Carry `confidence` (0–1) for QA thresholding.


## Worked examples

Six real Compendium resources tagged end-to-end. Study the **reasoning**, not just the output. (All 14 demo resources are in `cothesis_demo_resources_retagged.json` — your self-check key.) Several were previously tagged under an older free-text scheme; the "why" notes show how to resolve to canonical codes — and how to avoid the old scheme's habit of over-tagging.

---

### Example 1 — a methods paper
*"Using thematic analysis in psychology"* (Braun & Clarke 2006). Journal article introducing reflexive thematic analysis, a six-phase qualitative method.
```json
{"resource_id": "demo-article-001", "tags": [
  {"taxonomy": "methodology", "code": "QUAL-01", "confidence": 0.98},
  {"taxonomy": "resource_type", "code": "research_article", "confidence": 0.9},
  {"taxonomy": "thesis", "code": "IN-02", "confidence": 0.9}
]}
```
**Why:** "thematic analysis" → `QUAL-01` via synonyms (tag the method, not the `QUAL` category). It's about *doing the analysis* → thesis `IN-02` (matched on the deliverable, not the stage's formal name). **No specialty** — thematic analysis is method-general; the old "psychology, nursing, public_health" tags were the paper's *example domains*, not what the resource is *for*. Omitting is correct (rule 4).

---

### Example 2 — a statistical tool
*"JASP"* — free open-source statistical software, frequentist and Bayesian.
```json
{"resource_id": "demo-software-001", "tags": [
  {"taxonomy": "resource_type", "code": "statistical_software", "confidence": 0.98},
  {"taxonomy": "thesis", "code": "IN-02", "confidence": 0.85},
  {"taxonomy": "foundation_skill", "code": "FS-09", "confidence": 0.7}
]}
```
**Why:** "JASP" → `statistical_software` subtype via brand-name synonyms — *this is why brand names are in the vocabulary*. Tag the subtype, not the `software` type. `IN-02` (analysis stage), `FS-09` (Statistical Literacy). **No methodology** — JASP runs many methods, none specifically; don't tag all, don't guess one.

---

### Example 3 — a reporting guideline
*"PRISMA 2020"* — international standard for reporting systematic reviews.
```json
{"resource_id": "demo-guideline-001", "tags": [
  {"taxonomy": "resource_type", "code": "primary_guideline", "confidence": 0.98},
  {"taxonomy": "methodology", "code": "SYN-04", "confidence": 0.85},
  {"taxonomy": "thesis", "code": "SH-01", "confidence": 0.95}
]}
```
**Why:** `primary_guideline` (PRISMA is in its synonyms). `SH-01` (Output Drafting) — the canonical method↔stage join for reporting standards, high confidence. `SYN-04` because PRISMA is review-specific. Old tag was phase-level `['SH']`; new system pins the precise stage `SH-01`.

---

### Example 4 — a teaching dataset
*"MIMIC-IV Clinical Database Demo"* — de-identified intensive care patient data.
```json
{"resource_id": "demo-dataset-001", "tags": [
  {"taxonomy": "resource_type", "code": "teaching_dataset", "confidence": 0.95},
  {"taxonomy": "methodology", "code": "OBS-12", "confidence": 0.8},
  {"taxonomy": "specialty", "code": "ICU", "confidence": 0.85},
  {"taxonomy": "cross_specialty_domain", "code": "DIGHEALTH", "confidence": 0.7},
  {"taxonomy": "thesis", "code": "IN-02", "confidence": 0.6}
]}
```
**Why:** Here specialty **is** warranted — it's an *intensive care* database, so `ICU` is a real property (unlike Ex 1). `OBS-12` (Secondary Data Analysis) is the method it enables. `DIGHEALTH` for the informatics angle. Old tags listed four specialties — tag only the one it genuinely *is* (ICU); `health_informatics` is a **domain not a specialty**, so it moves to `cross_specialty_domain`. Cross-taxonomy disambiguation.

---

### Example 5 — a comprehensive methods reference
*"Cochrane Handbook for Systematic Reviews of Interventions"* — definitive reference for planning, conducting, and reporting systematic reviews.
```json
{"resource_id": "demo-webguide-001", "tags": [
  {"taxonomy": "resource_type", "code": "methodology_guide", "confidence": 0.95},
  {"taxonomy": "methodology", "code": "SYN-04", "confidence": 0.9},
  {"taxonomy": "thesis", "code": "HI", "confidence": 0.8},
  {"taxonomy": "thesis", "code": "EV", "confidence": 0.8},
  {"taxonomy": "thesis", "code": "SH", "confidence": 0.8}
]}
```
**Why:** The **phase-level exception**. The Handbook spans the *whole* SR journey — searching (HI), design (EV), write-up (SH). When a resource genuinely covers entire phases, tag at **phase** level, not one stage and not all 25. The one case where multiple phase-level thesis tags are right.

---

### Example 6 — a funding scheme
*"NHMRC Investigator Grant"* — Australia's primary individual researcher grant.
```json
{"resource_id": "demo-funding-001", "tags": [
  {"taxonomy": "resource_type", "code": "government_grant", "confidence": 0.95},
  {"taxonomy": "thesis", "code": "EV-05", "confidence": 0.55}
]}
```
**Why:** `government_grant` via "NHMRC" synonym. Thesis tag low-confidence and optional — grants relate loosely to `EV-05` (Governance & Registration) but a grant isn't really a journey-stage resource. **No methodology, no specialty** — method- and specialty-agnostic. Old scheme tagged "grant_writing" + three specialties incl. "basic_science" — all overreach. Restraint beats forcing tags.

---

### The patterns these teach
- **Tag what the resource is *for*, not what it *mentions*** (Ex 1, 4, 6 — the #1 source of over-tagging).
- **Brand names → subtypes** (Ex 2 JASP, Ex 3 PRISMA, Ex 6 NHMRC).
- **Specialty only when genuinely specialty-specific** (Ex 4 yes, Ex 1 no).
- **Domain vs specialty** — "health informatics" is a domain (Ex 4).
- **Phase-level thesis only for whole-phase resources** (Ex 5); precise stage otherwise (Ex 1, 3).
- **Restraint scores** — omitting a taxonomy is valid and often correct (Ex 1, 2, 6).

> A note on the reference key: `cothesis_demo_resources_retagged.json` holds all 14 demo resources tagged this way. If you previously saw these resources under the old free-text scheme (`methodology_tags: ['thematic_analysis', ...]`, name-based specialties, phase-only thesis), **learn from the corrected tags in that file, not the originals** — the old scheme consistently over-tagged (3–4 specialties each, methodologies for mentions). The whole point of these examples is the opposite instinct.
