# CoThesis Curation Agent — Demo Script (5 min)

## Setup before recording
- Console open: https://console-791873451733.us-central1.run.app — log in with passcode `cothesis-demo-2026`
- ADK Web UI open (authenticated): https://cothesis-agent-791873451733.us-central1.run.app/dev-ui
- Cloud Trace open: https://console.cloud.google.com/traces/list?project=cothesis-curation-agent
- Firestore open: https://console.cloud.google.com/firestore/databases/-default-/data?project=cothesis-curation-agent
- Screen recorder ready (Loom, OBS, or QuickTime)

---

## Segment 1 — Problem + architecture (30s)

**Say:** "Knowing how to do research is unevenly distributed. The CoThesis Compendium is a free, openly searchable global archive of research methodology resources. The problem: curating it by hand doesn't scale. We have over 4,000 resources queued and not one has reached publishable quality, because the editorial work is the constraint."

**Show:** `docs/AGENTS_SPEC.md` or the agent graph diagram — briefly walk through the 8 agents in order: Discovery → Appraisal → Classification → Editorial → Reconciliation → QC Panel → Arbiter → [human].

**Say:** "Each step is a specialist agent. The arbiter routes only the uncertain ones to a human curator — everything else publishes automatically."

---

## Segment 2 — Live pipeline run (90s)

**Navigate to:** ADK Web UI → `agents` app → New session.

**Type this prompt:**
```
Curate one article for SYN-01 (Narrative Systematic Review). 
Focus on: PRISMA reporting standard.
```

**While it runs, narrate:**
- "Discovery is querying OpenAlex and PubMed via MCP…"
- "Appraisal is scoring methodological quality across 6 dimensions…"
- "Classification is grounding the type against our Vertex AI Search taxonomy…"
- "Editorial is drafting the plain-language description — the words a novice would actually search…"
- "QC panel is running 4 evaluators: AI pattern scanner, voice reviewer, jargon check, badge check…"
- "Arbiter is computing the composite score and routing…"

**When complete:** show the final output — routing decision (auto_accept or review_needed), quality_score, proposed_badges.

---

## Segment 3 — Cloud Trace waterfall (30s)

**Navigate to:** Cloud Trace → Latest traces → click the most recent one.

**Show:** the span tree — each agent as a span, LLM calls nested within, tool calls visible.

**Say:** "Every agent invocation, LLM call, and tool call emits an OpenTelemetry span. This is the full audit trail of how a resource moved through the pipeline — latency, token counts, grounding confidence, all visible."

---

## Segment 4 — Console: review queue → approve (60s)

**Navigate to:** https://console-791873451733.us-central1.run.app (already logged in).

**Show:** Dashboard — pipeline stats, eval score band, pending review count.

**Click into a pending review item** from the queue.

**Highlight the four description slots:**
- Short description (always visible)
- Long AI assessment summary (always visible)
- Plain breakout card: "This is the jargon-free layer — what a research-naive person would search for."
- Quality bar with the 6 dimensions (expand it)

**Click Approve:** tick all checklist items → Approve.

**Show:** Firestore — navigate to the `resources` collection → show the newly written record with `editorial_status: approved`, `editorial_reviewed_by`, `editorial_reviewed_at`.

**Say:** "The human approves, the record is written to the live Compendium store with full provenance."

---

## Segment 5 — Arbiter routing demo (30s)

**In the ADK Web UI**, run a second prompt designed to trigger review:
```
Curate one resource for EVAL-01. Consider a resource with limited methodology alignment.
```

**Show the arbiter output:** routing = `review_needed`, and the reason string explaining which signal fell below threshold.

**Say:** "The arbiter only routes to human review when signals are genuinely uncertain — high-confidence items publish automatically. This is how a two-person team can curate at archive scale."

---

## Segment 6 — Eval scoreboard (30s)

**Navigate to:** ADK Web UI → `agents` app → Evals tab (or show the eval results JSON).

**Show:** `response_match_score`, `rubric_based_final_response_quality_v1` scores across the 20-case gold set.

**Say:** "The gold set covers 4 methodologies × 5 resource types. Tool trajectory scoring confirms the agents fire in the right order; LLM-as-judge scoring confirms editorial quality against hand-curated references."

---

## Segment 7 — What's next (30s)

**Say:** "The pipeline is live on Cloud Run. The next step is to point it at our existing queue of 4,000 resources — that first real batch will be behind the human review gate. The Compendium is where it goes."

**End on:** the console dashboard or the architecture diagram.

---

## Tips
- Keep the total under 5 minutes — judges watch many videos.
- Show real output, not mockups — the live pipeline is the demo.
- If a pipeline run takes too long live, pre-run one and show the saved output in Firestore + the trace.
- Passcode for judges: `cothesis-demo-2026`
