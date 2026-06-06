# Pipeline Quality Analysis — 60 processed resources (2026-06-06)

Evidence-based audit of the 60 real queue resources processed by the deterministic
pipeline. Four layers: pipeline performance, data quality/completeness, URL liveness,
and source-accuracy (each record vs its live source). Per-record results are written to
the `qa_audit` field on each `review_queue` doc. Raw data: `/tmp/cothesis_audit.json`
(data quality + URL), `/tmp/cothesis_source_verdicts.json` (60 source comparisons).

---

## Executive summary

The pipeline **runs reliably and writes complete, schema-valid records** — but **classification accuracy is the weak point**, and the pipeline **does not guard against bad source data** in the queue.

| Layer | Result |
|---|---|
| Pipeline performance | ✅ Stable. 0 crashes. Pure-code stages instant; LLM stages recover from transient 504s via backoff/fallback. |
| Data quality (schema/vocab) | ✅ 0 publish-blocking failures; all 60 schema-valid. Known field gaps on all 60 (`type_fields`, `time_to_consume`, `content_format`). |
| URL liveness | ⚠️ ~13/60 genuinely dead/unverifiable; the rest live (32 httpx "dead" were mostly publisher bot-blocks — 18 confirmed reachable via WebFetch). |
| **Source accuracy** | ❌ **7 pass / 24 warn / 29 fail.** Dominant cause: **wrong methodology code (40/60)** and **wrong resource_type (19/60)**. Editorial *writing* is mostly accurate (50/60). |

**The one-line takeaway:** the editorial layer (descriptions, plain-language) is good; the **classification layer is mis-assigning methodology codes and resource types because the deterministic pipeline classifies without grounding**, and the pipeline enriches dead/fabricated sources instead of flagging them.

---

## 1. Pipeline performance & API interactions

**Stage latency** (from `pipeline_state`, n=52 distinct; medians):

| Stage | Median | p90 | Max | Notes |
|---|---|---|---|---|
| discovery→appraisal | 17.2s | 107s | 281s | **bottleneck** — metadata fetch + appraisal LLM (+retries/504s) |
| appraisal→classification | 3.6s | 4.4s | 7.3s | Flash-Lite, fast |
| classification→editorial | 10.8s | 15.4s | 18.6s | Flash |
| editorial→reconciliation | 1.0s | — | 1.9s | **pure code** |
| reconciliation→QC | 0.3s | — | 1.0s | **pure code** |
| QC→arbiter | 0.7s | — | 0.9s | **pure code** |
| **total** | **34s** | **124s** | **302s** | ~99% of wall-clock is the 3 LLM stages |

**API interactions across the 5 batch runs:**
- **OpenAlex metadata: 14 × 404** — fetch-by-DOI fails on books/guidelines (DOIs not in OpenAlex) and on fabricated DOIs. Handled (returns `{}`, appraisal proceeds), but **no fallback chain** (OpenAlex→PubMed→Crossref), so metadata is simply absent for those.
- **Gemini 504 DEADLINE_EXCEEDED: 11** — all transient, all recovered by the backoff + 3.x fallback added this session. Confirms that hardening works.
- **0 unrecovered errors**; **0 crashes**.

**Model usage:** 50 drafts on `gemini-3-flash-preview`, 10 on `gemini-3.5-flash` — all Gemini 3.x (credit-covered). Quality scores 67–98.

**Observability gap:** the deterministic batch runs **in-process** (not the deployed `/run`), so **emits no Cloud Trace**. Evidence lives only in stdout logs + `pipeline_state`. No per-run metrics (latency/token/API counts) are persisted.

---

## 2. Data quality & completeness

Read-only audit of all 60 embedded `draft_records` (`scripts/audit_records.py`):

- **0 publish-blocking failures.** Every record has the 5 required fields (resource_code, title, url, resource_type_code, editorial_description) and valid value ranges (quality_score ∈ [0,100], routing signals ∈ [0,1]).
- **No invalid controlled-vocab values** — all methodology codes are platform-format (SYN/OBS/EVAL), all badges canonical, all stage codes valid THESIS. (Validity ≠ correctness — see §4.)
- **Universal completeness gaps (all 60):** `type_fields` empty, `time_to_consume` absent, `content_format` absent. These are unimplemented enrichment fields, not regressions.
- **4 records** have empty `methodology_codes`; **2** empty `discipline_codes`.
- **Integrity: 8 `resource_code` collisions.** Duplicate source resources (e.g. the AI-classification article ×2) derive identical kebab codes; `pipeline_state`/`draft_records` (keyed by code) overwrote one another (60 records → 52 pipeline_state docs), while `review_queue` (auto-id) kept duplicates. Within-batch duplicates are not deduped — `reconciliation` only checks the (empty) published `resources` collection.

---

## 3. URL liveness

httpx probe (bot UA): 25 live, 32 "dead", 3 unreachable. **But reconciled against Phase-4 WebFetch, 18 of those 32 "dead" served real content** — they are publisher anti-bot 403/429s, not dead links. **Genuinely dead/unverifiable ≈ 13** (see §4 — overlaps with fabricated sources). Takeaway: a naive HTTP check over-reports dead links for academic publishers; verification needs a real fetch or DOI-resolution check.

---

## 4. Source accuracy & appropriateness (the core finding)

60 Claude agents fetched each source and compared it to our record (no Vertex cost). Results:

- **Verdict: 7 pass · 24 warn · 29 fail**
- **type_match: 30 yes · 19 no · 11 unsure**
- **description_accurate: 38 yes · 12 minor · 1 no · 9 unsure** ← *the writing is mostly sound*
- **fetchable: 17 full · 22 partial · 21 no** (paywalls/bot-blocks limit full verification)

**Root causes (across 60):**

| Root cause | Count | Example |
|---|---|---|
| **Wrong methodology code** | **40** | "A retrospective chart review…" tagged **EVAL-01** (clinical audit) — should be **OBS-01**. "MyDispense… a scoping review" tagged **SYN-01** — should be **SYN-02**. |
| Hallucinated claim | 25 | summaries assert specifics the source doesn't state (often minor; sometimes because the source is unverifiable) |
| **Wrong resource_type** | **19** | PAHO Open Data portal, Russian State Register, NIH funding call, and a Wiley textbook all typed as **"article"** |
| **Dead / fabricated source** | **13** | `10.1001/jama.2021.1000` — DOI 404s, no such JAMA article in PubMed/web; **the source itself is fabricated** in the queue, yet the pipeline wrote a confident "comprehensive systematic review" description for it |
| Description inaccurate | 13 | overstatement (e.g. an observational chart review described as "validating therapeutic efficacy") |

**7 that passed** (accurate + appropriate): pypiserver, New Principles of Best Practice in Clinical Audit, Introduction to Meta-Analysis, GRACE Checklist, A Worked Example of Meta-Aggregation, vertigo health-services-utilization article, SAMHSA Data.

### Why classification is wrong: no grounding in the deterministic path
The methodology-card grounding (`VertexAiSearchTool`) lives only in the **interactive** orchestrator. The **deterministic** pipeline's classification stage is a bare LLM call with the classification prompt — **no grounding**. So it confuses adjacent MVP methods (OBS-01 vs EVAL-01, SYN-01 vs SYN-02) and over-defaults `resource_type` to "article". Compounding it: the queue contains many resources **outside the 4 MVP methodologies** (cohort studies, RCTs, D&I research, data portals, funding calls), and the pipeline force-fits one of the 4 codes instead of routing "no MVP methodology → human".

---

## 5. Root-cause → prioritised fix plan

### P0 — accuracy-critical (do before any more imports)
1. **Ground the methodology classification.** Inject the 4 methodology-card definitions (`data/methodologies/*.md`) into the deterministic classification payload, or call grounding before classifying. Disambiguates OBS-01/EVAL-01 and SYN-01/SYN-02. → `agents/pipeline/deterministic.py` (classification stage), `agents/prompts/classification.md`.
2. **Stop force-fitting methodology codes.** If the source clearly isn't one of the 4 MVP methods, emit `methodology_codes: []` + route `review_needed` with reason "outside MVP methodologies" rather than a wrong code. → classification stage + arbiter reason.
3. **Respect the source's real resource_type.** Pass the queue's original `resource_type` as a strong prior and instruct the classifier not to default to "article"; books/datasets/funding/video must keep their type. → classification payload + prompt.
4. **Guard against dead/fabricated sources.** Before appraisal, resolve the URL/DOI; if it 404s or the DOI doesn't resolve, route `review_needed` flagged "unverified source" and **do not** generate confident editorial copy. → `deterministic.py` pre-appraisal check (reuse `scripts/audit_records.test_url` + a doi.org resolve).

### P1 — integrity & quality
5. **Unique resource_code.** Append a short DOI/URL hash so duplicates don't collide/overwrite. → `derive_resource_code`.
6. **Within-batch dedup.** Dedup against `draft_records`/`review_queue`, not just published `resources`. → reconciliation stage.
7. **Curb hallucination.** Constrain appraisal/editorial prompts to source-supported claims only; when metadata is absent, say less. → `agents/prompts/{appraisal,editorial}.md`.
8. **Metadata fallback chain.** OpenAlex → PubMed → Crossref so book/guideline DOIs still enrich. → `agents/appraisal/tools.py`.

### P2 — completeness & ops
9. Populate `content_format`, `time_to_consume`, and `type_fields` (field-maps exist in `docs/field_maps/`).
10. Surface `qa_audit` in the console (the flags are already written; needs a UI column/badge). → `console/`.
11. Persist per-run metrics (latency, model, API hits, outcomes) to a `pipeline_runs` collection for observability without Cloud Trace.

---

## 6. Per-record flags
Each `review_queue` doc now has a `qa_audit` map: `{data_quality, dq_issues[], url_status, source_verdict, fetchable, type_match, methodology_plausible, description_accurate, source_issues[], hallucinations[], source_notes, checked_at}`. Filter the queue by `qa_audit.source_verdict == "fail"` to triage the 29 worst first.

## 7. Verification performed
- Data-quality + URL script ran clean over all 60 (`scripts/audit_records.py`).
- Source workflow returned 60/60 verdicts (reconciled to 60).
- URL liveness cross-checked: 18 httpx-"dead" confirmed reachable via WebFetch → true-dead ≈ 13.
- Spot-checks confirm the pattern: chart-review→EVAL-01 (OBS-01 correct), scoping→SYN-01 (SYN-02 correct), data-portal→article.

---

## 8. After the fixes — re-run + re-audit (2026-06-06)

All P0/P1/P2 fixes were implemented (Waves A–E) and the **same selection was re-run through the fixed pipeline** and re-audited with the identical tooling (`scripts/audit_records.py` + the 50-agent source-accuracy workflow).

### What "the 60" actually was
The cached selection of 60 turned out to be **51 unique resources + 8 duplicate copies + 1 record not present in the queue** (a manual addition). The 8 duplicates are precisely the within-batch duplication that **B2 now prevents** — so the re-run processes the **51 unique resources** (→ 50 review_queue docs: 44 `review_needed`, 6 `auto_accept`, 1 `auto_exclude` for a true duplicate). Re-running the 8 duplicate copies is unnecessary; the new dedup would `auto_exclude` them (verified in smoke).

### Source accuracy (the core metric)

| Metric | Before (60) | After (50) |
|---|---|---|
| **Verdict** | 7 pass · 24 warn · **29 fail** | **33 pass · 9 warn · 8 fail** |
| **Resource-type** | 19 wrong | **41 match · 3 mismatch · 6 uncertain** |
| **Methodology** | **40 wrong** | **13 plausible · 1 implausible · 36 n/a** (correctly empty) |
| **Description accuracy** | 25 hallucinated/inaccurate | **45 accurate · 3 overstated · 1 inaccurate · 1 uncertain** |

Pass rate **12% → 66%**; methodology errors **40 → 1**; type errors **19 → 3** (+6 uncertain where the source is bot-blocked/unconfirmable).

### The remaining 8 fails are mostly the pipeline doing the *right* thing
- **4 are dead/fabricated/unreachable sources** the pipeline correctly short-circuited to `review_needed` with **no fabricated description** — the fabricated JAMA DOI (`10.1001/jama.2021.1000`, 404), the unresolvable mirikizumab chart-review DOI, ROSe (`roser.org`, ECONNREFUSED), and one AWS-docs page confirmable only indirectly. Before, these got confident invented write-ups; now they get an empty minimal record flagged for a human.
- **~3–4 are residual type mismatches** — review articles/scales whose titles contain the word "Guidelines" still type as `reporting_guideline` (e.g. *Guidelines for diagnostic tests…*, RoBiNT scale, *Guidelines for reporting non-randomised pilot…*). A title-vs-content nuance for a future pass; not a regression.
- **1 implausible methodology** (institutional-use-of-national-clinical-audits) — down from 40.

### Completeness & integrity

| Metric | Before | After |
|---|---|---|
| `resource_code` collisions | present | **none** (`{}`) |
| `type_fields` populated | 0/60 | **34/50** (16 warn where free sources returned nothing) |
| `content_format` / `time_to_consume` | 0/60 | **44/50** |
| Pipeline errors | 0 | **0** |
| Within-batch dedup | none | **1 `auto_exclude`** (true duplicate caught) |

### Verification
- `scripts/rerun_60.py --clear` re-ran the 51 unique resources (gemini-3.5-flash + gemini-3.1-flash-lite, both credit-covered); `pipeline_runs/rerun60-*` metrics doc written.
- `scripts/audit_records.py` re-ran clean; `resource_code_dupes: {}`.
- 50-agent source-accuracy workflow returned 50/50 verdicts; `scripts/write_qa_audit.py` wrote `qa_audit` to all 50 review_queue docs (console QA column/panel render them).
- 269 pytest tests green (24 new for source-check, enrichment, no-MVP routing, completeness, resource_code hashing).
