import { Suspense } from "react"
import { requireAuth } from "@/lib/auth"
import { getReviewQueue } from "@/lib/firestore"
import {
  parseReviewQueueFilters, isCompactView, reviewDetailHref, currentPreset,
  queueQueryString,
} from "@/lib/queue-filters"
import { Badge } from "@/components/ui/badge"
import { QueueFilters } from "@/components/QueueFilters"
import { TriagePresets } from "@/components/TriagePresets"
import { ReviewQueueTable } from "@/components/ReviewQueueTable"

export const metadata = { title: "Review queue — CoThesis" }

export const revalidate = 0

function qualityColour(score: number): string {
  if (score >= 80) return "#289642"
  if (score >= 60) return "#f59e0b"
  return "#dc2626"
}

export default async function ReviewQueuePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>
}) {
  await requireAuth()
  const sp = await searchParams
  const compact = isCompactView(sp)
  const preset = currentPreset(sp)
  const filters = parseReviewQueueFilters(sp)
  const detailQuery = queueQueryString(sp)

  let items: Awaited<ReturnType<typeof getReviewQueue>> = []
  let error: string | null = null
  try {
    items = await getReviewQueue(filters)
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load queue"
  }

  const avgQuality = items.length
    ? Math.round(items.reduce((s, i) => s + (i.draft_record?.quality_score ?? 0), 0) / items.length)
    : null

  const startHref = items.length > 0 ? reviewDetailHref(items[0].id, sp) : null

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="font-serif text-3xl font-semibold text-[#0E3A27]">Review queue</h1>
          <Badge variant="secondary">{items.length} pending</Badge>
          {avgQuality !== null && (
            <span className="text-sm text-[#6b7280]">
              avg quality: <strong style={{ color: qualityColour(avgQuality) }}>{avgQuality}</strong>
            </span>
          )}
          {startHref && (
            <a href={startHref} className="text-sm font-medium text-[#289642] hover:underline">
              Start reviewing →
            </a>
          )}
        </div>
        <Suspense fallback={null}>
          <QueueFilters />
        </Suspense>
      </div>

      <Suspense fallback={null}>
        <TriagePresets active={preset} />
      </Suspense>

      <p className="text-xs text-[#9ca3af]">
        Select rows for bulk approve/reject. Use <strong>Ready to clear</strong> + bulk approve for high-throughput sessions.
      </p>

      {error && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {error}
        </div>
      )}

      {!error && items.length === 0 && (
        <div className="rounded-xl border border-[#d4cfc5] bg-white p-12 text-center space-y-3">
          <p className="text-[#6b7280]">No items match the current filters.</p>
        </div>
      )}

      {items.length > 0 && (
        <ReviewQueueTable items={items} compact={compact} detailQuery={detailQuery} />
      )}
    </div>
  )
}
