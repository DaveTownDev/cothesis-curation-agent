export const REQUEUE_STAGES = [
  { value: "classification", label: "Fix classification / taxonomy" },
  { value: "enrichment", label: "Re-fetch metadata (enrichment)" },
  { value: "editorial", label: "Rewrite descriptions" },
  { value: "other", label: "Other — specify below" },
] as const

export type RequeueStage = (typeof REQUEUE_STAGES)[number]["value"]

export function formatRequeueReason(stage: RequeueStage, note: string): string {
  const trimmed = note.trim()
  const label = REQUEUE_STAGES.find((s) => s.value === stage)?.label ?? stage
  if (stage === "other") return trimmed
  return trimmed ? `[${stage}] ${label}: ${trimmed}` : `[${stage}] ${label}`
}
