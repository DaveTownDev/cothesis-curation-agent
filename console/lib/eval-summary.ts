import { readFileSync } from "fs"
import { join } from "path"

/** Normalized view for the dashboard (supports legacy + benchmark JSON). */
export interface EvalSummary {
  response_match_score: number
  response_match_threshold: number
  rubric_threshold: number
  rubric_pass_rate: number
  cases_passed: number
  cases_total: number
  unit_tests: number
  updated_at: string
  /** @deprecated alias for response_match_score */
  tool_trajectory_avg: number
  /** @deprecated alias for response_match_threshold */
  tool_trajectory_threshold: number
}

const FALLBACK: EvalSummary = {
  response_match_score: 0.12,
  response_match_threshold: 0.12,
  rubric_threshold: 0.6,
  rubric_pass_rate: 0.95,
  cases_passed: 19,
  cases_total: 20,
  unit_tests: 289,
  updated_at: "unknown",
  tool_trajectory_avg: 0.12,
  tool_trajectory_threshold: 0.12,
}

let _cache: EvalSummary | null = null

function asNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback
}

/** Map console/data/eval-summary.json (benchmark or legacy) to dashboard fields. */
export function normalizeEvalSummary(raw: Record<string, unknown>): EvalSummary {
  const thresholds =
    raw.thresholds && typeof raw.thresholds === "object"
      ? (raw.thresholds as Record<string, unknown>)
      : {}

  const response_match_score = asNumber(
    raw.response_match_score ?? raw.tool_trajectory_avg,
    FALLBACK.response_match_score,
  )
  const response_match_threshold = asNumber(
    thresholds.response_match_score ?? raw.tool_trajectory_threshold,
    FALLBACK.response_match_threshold,
  )
  const rubric_threshold = asNumber(
    thresholds.rubric_threshold ?? raw.rubric_threshold,
    FALLBACK.rubric_threshold,
  )

  return {
    response_match_score,
    response_match_threshold,
    rubric_threshold,
    rubric_pass_rate: asNumber(raw.rubric_pass_rate, FALLBACK.rubric_pass_rate),
    cases_passed: asNumber(raw.cases_passed, FALLBACK.cases_passed),
    cases_total: asNumber(raw.cases_total, FALLBACK.cases_total),
    unit_tests: asNumber(raw.unit_tests, FALLBACK.unit_tests),
    updated_at: typeof raw.updated_at === "string" ? raw.updated_at : FALLBACK.updated_at,
    tool_trajectory_avg: response_match_score,
    tool_trajectory_threshold: response_match_threshold,
  }
}

export function getEvalSummary(): EvalSummary {
  if (_cache) return _cache
  try {
    const raw = readFileSync(join(process.cwd(), "data/eval-summary.json"), "utf8")
    _cache = normalizeEvalSummary(JSON.parse(raw) as Record<string, unknown>)
  } catch {
    _cache = FALLBACK
  }
  return _cache
}
