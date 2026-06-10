import { Suspense } from "react"
import { requireAuth } from "@/lib/auth"
import { getReviewQueue } from "@/lib/firestore"
import {
  parseReviewQueueFilters, isCompactView, reviewDetailHref, currentPreset,
  queueQueryString,
} from "@/lib/queue-filters"
import { ReviewQueueListSubBar } from "@/components/ReviewQueueListSubBar"
import { QueueFilters } from "@/components/QueueFilters"
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
    <div className="space-y-4">
      <ReviewQueueListSubBar
        itemCount={items.length}
        avgQuality={avgQuality}
        avgQualityColor={avgQuality !== null ? qualityColour(avgQuality) : undefined}
        startHref={startHref}
        preset={preset}
      />

      <h1 className="hitl-page-title">Review queue</h1>

      <p className="text-xs text-[var(--text-body)]">
        Select rows for bulk approve/reject. Use <strong>Ready to clear</strong> + bulk approve for
        high-throughput sessions.
      </p>

      <div className="flex justify-end">
        <Suspense fallback={null}>
          <QueueFilters />
        </Suspense>
      </div>

      {error && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {error}
        </div>
      )}

      {!error && items.length === 0 && (
        <div className="hitl-card p-12 text-center space-y-3">
          <p className="text-[var(--text-body)]">No items match the current filters.</p>
        </div>
      )}

      {items.length > 0 && (
        <ReviewQueueTable items={items} compact={compact} detailQuery={detailQuery} />
      )}
    </div>
  )
}
