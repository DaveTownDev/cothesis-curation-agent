"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PanelDetail } from "@/components/PanelDetail"
import { CheckCircle, Copy, ChevronDown, ChevronUp } from "lucide-react"
import type {
  DraftRecord, PanelResult, PipelineStateDoc, DraftDoc, QualityDimension,
} from "@/lib/firestore"

const TABS = ["Quality", "Panel", "Classification", "Provenance"] as const
type Tab = typeof TABS[number]

const STAGE_LABELS: Record<string, string> = {
  discovered: "Discovered", appraised: "Appraised", classified: "Classified",
  edited: "Editorial", reconciled: "Reconciled", qc_panel: "QC Panel",
  arbiter: "Arbiter",
}
const STAGE_KEYS: Array<[string, keyof PipelineStateDoc]> = [
  ["Discovered", "discovered_at"],
  ["Appraised", "appraised_at"],
  ["Classified", "classified_at"],
  ["Editorial", "edited_at"],
  ["Reconciled", "reconciled_at"],
  ["QC Panel", "qc_panel_at"],
  ["Arbiter", "arbiter_decision_at"],
]

const METHODOLOGY_LABELS: Record<string, string> = {
  "SYN-01": "Narrative Systematic Review", "SYN-02": "Scoping Review",
  "OBS-01": "Retrospective Chart Review", "EVAL-01": "Clinical Audit",
}
const STAGE_CODE_LABELS: Record<string, string> = {
  TH: "Thesis Design", HI: "Health Impact", EV: "Evidence", ST: "Statistics", IN: "Interpretation", SH: "Sharing",
}

function DimBar({ name, dim }: { name: string; dim: QualityDimension }) {
  const colour = dim.score >= 70 ? "#289642" : dim.score >= 50 ? "#f59e0b" : "#dc2626"
  return (
    <div className="space-y-0.5">
      <div className="flex items-center gap-2">
        <span className="text-xs w-32 shrink-0 capitalize text-[#4a6741] font-medium">
          {name.replace(/_/g, " ")}
        </span>
        <div className="flex-1 h-1.5 bg-[#e8e4dc] rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${dim.score}%`, backgroundColor: colour }} />
        </div>
        <span className="text-xs font-mono w-6 text-right" style={{ color: colour }}>
          {Math.round(dim.score)}
        </span>
        <span className="text-[10px] text-[#9ca3af] w-8 text-right">
          ×{dim.weight.toFixed(2)}
        </span>
      </div>
      {dim.reasoning && (
        <p className="text-[11px] text-[#6b7280] ml-[8.5rem] leading-relaxed">{dim.reasoning}</p>
      )}
    </div>
  )
}

function SignalBar({ label, value, max = 1, colour }: { label: string; value: number; max?: number; colour: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs w-36 shrink-0 text-[#4a6741]">{label}</span>
      <div className="flex-1 h-1.5 bg-[#e8e4dc] rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${(value / max) * 100}%`, backgroundColor: colour }} />
      </div>
      <span className="text-xs font-mono" style={{ color: colour }}>
        {max === 1 ? value.toFixed(2) : Math.round(value)}
      </span>
    </div>
  )
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      type="button"
      aria-label="Copy pipeline run ID"
      onClick={() => { navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500) }}
      className="text-[#6b7280] hover:text-[#0E3A27] transition-colors ml-1 focus:outline-none focus:ring-2 focus:ring-[#289642] rounded"
      title="Copy"
    >
      {copied ? <CheckCircle size={12} className="text-[#289642]" /> : <Copy size={12} />}
    </button>
  )
}

interface Props {
  draft: DraftRecord
  panel: PanelResult | Record<string, unknown>
  pipelineState: PipelineStateDoc | null
  draftDoc: DraftDoc | null
}

export function PipelineInspector({ draft, panel, pipelineState, draftDoc }: Props) {
  const [tab, setTab] = useState<Tab>("Quality")
  const arbiter = pipelineState?.arbiter_decision
  const classification = pipelineState?.classification_result

  return (
    <Card className="h-full">
      {/* Tab bar */}
      <CardHeader className="pb-0">
        <div className="flex gap-1 border-b border-[#e8e4dc]">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-2 text-xs font-medium rounded-t transition-colors -mb-px border-b-2 ${
                tab === t
                  ? "border-[#289642] text-[#0E3A27]"
                  : "border-transparent text-[#6b7280] hover:text-[#0E3A27]"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">

        {/* ── Quality tab ─────────────────────────────────────────────────── */}
        {tab === "Quality" && (
          <div className="space-y-4">
            {/* Scores */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-[#F8F5EE] rounded-lg p-3 text-center">
                <div className={`text-3xl font-bold ${draft.quality_score >= 80 ? "text-[#289642]" : draft.quality_score >= 60 ? "text-[#f59e0b]" : "text-red-600"}`}>
                  {Math.round(draft.quality_score)}
                </div>
                <div className="text-xs text-[#6b7280] mt-0.5">quality score</div>
              </div>
              <div className="bg-[#F8F5EE] rounded-lg p-3 text-center">
                <div className={`text-3xl font-bold ${draft.ai_confidence >= 70 ? "text-[#03848F]" : "text-[#f59e0b]"}`}>
                  {Math.round(draft.ai_confidence)}
                </div>
                <div className="text-xs text-[#6b7280] mt-0.5">
                  AI confidence
                  {draft.ai_confidence < 70 && <span className="text-[#f59e0b] ml-1">⚠ &lt;70</span>}
                </div>
              </div>
            </div>

            {/* Routing signals */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide">Routing signals</p>
              <SignalBar label="Relevance score (0-1)" value={draft.relevance_score} colour="#03848F" />
              <SignalBar label="Classification confidence" value={draft.classification_confidence} colour="#289642" />
              {arbiter && (
                <SignalBar label="Composite score (0-100)" value={arbiter.composite_score} max={100} colour="#6366f1" />
              )}
            </div>

            {draft.requires_human_review && (
              <div className="text-xs text-[#f59e0b] bg-amber-50 border border-amber-200 rounded px-3 py-2">
                Human review flagged by pipeline
              </div>
            )}

            {/* Quality dimensions — always expanded */}
            {draft.quality_dimensions && Object.keys(draft.quality_dimensions).length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide">Quality dimensions</p>
                {Object.entries(draft.quality_dimensions).map(([name, dim]) => (
                  <DimBar key={name} name={name} dim={dim} />
                ))}
              </div>
            )}

            {/* Trainee suitability */}
            {draft.trainee_suitability_score !== undefined && draft.trainee_suitability_score !== null && (
              <SignalBar label="Trainee suitability" value={draft.trainee_suitability_score} max={100} colour="#8b5cf6" />
            )}
          </div>
        )}

        {/* ── Panel tab ───────────────────────────────────────────────────── */}
        {tab === "Panel" && <PanelDetail panel={panel} />}

        {/* ── Classification tab ──────────────────────────────────────────── */}
        {tab === "Classification" && (
          <div className="space-y-4">
            {/* Signals */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide">Classification signals</p>
              <SignalBar label="Relevance score" value={draft.relevance_score} colour="#03848F" />
              <SignalBar label="Classification confidence" value={draft.classification_confidence} colour="#289642" />
            </div>

            {classification?.relevance_reasoning && (
              <div>
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-1">Relevance reasoning</p>
                <p className="text-xs text-[#4a5568] leading-relaxed bg-[#F8F5EE] rounded p-2">
                  {classification.relevance_reasoning}
                </p>
              </div>
            )}

            {classification?.skip_reason && (
              <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
                Skip reason: {classification.skip_reason}
              </div>
            )}

            {/* Tags */}
            {[
              { label: "Methodology codes", codes: draft.methodology_codes, labels: METHODOLOGY_LABELS },
              { label: "Stage codes", codes: draft.stage_codes, labels: STAGE_CODE_LABELS },
              { label: "Discipline codes", codes: draft.discipline_codes, labels: {} },
              { label: "Foundation skills", codes: draft.skill_codes, labels: {} },
            ].map(({ label, codes, labels }) => codes?.length > 0 && (
              <div key={label}>
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-1">{label}</p>
                <div className="flex flex-wrap gap-1">
                  {codes.map((c) => (
                    <span key={c} className="text-xs bg-[#e8e4dc] text-[#0E3A27] rounded px-2 py-0.5">
                      {c}{(labels as Record<string, string>)[c] ? ` — ${(labels as Record<string, string>)[c]}` : ""}
                    </span>
                  ))}
                </div>
              </div>
            ))}

            {/* Language */}
            {draft.language_detected && draft.language_detected !== "en" && (
              <div className="text-xs">
                <span className="text-[#4a6741] font-medium">Language detected: </span>
                <span className="bg-amber-100 text-amber-800 rounded px-1">{draft.language_detected}</span>
              </div>
            )}
          </div>
        )}

        {/* ── Provenance tab ──────────────────────────────────────────────── */}
        {tab === "Provenance" && (
          <div className="space-y-4">
            {/* Pipeline run ID */}
            {pipelineState?.pipeline_run_id && (
              <div>
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-1">Pipeline run</p>
                <code className="text-xs text-[#4a5568] bg-[#F8F5EE] px-2 py-1 rounded font-mono">
                  {pipelineState.pipeline_run_id}
                  <CopyButton value={pipelineState.pipeline_run_id} />
                </code>
              </div>
            )}

            {/* Stage timeline */}
            {pipelineState && (
              <div>
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-2">Stage timeline</p>
                <div className="space-y-1">
                  {STAGE_KEYS.map(([label, key]) => {
                    const ts = pipelineState[key] as string | undefined
                    return (
                      <div key={key} className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full shrink-0 ${ts ? "bg-[#289642]" : "bg-[#d4cfc5]"}`} />
                        <span className="text-xs w-24 text-[#4a6741]">{label}</span>
                        <span className="text-xs text-[#6b7280]">
                          {ts ? new Date(ts).toLocaleString("en-AU", { dateStyle: "short", timeStyle: "short" }) : "—"}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Arbiter decision detail */}
            {arbiter && (
              <div>
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-1">Arbiter decision</p>
                <div className={`rounded px-3 py-2 text-xs ${arbiter.routing === "auto_accept" ? "bg-green-50 text-green-800" : "bg-amber-50 text-amber-800"}`}>
                  <span className="font-medium capitalize">{arbiter.routing}</span>
                  {" — "}composite: {arbiter.composite_score.toFixed(1)}
                  <p className="mt-1 text-[11px] opacity-80">{arbiter.reason}</p>
                </div>
              </div>
            )}

            {/* Model info */}
            {(draftDoc?.model_version || draftDoc?.assessed_at) && (
              <div>
                <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-1">Model</p>
                <div className="text-xs text-[#6b7280] space-y-0.5">
                  {draftDoc.model_version && <div>Model: <span className="font-mono">{draftDoc.model_version}</span></div>}
                  {draftDoc.assessed_at && (
                    <div>Assessed: {new Date(draftDoc.assessed_at).toLocaleString("en-AU", { dateStyle: "short", timeStyle: "short" })}</div>
                  )}
                </div>
              </div>
            )}

            {!pipelineState && !draftDoc && (
              <p className="text-xs text-[#6b7280] italic">No provenance data found for this resource.</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
