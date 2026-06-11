# CoThesis Tag Vocabulary — Ingestion Schema Spec

**Companion to `cothesis_tag_vocabulary.json`.** This tells the ingestion/enrichment agent how to consume the vocabulary to tag resources. The JSON is the machine-readable contract; this is the how. (The prompt covers the same rules conversationally — this is the precise reference.)

---

## What the JSON gives you

One file, six taxonomies, **one uniform node shape** so your tagging code is a single path regardless of taxonomy:

```json
{ "code": "OBS-11", "level": "methodology", "name": "Administrative Database Study",
  "parent": "OBS", "synonyms": [...], "search_terms": [...], "child_terms": [...] }
```

Every node has this shape. `parent: null` = top-level. `level` tells you which of the taxonomy's levels the node sits at. Some nodes carry extra fields (thesis stages add `deliverables`, `tag_here`, `disambiguate`, `description`; some nodes carry `_flag`/`_preserved` provenance notes — informational, ignore for tagging).

| Taxonomy | levels | top → leaf | total nodes |
|---|---|---|---|
| `resource_type` | type → subtype | 13 → 74 | 87 |
| `specialty` | grouping → specialty | 17 → 78 | 95 |
| `methodology` | category → methodology | 13 → 140 | 153 |
| `cross_specialty_domain` | (flat) | 11 | 11 |
| `foundation_skill` | (flat) | 16 | 16 |
| `thesis` | phase → stage | 6 → 25 | 31 |

(THESIS is fully inline in the JSON — no separate guide needed.)

> **Footnote:** `resource_type` has **74** subtypes (not 73). The tagging-model migration addendum predates a subtype addition; this vocabulary and the production taxonomy library export use 74.

---

## The core tagging rules

1. **Tag at the finest level you're confident about, and STOP.** Do not also tag the parent — rollup is handled at query time. Tagging `OBS-11` (a methodology) automatically makes the resource appear under `OBS` (its category). Adding both is redundant and wrong.
2. **Rollup is up-only.** A leaf tag satisfies ancestor filters; an ancestor tag never satisfies descendant filters. (A resource tagged `subtype` appears under its `type`; one tagged only at `type` does not appear under a specific subtype.)
3. **Multi-tag freely** — within a taxonomy (a resource can be `IN-01` and `IN-02` if it covers both) and across taxonomies (typically methodology + thesis + specialty + resource_type at once).
4. **Omit rather than guess.** Can't confidently place a resource in a taxonomy? Leave that taxonomy off entirely. A weak specialty guess is worse than none.

---

## When to use which level (each taxonomy block carries a `when_to_use` string)

- **resource_type:** subtype when the format is specific ("a reference manager" → `reference_manager`); type when only broad format is clear ("some software" → `software`).
- **specialty:** specialty when it targets a named specialty ("psychiatry research" → `PSYCH`); grouping only when it spans a whole grouping ("surgical research methods" → the Surgery grouping). Subspecialties (e.g. CAMHS) are leaf specialties — they roll up to their grouping.
- **methodology:** methodology when about a specific method ("how to run a cohort study" → `OBS-xx`); category when study-type-general ("intro to observational research" → `OBS`).
- **thesis:** stage when the resource targets one stage's task ("sample size calculation" → `EV-03`); phase when it genuinely spans a whole phase (a complete "how to do a systematic review" guide → `HI`/`EV`/`SH`). See the THESIS-specific note below.
- **domain / skill:** single level — tag when the resource addresses that cross-cutting domain or transferable skill.

---

## How to match (the `match_priority` order)

Resolve a resource's free-text (title + description) to codes in this priority:

1. **Exact code** (if the source already names one)
2. **Exact name** match
3. **`search_terms`** — purpose-built search phrases (present on methodology and thesis; richest signal where present)
4. **`synonyms`** — regional name variations, abbreviations, and brand names (e.g. "anesthesiology" → `ANAES`; "Zotero" → `reference_manager`; "PRISMA" → `primary_guideline`)
5. **`child_terms`** — names of the level below. Matching a child_term means tag the **node that owns it**, unless you can resolve to the child itself.
6. **description keywords** — weakest; use only to disambiguate between candidates, never as sole basis.

> **Worked example.** Resource: *"A free guide to managing references with Zotero."* → "Zotero" is in `reference_manager`'s synonyms → tag **`reference_manager`** (subtype). Don't also tag `software` (its type). No specialty (tool is field-general) — omit rather than guess. (If a foundation-skill tag fits, match the resource's task against skill `synonyms`, not the skill's display name — e.g. "reference management" appears in FS-13's synonyms.)

---

## THESIS tags differently — match on deliverables, not name

For `thesis` ONLY, **do not match on the node name** — the stage names are framework jargon nobody searches ("Construct Operationalization"). Each thesis stage node carries, inline:
- `search_terms` — how trainees actually search ("defining variables", "sample size calculation")
- `deliverables` — what the stage produces (**your primary tag signal**: does the resource help produce this?)
- `tag_here` — the resource types that belong at this stage
- `disambiguate` — rules for overlap zones (e.g. HI-01 preliminary search vs EV-04 reproducible protocol search)

Match on `deliverables` + `search_terms` + `tag_here`. Three deterministic method↔stage joins: a method resource → its design stage `EV-01`, analysis stage `IN-02` (but `HI-04` for synthesis methods), reporting stage `SH-01`.

---

## Synonym coverage — what to expect

Coverage is now **comprehensive across every taxonomy**, concentrated at the leaf level and at top levels where bucket-terms matter:

| Taxonomy | Leaf coverage | Notes |
|---|---|---|
| **methodology** | 140/140 + 13/13 categories | regional variants + search_terms; method names drift heavily — lean on these |
| **resource_type** | 74/74 + 13/13 types | **includes brand names** — Zotero/Covidence/R/SPSS/PROSPERO/NHMRC etc. resolve to their subtype. Critical for tool resources. |
| **specialty** | 69/78 + 17/17 groupings | international variants (anesthesiology/pediatrics/PM&R/GUM/I-O). 9 leaves intentionally empty (single-term names identical across regions — match on name) |
| **thesis** | 25/25 stages + 6/6 phases | search_terms (SEO) + deliverables — match on these, NOT names |
| **domain / skill** | 11/11, 16/16 | acronyms + regional terms (KT, HEOR, I-O, etc.) |

The 9 empty specialties (Nursing, Neurology, General/Vascular Surgery, Midwifery, Pharmacy, the single-term psychology/psychiatry ones) are **empty by design** — verified to have no regional variant. Match those on name. **Do not treat them as missing data.**

---

## Rollup is NOT your job at ingestion

You tag leaves. The **query layer** (the closure table / graph traversal from the tagging-model migration addendum) resolves rollup. So:
- You never compute or store ancestor tags.
- You never need a node's full ancestor chain — only its own code and level.
- The `parent` field is for *your* disambiguation (knowing `OBS-11` sits under `OBS`), not a second tag you write back.

---

## Persistence — `resource_tag`, `taxonomy_closure`, `TAGGED_AS`

Per the **tagging-model migration addendum** (`files/migration_addendum_tagging_model.md`):

**PostgreSQL**

- `compendium.resource_tag` — one row per tag the agent assigns: `(resource_id, taxonomy, node_code)`. Write only the level you tagged; **no ancestor rows**.
- `compendium.taxonomy_closure` — pre-seeded ancestor map: each `node_code` → itself (`depth=0`) + each parent (`depth=1` for MVP two-level taxonomies). Filter queries join `resource_tag` to closure on `ancestor_code` for up-only rollup.

**Neo4j**

- `(Resource)-[:TAGGED_AS]->(TaxonomyNode)` — one edge per tag, same finest-level rule as PG.
- Rollup at query time via variable-length paths from the tagged node up toward the filter ancestor (e.g. `SUBTYPE_OF*0..` for resource types).

Keep PG closure and Neo4j parent edges in sync (same codes, same hierarchy). The closure table is the materialised form of the Neo4j up-traversal.

**Specialty:** agent output uses vocabulary **codes**; the write path resolves `code` → directory **slug** and the `Specialty` node (slugs on specialty leaf nodes in this JSON are for that resolver, not for agent output).

---

## Dual-legacy transition

Existing Compendium resources may still carry legacy fields from the pre-closure classifier:

| Legacy field | What it holds | Status |
|---|---|---|
| `methodology_tags[]` | RS- prefix codes, free-text method names | **Readable** during transition; not the forward write target |
| `thesis_stages[]` | Six **phase** codes (`TH` … `SH`) only | **Readable** during transition; not stage-level (`TH-01` … `SH-04`) |

**Forward canonical model:** `compendium.resource_tag` + `compendium.taxonomy_closure` (PG) and `TAGGED_AS` (Neo4j), using the codes in `cothesis_tag_vocabulary.json`. New ingestion via this vocabulary writes there; legacy arrays remain for backward-compatible reads until fully migrated.

This ingestion agent is **standalone** — not a drop-in for `compendium-web` `classify.ts` (RS- methodology, phase-only thesis, slug-based specialties).

---

## Output contract (per resource)

```json
{
  "resource_id": "...",
  "tags": [
    {"taxonomy":"methodology","code":"OBS-12","confidence":0.9},
    {"taxonomy":"thesis","code":"EV-03","confidence":0.8},
    {"taxonomy":"resource_type","code":"systematic_review_tool","confidence":0.95},
    {"taxonomy":"specialty","code":"PSYCH","confidence":0.7}
  ]
}
```
- One row per tag: `taxonomy` + `code` + `confidence`.
- `code` must exist in the vocabulary for that `taxonomy` (validate against it).
- Emit at the finest confident level only; omit a taxonomy rather than tag on a weak guess.
- Carry `confidence` so the QA layer can threshold (e.g. auto-accept ≥0.8, queue 0.5–0.8, drop <0.5).

---

## Validation before you write tags
- Every emitted `code` resolves to a node in `cothesis_tag_vocabulary.json` for its `taxonomy`.
- No tag emitted at a level the taxonomy doesn't have (no "subtype" for `foundation_skill`).
- No parent+child pair for the same resource in the same taxonomy (the redundant double-tag rule 1 forbids).
- Cross-check against `cothesis_demo_resources_retagged.json` — 14 worked examples tagged this way.
