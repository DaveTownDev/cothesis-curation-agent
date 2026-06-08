import { readFileSync } from "fs"
import { join } from "path"

export interface EvalSummary {
  tool_trajectory_threshold: number
  tool_trajectory_avg: number
  rubric_threshold: number
  rubric_pass_rate: number
  cases_passed: number
  cases_total: number
  unit_tests: number
  updated_at: string
}

const FALLBACK: EvalSummary = {
  tool_trajectory_threshold: 0.7,
  tool_trajectory_avg: 0.7,
  rubric_threshold: 0.7,
  rubric_pass_rate: 0.95,
  cases_passed: 19,
  cases_total: 20,
  unit_tests: 289,
  updated_at: "unknown",
}

let _cache: EvalSummary | null = null

export function getEvalSummary(): EvalSummary {
  if (_cache) return _cache
  try {
    const raw = readFileSync(join(process.cwd(), "data/eval-summary.json"), "utf8")
    _cache = JSON.parse(raw) as EvalSummary
  } catch {
    _cache = FALLBACK
  }
  return _cache
}
