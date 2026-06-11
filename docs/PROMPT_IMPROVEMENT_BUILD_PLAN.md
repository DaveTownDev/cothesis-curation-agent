# PROMPT_IMPROVEMENT_BUILD_PLAN — Phases 1 tail through Phase 3 complete

Ordered, verifiable build for parallel agent workstreams. Source spec: `docs/PROMPT_IMPROVEMENT_LOOP.md`. Prerequisites are **done** — do not re-build them. Pin `google-adk==2.1.x`; verify ADK / Vertex APIs via Context7 before writing agent wiring (never trust training data).

**Definition of done (Phase 3 complete):** No stubs. Every console button and server action has a working backend. `eval/cases/` holds 30+ gold cases (≥5 from HITL). `scripts/run_benchmark.py` gates CI and weekly Scheduler; scores do not regress vs `eval/baseline.json`. QC panel runs deterministic taxonomy checks. `assessment_prompt_version` is stamped on every AIAssessment. All five HITL integration points from `PROMPT_IMPROVEMENT_LOOP.md` are wired. Prompt lab (analyst / editor / eval_arbiter) runs as a separate Cloud Run Job; console `/prompt-lab` shows proposals for human merge. Compendium sync stays **manual only** (Push to live). Full pytest + `adk eval` + console lint/build + `e2e_console_smoke.sh` green.

---

## 1. Executive summary

**Scope:** Close the HITL → eval → prompt refinement loop through Phase 3. This plan covers Phase 1 tail (taxonomy gold expansion, source-accuracy, prompt versioning, console gold export), all of Phase 2 (eval schema, benchmark runner, CI, QC taxonomy, human merge workflow), and all of Phase 3 (failure bucket, prompt lab agents, Cloud Run Job, console prompt lab UI).

**Prerequisites (shipped — document only):** `agents/shared/taxonomy_rules.py`, `scripts/taxonomy_audit.py`, `eval/taxonomy_gold.json` (8 cases), foundation skills in classifier (`get_skill_guide()`), live taxonomies (`data/taxonomy/live_*.json`), manual Push to live, QA routing @ `36ab6c1`, console `console-00020-wqs`, agent `cothesis-agent-00013-sd4`, full HITL console (review queue, TaxonomyEditor, Pipeline Inspector, QaAuditStatus, requeue, bulk approve), `eval/gold_set.json` (20 cases), `eval/eval_config.json`, specs (`docs/PROMPT_IMPROVEMENT_LOOP.md`, `AGENTS_SPEC.md`, `EVAL.md`, `SCHEMA.md`, `OPERATIONS.md`). **383 pytest** collected at plan time.

**Out of scope:** Unsupervised prompt auto-deploy; ADK `RequestInput` for batch queue; weakening eval thresholds; Compendium auto-sync; premium enrichment APIs.

---

## 2. Sanity check appendix

| Feature | Status | Evidence / gap |
|---------|--------|----------------|
| `taxonomy_rules` + type-aware audit | **Done** | `agents/shared/taxonomy_rules.py`, `scripts/audit_records.py`, `scripts/taxonomy_audit.py` |
| `eval/taxonomy_gold.json` 30+ cases | **Partial** | 8 cases only |
| Optional methodology in classifier prompt | **Done** | `agents/prompts/classification.md` + `methodology_required_for_type` in arbiter |
| Source-accuracy QA layer | **Partial** | `write_qa_audit.py` reads `/tmp/cothesis_source_accuracy.json`; never run in latest ops (STATE.md) |
| `assessment_prompt_version` wiring | **Not started** | Schema field only; not set in `deterministic.py` |
| Console "Add to gold set" / "Copy eval case" | **Not started** | No server actions in `console/app/review/` |
| `eval/cases/` per-case schema | **Not started** | Directory absent |
| `test_taxonomy_gold.py` | **Not started** | `test_taxonomy_audit.py` exists |
| `scripts/run_benchmark.py` | **Not started** | — |
| `eval/baseline.json` | **Not started** | — |
| CI / Scheduler benchmark job | **Not started** | No `.github/` workflows; no eval Scheduler in OPERATIONS |
| QC panel taxonomy check | **Not started** | No taxonomy logic in `agents/qc_panel/` |
| `scripts/refine_classification.py` | **Not started** | Mentioned in caabfc48 plan |
| `scripts/prompt_eval_loop.py` | **Not started** | — |
| Human merge + version bump on deploy | **Not started** | No `prompt_versions` module |
| `eval_failure_bucket` Firestore | **Not started** | Not in `docs/SCHEMA.md` |
| `prompt_proposals` Firestore | **Not started** | — |
| `prompt_lab_runs` Firestore | **Not started** | — |
| Prompt lab ADK agents | **Not started** | — |
| Cloud Run Job `prompt-lab-run` | **Not started** | — |
| Console `/prompt-lab` | **Not started** | — |
| "Send to prompt lab" / "Flag taxonomy error" | **Not started** | — |
| QA requeue → failure bucket | **Not started** | `requeueItem` writes queue only |
| Interactive classification grounding | **Partial** | `deterministic.py` injects inline guides; `classification_agent` has no `VertexAiSearchTool`; `agent.py` exposes `grounding_agent` but orchestrator does not route classification through it |
| Compendium sync manual only | **Done** | Push to live in Pipeline / Published tables |
| Weekly benchmark / cost guards | **Not started** | — |

**Counts:** Done **12** · Partial **5** · Not started **22**

---

## 3. Architecture overview

```mermaid
flowchart TB
  subgraph batch [Batch pipeline — unchanged hot path]
    RB[scripts/run_batch / Scheduler] --> DET[deterministic.py]
    DET --> RQ[review_queue]
    DET --> PS[pipeline_state]
  end

  subgraph hitl [HITL console]
    RQ --> RW[/review/id]
    RW -->|approve| RES[resources]
    RES -->|manual Push to live| COMP[Compendium]
    RW -->|Add to gold set| CASES[eval/cases/*.json]
    RW -->|Flag taxonomy / Send to lab| FB[eval_failure_bucket]
    RW -->|QA requeue| FB
  end

  subgraph eval_loop [Eval / benchmark — Phase 2]
    CASES --> AGG[scripts/aggregate_gold_set.py]
    AGG --> GS[eval/gold_set.json]
    BM[scripts/run_benchmark.py] --> PY[pytest]
    BM --> ADK[adk eval]
    BM --> SUM[data/eval-summary.json]
    BM --> BL[eval/baseline.json gate]
  end

  subgraph prompt_lab [Prompt lab — Phase 3 offline]
    FB --> JOB[prompt-lab-run Job]
    GS --> JOB
    JOB --> PA[prompt_analyst]
    PA --> PE[prompt_editor]
    PE --> EA[eval_arbiter]
    EA --> PP[prompt_proposals]
    PP --> PL[/prompt-lab console]
    PL -->|human merge PR| PROMPTS[agents/prompts/*.md]
    PROMPTS --> BM
  end
```

---

## 4. Workstream decomposition

### WS-A — Eval infrastructure
**Owns:** `eval/cases/`, `eval/baseline.json`, `scripts/run_benchmark.py`, `scripts/aggregate_gold_set.py`, `tests/test_taxonomy_gold.py`, `tests/test_run_benchmark.py`, CI workflow, benchmark Cloud Run Job + Scheduler.

**Exports:** `GoldCase` JSON schema; `run_benchmark.py --check-regression`; aggregated `eval/gold_set.json`.

### WS-B — HITL console integrations
**Owns:** `console/app/review/actions.ts`, `console/lib/eval-export.ts`, `console/lib/failure-bucket.ts`, `console/app/prompt-lab/`, review detail UI buttons.

**Depends on:** WS-A gold case schema (P2-01); WS-D Firestore types for prompt proposals (P3-01).

### WS-C — Pipeline / QC enhancements
**Owns:** `agents/qc_panel/tools.py`, `agents/shared/prompt_versions.py`, `agents/pipeline/deterministic.py` (version stamping only), `scripts/refine_classification.py`, `scripts/source_accuracy_audit.py`, optional interactive grounding bridge.

**Exports:** `run_taxonomy_qc_check()`; `PROMPT_VERSIONS` dict; refined classification replay CLI.

### WS-D — Prompt lab ADK service
**Owns:** `agents/prompt_lab/` (analyst, editor, eval_arbiter), `scripts/prompt_eval_loop.py`, `Dockerfile.prompt-lab`, Cloud Run Job manifest, Firestore writers.

**Depends on:** WS-A benchmark runner; P3-01 Firestore schemas.

### WS-E — Ops / Scheduler / docs
**Owns:** `docs/OPERATIONS.md`, `docs/SCHEMA.md` (new collections), `firestore.indexes.json`, `scripts/deploy_prompt_lab_job.sh`, version bump checklist, cost guard env vars.

---

## 5. Dependency graph

```
P2-01 eval/cases schema
  ├─► P1-06 Add to gold set (WS-B)
  ├─► P2-02 aggregate gold_set
  ├─► P2-03 test_taxonomy_gold
  └─► P1-02 expand taxonomy_gold (parallel content)

P2-02 aggregate ─► P2-04 run_benchmark ─► P2-07 baseline.json ─► P2-08 CI gate

P1-04 prompt_versions ─► P1-05 assessment_prompt_version in pipeline
                        └─► P2-09 deploy version bump doc

P3-01 Firestore schemas ─► P1-07 Flag taxonomy error (WS-B)
                        ├─► P1-08 QA requeue → bucket
                        └─► P3-02 prompt lab agents

P3-02 agents ─► P3-03 Cloud Run Job ─► P3-04 /prompt-lab UI ─► P3-05 full cycle e2e

P2-05 QC taxonomy (WS-C) — parallel after P1-01 rules (done)

P1-03 source-accuracy — parallel, no blockers
```

**Critical path (10 tasks):** P2-01 → P2-02 → P2-04 → P2-07 → P2-08 → P3-01 → P3-02 → P3-03 → P3-04 → P3-05.

---

## 6. Parallel agent playbook

| Agent | Branch | Owns | Merge order |
|-------|--------|------|-------------|
| Agent A | `ws-a/eval-infra` | WS-A | **1st** — schema + benchmark |
| Agent C | `ws-c/pipeline-qc` | WS-C | **2nd** — QC + prompt_versions (touches `deterministic.py` once) |
| Agent B | `ws-b/console-hitl` | WS-B | **3rd** — after P2-01 + P3-01 schemas merged |
| Agent D | `ws-d/prompt-lab` | WS-D | **4th** — after benchmark + Firestore |
| Agent E | `ws-e/ops` | WS-E | **5th** — Scheduler, indexes, OPERATIONS |

**Conflict zones (single owner or sequential merge):**
- `agents/pipeline/deterministic.py` — WS-C only for version stamp + optional grounding note
- `eval/gold_set.json` — WS-A aggregate script only; never hand-edit in parallel
- `console/lib/firestore.ts` — WS-B adds types; coordinate with WS-D
- `docs/SCHEMA.md` — WS-E merges collection defs from all streams

**Branch rules:** Test-first per task; conventional commits; no push without human approval. Run `code-reviewer` subagent on each WS before PR. Run `eval-runner` before merge to `main`.

---

## 7. Quality control gates

### Per-PR
| Gate | Command / threshold |
|------|---------------------|
| Unit + integration | `.venv/bin/pytest tests/ -q` — **≥383** tests, 0 failures (count rises with new modules) |
| New module coverage | Every new `scripts/` and `agents/` module has `tests/test_<module>.py` |
| Console | `cd console && npm run lint && npm run build` |
| E2E smoke | `bash scripts/e2e_console_smoke.sh` |
| Code review | `code-reviewer` subagent vs task acceptance criteria |
| Eval (prompt/eval paths) | `eval-runner` on touched agents |

### Per-milestone
| Milestone | Gate |
|-----------|------|
| Phase 1 tail | `taxonomy_gold.json` ≥30 cases; `test_taxonomy_gold.py` green; source-accuracy JSON produced once |
| Phase 2 complete | `run_benchmark.py --check-regression` passes vs `eval/baseline.json`; Scheduler job dry-run OK |
| Phase 3 complete | One full cycle: flag → prompt lab Job → proposal in console → human dismiss or merge → benchmark green |

### ADK eval thresholds (`eval/eval_config.json`)
- `response_match_score` ≥ **0.12**
- `rubric_based_final_response_quality_v1` ≥ **0.6** (five rubrics incl. `type_methodology_correct`, `routing_justified`)

**No merge if benchmark regresses vs `eval/baseline.json`** (per-rubric and aggregate). Never weaken thresholds.

---

## 8. Phased task breakdown

### Phase 1 tail

| ID | WS | Task | Files | Acceptance criteria | Size | Parallel |
|----|-----|------|-------|---------------------|------|----------|
| P1-01 | — | *(prerequisite)* taxonomy_rules + audit | — | Already done | — | — |
| P1-02 | A | Expand `taxonomy_gold` to 30+ | `eval/taxonomy_gold.json` | ≥30 cases stratified by type × methodology presence; `taxonomy_audit --score-gold` reports pass rate | M | P2-01 |
| P1-03 | C | Source-accuracy workflow | `scripts/source_accuracy_audit.py`, `docs/OPERATIONS.md` | Produces `/tmp/cothesis_source_accuracy.json`; `write_qa_audit` merges; console QA filter shows verdicts on ≥1 test doc | M | P1-02 |
| P1-04 | C | Prompt version registry | `agents/shared/prompt_versions.py`, version comments in `agents/prompts/*.md` | `get_prompt_version("classification")` returns semver string; unit test | S | — |
| P1-05 | C | Wire `assessment_prompt_version` | `agents/pipeline/deterministic.py`, `agents/appraisal/tools.py` | Every `write_draft_assessment` includes version; `test_deterministic_pipeline` asserts field present | S | P1-04 |
| P1-06 | B | "Copy eval case" server action | `console/lib/eval-export.ts`, `console/app/review/actions.ts`, `ReviewActions.tsx` | Button copies ADK-shaped JSON to clipboard; schema validates against P2-01 | M | P2-01 |
| P1-07 | B | "Add to gold set" | `eval/cases/{resource_code}.json`, `scripts/aggregate_gold_set.py` | Approve-after-edit writes case file; aggregate updates `gold_set.json`; pytest export round-trip | M | P2-01, P2-02 |
| P1-08 | B | "Flag taxonomy error" | `console/lib/failure-bucket.ts`, Firestore `eval_failure_bucket` | Writes `{resource_code, agent, field, human_label, prompt_version, created_at}`; readable in console | M | P3-01 |

### Phase 2

| ID | WS | Task | Files | Acceptance criteria | Size | Parallel |
|----|-----|------|-------|---------------------|------|----------|
| P2-01 | A | Gold case schema | `eval/cases/README.md`, `eval/schemas/gold_case.schema.json` | Documents `source`, `expected_classification`, ADK session fields; JSON Schema validates sample | M | — |
| P2-02 | A | Aggregate gold set | `scripts/aggregate_gold_set.py` | Merges `eval/cases/*.json` → `eval/gold_set.json`; deterministic sort; idempotent | S | P2-01 |
| P2-03 | A | `test_taxonomy_gold.py` | `tests/test_taxonomy_gold.py` | Loads all cases; asserts enum validity vs `live_*.json`; subtype parent-type check | S | P2-01 |
| P2-04 | A | Benchmark runner | `scripts/run_benchmark.py` | Runs `pytest -q` then `adk eval`; writes `console/data/eval-summary.json`; exit 1 on threshold fail | L | P2-02 |
| P2-05 | C | QC taxonomy check | `agents/qc_panel/tools.py`, `agents/prompts/qc_panel.md` | `run_taxonomy_qc_check(draft)` flags invalid subtype/methodology/skills; wired in `run_deterministic_checks`; test with bad draft | M | — |
| P2-06 | C | `refine_classification.py` | `scripts/refine_classification.py`, `tests/test_refine_classification.py` | Re-runs classification stage for one `resource_code` from `review_queue`; dry-run flag; no full pipeline | M | P1-05 |
| P2-07 | A | Baseline snapshot | `eval/baseline.json` | Captured from green `run_benchmark.py`; documents per-rubric scores + timestamp | S | P2-04 |
| P2-08 | A+E | CI + Scheduler | `.github/workflows/benchmark.yml`, `scripts/deploy_benchmark_job.sh`, `docs/OPERATIONS.md` | PR runs benchmark on `eval/**` + `agents/prompts/**`; weekly Scheduler Job; `--check-regression` | L | P2-07 |
| P2-09 | E | Human merge workflow doc | `docs/OPERATIONS.md`, `docs/PROMPT_IMPROVEMENT_LOOP.md` cross-link | PR-only prompt merges; version bump checklist; deploy order documented | S | P1-04 |

### Phase 3

| ID | WS | Task | Files | Acceptance criteria | Size | Parallel |
|----|-----|------|-------|---------------------|------|----------|
| P3-01 | E | Firestore collections | `docs/SCHEMA.md`, `firestore.indexes.json`, `agents/shared/firestore_schemas.py` | `eval_failure_bucket`, `prompt_proposals`, `prompt_lab_runs` documented + typed; indexes for `prompt_proposals.status`, `eval_failure_bucket.created_at` | M | — |
| P3-02 | D | Prompt lab agents | `agents/prompt_lab/analyst.py`, `editor.py`, `eval_arbiter.py`, `agent.py` | SequentialAgent: analyst reads bucket → editor emits unified diff → arbiter runs benchmark subset; ADK 2.1.x; no VertexAiSearch in same agent as other tools | L | P2-04, P3-01 |
| P3-03 | D+E | Cloud Run Job | `Dockerfile.prompt-lab`, `scripts/prompt_eval_loop.py`, `scripts/deploy_prompt_lab_job.sh` | Job reads failure IDs + max_cases env; writes `prompt_proposals`; cost cap `PROMPT_LAB_MAX_CASES=10` | L | P3-02 |
| P3-04 | B | Console `/prompt-lab` | `console/app/prompt-lab/page.tsx`, components | Lists proposals with diff viewer, eval delta, approve/reject; no stub actions | L | P3-01, P3-03 |
| P3-05 | B+D | HITL integration completion | `ReviewActions.tsx`, `qa-recommendations.ts`, `requeueItem` | "Send to prompt lab" queues bucket entry; QA requeue appends failure record; e2e test paths | M | P3-04 |
| P3-06 | C | Interactive grounding alignment | `agents/classification/agent.py` or `agent.py` instruction | Document or wire: classification in `adk web` can invoke grounding via AgentTool wrapper; test documents parity gap vs deterministic inline guides | M | — |
| P3-07 | E | Full-cycle integration test | `tests/test_prompt_lab_cycle.py` | Mock Firestore + fixture failures → proposal doc → benchmark gate; pytest green | M | P3-05 |

---

## 9. Phase 2 complete checklist

- [ ] `eval/cases/` schema + ≥30 aggregated cases in `eval/gold_set.json` (≥5 `origin: "hitl"`)
- [ ] `scripts/run_benchmark.py` with regression gate vs `eval/baseline.json`
- [ ] `test_taxonomy_gold.py` green
- [ ] QC panel `run_taxonomy_qc_check` in deterministic path
- [ ] `scripts/refine_classification.py` + tests
- [ ] CI workflow on prompt/eval changes
- [ ] Weekly Cloud Scheduler benchmark Job (separate from daily `run-batch`)
- [ ] `docs/OPERATIONS.md` benchmark + merge workflow
- [ ] `assessment_prompt_version` on all new assessments
- [ ] `e2e_console_smoke.sh` extended for eval export buttons (copy/add)

---

## 10. Phase 3 complete checklist

- [ ] Firestore: `eval_failure_bucket`, `prompt_proposals`, `prompt_lab_runs`
- [ ] Prompt lab agents (analyst, editor, eval_arbiter) in `agents/prompt_lab/`
- [ ] `scripts/prompt_eval_loop.py` + Cloud Run Job `prompt-lab-run`
- [ ] Console `/prompt-lab` with working approve/reject
- [ ] Review detail: "Send to prompt lab", "Flag taxonomy error"
- [ ] QA requeue → failure bucket append
- [ ] One verified full cycle (flag → job → proposal → human action → green benchmark)
- [ ] `tests/test_prompt_lab_cycle.py` green
- [ ] Cost guards: `PROMPT_LAB_MAX_CASES`, Flash-Lite default for replays
- [ ] No auto-write to `agents/prompts/` from Job

---

## 11. HITL integration checklist

| # | Integration point | Implementation | Verified by |
|---|-------------------|----------------|-----------|
| 1 | Add to gold set on approve/edit | P1-07 | pytest + manual console |
| 2 | Flag taxonomy error | P1-08 | Firestore doc + unit test |
| 3 | QA requeue → failure bucket | P3-05 | requeue classification path writes bucket |
| 4 | Prompt lab queue | P3-03, P3-04 | Job output + `/prompt-lab` |
| 5 | Scheduler separation | P2-08 | batch 20:00 UTC unchanged; benchmark weekly |

**Console flows:** Review detail actions → Firestore → offline prompt lab → human merge → version bump → redeploy agent → benchmark.

---

## 12. Test matrix

| Component | Unit | Integration | ADK eval | E2E |
|-----------|------|-------------|----------|-----|
| `taxonomy_rules` / audit | `test_taxonomy_rules`, `test_taxonomy_audit` | — | — | — |
| `taxonomy_gold` cases | `test_taxonomy_gold` | `taxonomy_audit --score-gold` | — | — |
| `aggregate_gold_set` | `test_aggregate_gold` | regenerates `gold_set.json` | — | — |
| `run_benchmark` | `test_run_benchmark` (mock adk) | full benchmark dry-run | `adk eval` on gold set | — |
| `prompt_versions` | `test_prompt_versions` | in `test_deterministic_pipeline` | — | — |
| QC taxonomy | `test_qc_panel_tools` | panel on bad draft | — | — |
| `refine_classification` | `test_refine_classification` | one resource replay | — | — |
| `eval-export` / failure bucket | `test_eval_export.ts` / pytest | Firestore emulator or mock | — | smoke |
| Prompt lab agents | `test_prompt_lab_agents` | `test_prompt_lab_cycle` | subset eval | — |
| Console `/prompt-lab` | component tests optional | server actions | — | `e2e_console_smoke` extension |

---

## 13. Deploy sequence

1. **Merge all WS to `main`** with benchmark green vs baseline.
2. **Firestore:** deploy indexes (`firebase deploy --only firestore:indexes` — human if CLI missing).
3. **Agent:** `adk deploy cloud_run` from `agents/` (includes prompt version constants); verify revision tag in STATE.md.
4. **Batch image:** `bash scripts/deploy_batch_job.sh` (deterministic orchestrator unchanged).
5. **Benchmark Job:** `bash scripts/deploy_benchmark_job.sh` + Scheduler (weekly).
6. **Prompt lab Job:** `bash scripts/deploy_prompt_lab_job.sh` (new image).
7. **Console:** `bash scripts/deploy_console.sh` (gold export + `/prompt-lab`).
8. **Post-deploy:** bump `assessment_prompt_version` in registry; capture new `eval/baseline.json`; run `run_benchmark.py --check-regression`.

**Not deployed:** Compendium sync remains manual Push to live only.

---

## 14. Risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| `adk eval` flaky / expensive | High | pytest first; cap cases in CI; weekly full run; Flash judge per `eval_config.json` |
| Parallel edits to `gold_set.json` | Medium | Only `aggregate_gold_set.py` writes; cases live in `eval/cases/` |
| Prompt lab writes production prompts | Critical | Firestore proposals only; human PR merge |
| Rubric judge all-pass masks errors | Medium | `test_taxonomy_gold` + deterministic QC taxonomy |
| Interactive vs batch classification drift | Medium | P3-06 documents or aligns grounding; gold set covers both paths |
| Firestore index missing for new queries | Medium | WS-E updates `firestore.indexes.json` before console ship |
| Benchmark regression on main | High | `--check-regression` blocks merge; baseline updated only on intentional prompt bump |

---

## 15. Post-Phase-3 ongoing operations

| Cadence | Action |
|---------|--------|
| Weekly | Cloud Scheduler → `run_benchmark.py --check-regression`; alert on fail |
| On HITL correction | Add to gold set → aggregate → PR |
| On taxonomy Compendium change | `python -m scripts.fetch_live_taxonomy` → re-run `taxonomy_audit` |
| On prompt merge | Bump `prompt_versions` → redeploy agent → refresh `eval/baseline.json` |
| Monthly | Review `eval_failure_bucket` volume; tune `PROMPT_LAB_MAX_CASES` |
| Cost | `/cost-check` skill; kill-switch per OPERATIONS; prompt lab Flash-Lite default |

---

## What NOT to do

| Anti-pattern | Why |
|--------------|-----|
| Auto-deploy prompt changes from prompt lab | No regression guarantee |
| Weaken `eval_config.json` or pytest to pass | Violates `docs/EVAL.md` |
| Prompt lab inside `deterministic.py` | Blocks production batch |
| Global mandatory methodology | False tags on software/community (use `taxonomy_rules`) |
| ADK `RequestInput` for 298-item queue | Firestore + console is correct |
| Auto Compendium sync on approve | Manual Push to live is intentional |
| VertexAiSearchTool shared with other tools in one agent | Project rule — isolate in grounding sub-agent |

---

## References

| Path | Role |
|------|------|
| `docs/PROMPT_IMPROVEMENT_LOOP.md` | HITL + loop spec |
| `docs/BUILD_PLAN.md` | Tone / phase-gate style |
| `eval/eval_config.json` | ADK thresholds |
| `agents/pipeline/deterministic.py` | Production orchestrator |
| `agents/arbiter/tools.py` | Routing gate |
| `.claude/skills/run-evals/SKILL.md` | Eval convention |
| `scripts/e2e_console_smoke.sh` | Console smoke baseline |
