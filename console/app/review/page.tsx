import Link from "next/link"
import { Suspense } from "react"
import { requireAuth } from "@/lib/auth"
import { getReviewQueue, type ReviewQueueFilters } from "@/lib/firestore"
import { Badge } from "@/components/ui/badge"
import { QueueFilters } from "@/components/QueueFilters"
import { ExternalLink } from "lucide-react"

export const revalidate = 0

const TYPE_LABELS: Record<string, string> = {
  article: "Article", book: "Book", book_chapter: "Book chapter", video: "Video",
  podcast: "Podcast", software: "Software", reporting_guideline: "Guideline",
  course: "Course", web_guide: "Web guide", template: "Template",
  visual_reference: "Visual", dataset: "Dataset", community: "Community", funding: "Funding",
}

function qualityColour(score: number): string {
  if (score >= 80) return "#289642"
  if (score >= 60) return "#f59e0b"
  return "#dc2626"
}

function MiniBar({ value, max = 100, colour }: { value: number; max?: number; colour: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs font-mono w-6 text-right" style={{ color: colour }}>
        {max === 1 ? value.toFixed(2) : value}
      </span>
      <div className="h-1.5 w-12 bg-[#e8e4dc] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${(value / max) * 100}%`, backgroundColor: colour }}
        />
      </div>
    </div>
  )
}

export default async function ReviewQueuePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string>>
}) {
  await requireAuth()
  const sp = await searchParams

  const qualityBand = sp.quality ?? ""
  const filters: ReviewQueueFilters = {
    type: sp.type || undefined,
    methodology: sp.methodology || undefined,
    sortBy: (sp.sort as ReviewQueueFilters["sortBy"]) || "newest",
    minQuality: qualityBand === "green" ? 80 : qualityBand === "amber" ? 60 : undefined,
    maxQuality: qualityBand === "amber" ? 79 : qualityBand === "red" ? 59 : undefined,
    limit: 200,
  }

  let items: Awaited<ReturnType<typeof getReviewQueue>> = []
  let error: string | null = null
  try {
    items = await getReviewQueue(filters)
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load queue"
  }

  // Stats bar
  const avgQuality = items.length
    ? Math.round(items.reduce((s, i) => s + (i.draft_record?.quality_score ?? 0), 0) / items.length)
    : null

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <h1 className="font-serif text-3xl font-semibold text-[#0E3A27]">Review queue</h1>
          <Badge variant="secondary">{items.length} pending</Badge>
          {avgQuality !== null && (
            <span className="text-sm text-[#6b7280]">avg quality: <strong style={{ color: qualityColour(avgQuality) }}>{avgQuality}</strong></span>
          )}
        </div>
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
        <div className="rounded-xl border border-[#d4cfc5] bg-white p-12 text-center">
          <p className="text-[#6b7280]">No items match the current filters.</p>
        </div>
      )}

      {items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[#d4cfc5] bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[#d4cfc5] bg-[#F8F5EE]">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Resource</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Type</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Quality</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Signals</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Reason</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Queued</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8e4dc]">
              {items.map((item) => {
                const draft = item.draft_record
                const score = draft?.quality_score
                const rel = draft?.relevance_score
                const conf = draft?.classification_confidence
                return (
                  <tr key={item.id} className="hover:bg-[#F8F5EE] transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-[#0E3A27] max-w-xs truncate">
                        {draft?.title ?? item.resource_code}
                      </div>
                      {draft?.url && (
                        <div className="text-xs text-[#6b7280] truncate max-w-xs">
                          {draft.url}
                        </div>
                      )}
                      {draft?.methodology_codes?.length > 0 && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {draft.methodology_codes.map((c) => (
                            <span key={c} className="text-[10px] bg-[#e8e4dc] text-[#4a6741] rounded px-1">{c}</span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">
                        {TYPE_LABELS[draft?.resource_type_code] ?? draft?.resource_type_code}
                      </Badge>
                      {draft?.resource_subtype_code && (
                        <div className="text-[10px] text-[#6b7280] mt-0.5">{draft.resource_subtype_code}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {score !== undefined ? (
                        <span className="font-bold text-sm" style={{ color: qualityColour(score) }}>
                          {score}
                        </span>
                      ) : <span className="text-[#6b7280]">—</span>}
                    </td>
                    <td className="px-4 py-3 space-y-1">
                      {rel !== undefined && (
                        <MiniBar value={rel} max={1} colour="#03848F" />
                      )}
                      {conf !== undefined && (
                        <MiniBar value={conf} max={1} colour="#289642" />
                      )}
                    </td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <span className="text-[#6b7280] text-xs line-clamp-2">{item.reason}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-[#6b7280] whitespace-nowrap">
                      {new Date(item.queued_at).toLocaleDateString("en-AU", {
                        day: "numeric", month: "short",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/review/${item.id}`}
                        className="flex items-center gap-1 text-[#289642] text-sm font-medium hover:underline whitespace-nowrap"
                      >
                        Review <ExternalLink size={12} />
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
