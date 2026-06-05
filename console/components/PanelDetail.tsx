"use client"

import { CheckCircle, XCircle, Minus } from "lucide-react"
import type { PanelResult, PanelScore } from "@/lib/firestore"

const EVALUATOR_LABELS: Record<string, string> = {
  relevance: "Relevance",
  accuracy: "Accuracy",
  authority: "Authority",
  currency: "Currency",
  accessibility: "Accessibility",
  practical_utility: "Practical utility",
  ebm_level: "EBM level",
  ai_pattern_scanner: "AI pattern scan",
  voice_reviewer: "Voice review",
  plain_jargon_check: "Jargon check",
  badge_check: "Badge check",
  claim_verifier: "Claim verify",
  ref_checker: "Ref check",
}

function ScoreBar({ score }: { score: number }) {
  const colour = score >= 70 ? "#289642" : score >= 50 ? "#f59e0b" : "#dc2626"
  return (
    <div className="flex items-center gap-2 flex-1 min-w-0">
      <div className="h-1.5 flex-1 bg-[#e8e4dc] rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: colour }} />
      </div>
      <span className="text-xs font-mono w-7 text-right" style={{ color: colour }}>
        {Math.round(score)}
      </span>
    </div>
  )
}

interface Props {
  panel: PanelResult | Record<string, unknown>
}

function toPanelScores(panel: PanelResult | Record<string, unknown>): PanelScore[] {
  if (!panel) return []
  if (Array.isArray((panel as PanelResult).panel_scores)) {
    return (panel as PanelResult).panel_scores!
  }
  // Legacy flat object shape — convert
  return Object.entries(panel)
    .filter(([k]) => !["panel_agreement", "overall_pass", "avg_score", "summary"].includes(k))
    .map(([dimension, val]) => {
      if (typeof val === "object" && val !== null) {
        const v = val as Record<string, unknown>
        return {
          dimension,
          score: typeof v.score === "number" ? v.score : 0,
          pass: Boolean(v.pass),
          reasoning: typeof v.reasoning === "string" ? v.reasoning : "",
        }
      }
      return { dimension, score: 0, pass: false, reasoning: "" }
    })
}

export function PanelDetail({ panel }: Props) {
  const scores = toPanelScores(panel)
  const typedPanel = panel as PanelResult
  const agreement = typedPanel.panel_agreement
  const avgScore = typedPanel.avg_score
  const overallPass = typedPanel.overall_pass
  const summary = typedPanel.summary

  if (scores.length === 0) {
    return (
      <div className="text-sm text-[#6b7280] italic">No panel evaluation data available.</div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Summary row */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-[#e8e4dc]">
        <div className="flex items-center gap-3">
          {overallPass !== undefined && (
            <span className={`flex items-center gap-1 text-sm font-medium ${overallPass ? "text-[#289642]" : "text-red-600"}`}>
              {overallPass ? <CheckCircle size={14} /> : <XCircle size={14} />}
              {overallPass ? "Panel passed" : "Panel failed"}
            </span>
          )}
          {agreement !== undefined && (
            <span className="text-xs text-[#6b7280]">
              {Math.round(agreement * 100)}% agreement
            </span>
          )}
          {avgScore !== undefined && (
            <span className="text-xs text-[#6b7280]">avg {Math.round(avgScore)}</span>
          )}
        </div>
      </div>

      {summary && (
        <p className="text-xs text-[#4a6741] bg-[#F8F5EE] rounded px-3 py-2">{summary}</p>
      )}

      {/* Per-evaluator rows */}
      <div className="space-y-2">
        {scores.map(({ dimension, score, pass, reasoning }) => (
          <div key={dimension} className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-xs w-32 shrink-0 text-[#4a6741] font-medium">
                {EVALUATOR_LABELS[dimension] ?? dimension}
              </span>
              <span>
                {pass ? (
                  <CheckCircle size={12} className="text-[#289642]" />
                ) : (
                  <XCircle size={12} className="text-red-500" />
                )}
              </span>
              <ScoreBar score={score} />
            </div>
            {reasoning && (
              <p className="text-[11px] text-[#6b7280] ml-[8.5rem] leading-relaxed">{reasoning}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
