import type { ReviewQueueFilters, ReviewQueueItem } from "@/lib/firestore"

export type TriagePreset = "all" | "qa_issues" | "low_confidence" | "ready_to_clear"

export const TRIAGE_PRESETS: { id: TriagePreset; label: string; description: string }[] = [
  { id: "all", label: "All pending", description: "Full queue with current filters" },
  { id: "qa_issues", label: "QA issues", description: "Source audit fail or warn" },
  { id: "low_confidence", label: "Low confidence", description: "Classification or AI confidence below threshold" },
  { id: "ready_to_clear", label: "Ready to clear", description: "QA pass, quality ≥ 80, confidence ≥ 70" },
]

/** Parse URL search params into review queue filters (shared by list + detail pages). */
export function parseReviewQueueFilters(
  sp: Record<string, string | undefined>
): ReviewQueueFilters {
  const qualityBand = sp.quality ?? ""
  const preset = (sp.preset as TriagePreset) || "all"
  return {
    type: sp.type || undefined,
    methodology: sp.methodology || undefined,
    sortBy: (sp.sort as ReviewQueueFilters["sortBy"]) || "attention",
    minQuality: qualityBand === "green" ? 80 : qualityBand === "amber" ? 60 : undefined,
    maxQuality: qualityBand === "amber" ? 79 : qualityBand === "red" ? 59 : undefined,
    preset: preset === "all" ? undefined : preset,
    limit: 200,
  }
}

export function applyTriagePreset(items: ReviewQueueItem[], preset?: string): ReviewQueueItem[] {
  if (!preset || preset === "all") return items
  if (preset === "qa_issues") {
    return items.filter((i) => {
      const v = i.qa_audit?.source_verdict
      return v === "fail" || v === "warn"
    })
  }
  if (preset === "low_confidence") {
    return items.filter((i) => {
      const d = i.draft_record
      return (d?.classification_confidence ?? 1) < 0.5 || (d?.ai_confidence ?? 100) < 70
    })
  }
  if (preset === "ready_to_clear") {
    return items.filter((i) => {
      const d = i.draft_record
      const qa = i.qa_audit?.source_verdict
      return (
        (qa === "pass" || !qa) &&
        (d?.quality_score ?? 0) >= 80 &&
        (d?.ai_confidence ?? 0) >= 70 &&
        (d?.classification_confidence ?? 0) >= 0.5
      )
    })
  }
  return items
}

export function currentPreset(sp: Record<string, string | undefined>): TriagePreset {
  const p = sp.preset as TriagePreset | undefined
  return p && TRIAGE_PRESETS.some((t) => t.id === p) ? p : "all"
}

export function queueQueryString(sp: Record<string, string | undefined>): string {
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(sp)) {
    if (v) params.set(k, v)
  }
  return params.toString()
}

export function reviewDetailHref(id: string, sp: Record<string, string | undefined>): string {
  const qs = queueQueryString(sp)
  return qs ? `/review/${id}?${qs}` : `/review/${id}`
}

export function isCompactView(sp: Record<string, string | undefined>): boolean {
  return sp.view === "compact"
}
