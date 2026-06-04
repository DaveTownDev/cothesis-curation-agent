# Arbiter agent prompt

Rebuild on Gemini (Pro). Inputs: the Classification output (`relevance_score` + `classification_confidence`, both 0-1) and the QC panel result. Route on the 0-1 signals ONLY — do NOT route on `ai_confidence` (0-100 quality signal, separate layer). Produce a composite judgement and a routing decision via the gate (docs/ARCHITECTURE.md):
```
skip_reason set                                                    -> auto_exclude
classification_confidence >= 0.8 and relevance_score >= 0.6       -> auto_accept (-> publish checklist)
classification_confidence >= 0.8 and relevance_score < 0.3        -> auto_exclude
classification_confidence < 0.5  OR panel disagreement high       -> review_needed (human)
else                                                               -> review_needed
```
Output: `{ "decision": "auto_accept|auto_exclude|review_needed", "composite_score": number, "panel_agreement": number, "reason": string }`. Auto-accepted items still pass the publish checklist; nothing is published without human ratification (the console writes provenance + sets editorial_status=published). Auto-accepted items get sampling audits.
