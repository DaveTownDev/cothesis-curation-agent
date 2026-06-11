# Gold eval cases

Per-case ADK eval fixtures for the CoThesis pipeline. Each file is one hand-curated or HITL-exported case.

## Layout

- One JSON file per case: `{eval_id}.json` (seed/synthetic) or `{resource_code}.json` (HITL export).
- JSON Schema: [`../schemas/gold_case.schema.json`](../schemas/gold_case.schema.json)
- Aggregated ADK evalset (do not edit by hand): [`../gold_set.json`](../gold_set.json)

## Case shape

Cases extend the ADK `EvalCase` with CoThesis metadata:

| Field | Required | Purpose |
|-------|----------|---------|
| `eval_id` | yes | Stable sort key and ADK case id |
| `source.resource_code` | yes | Compendium / queue identifier |
| `source.origin` | yes | `seed` \| `hitl` \| `synthetic` |
| `source.prompt_versions` | no | Agent prompt versions at capture |
| `source.failure_mode` | no | Human failure label for prompt-lab |
| `expected_classification` | no | Hand-labeled taxonomy block |
| `conversation` | yes | ADK session turns + rubrics |

`expected_classification` may use flat Firestore fields (`resource_type_code`, `methodology_codes`, …) and/or vocabulary-native `tags[]`.

## Workflow

```bash
# After adding or editing a case file:
python -m scripts.aggregate_gold_set

# Run benchmark (pytest → adk eval → summary):
python -m scripts.run_benchmark
python -m scripts.run_benchmark --check-regression
```

Only `scripts/aggregate_gold_set.py` writes `eval/gold_set.json`. Commit both the per-case file and the regenerated monolith.

## Origins

- **seed** — migrated from the original 20-case monolith or demo fixtures
- **hitl** — exported from the review console after human correction (WS-B)
- **synthetic** — constructed for coverage without a live resource

Target: ≥30 cases total, ≥5 with `origin: "hitl"` after console wiring lands.
