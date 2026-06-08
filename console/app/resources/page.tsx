import { requireAuth } from "@/lib/auth"
import { getPublishedResources } from "@/lib/firestore"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Clock, AlertCircle } from "lucide-react"

export const metadata = { title: "Published — CoThesis" }

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

function fmtDate(v?: string): string {
  if (!v) return "—"
  try {
    return new Date(v).toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" })
  } catch {
    return "—"
  }
}

export default async function ResourcesPage() {
  await requireAuth()

  let resources: Awaited<ReturnType<typeof getPublishedResources>> = []
  let error: string | null = null
  try {
    resources = await getPublishedResources(200)
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load resources"
  }

  const synced = resources.filter((r) => r.compendium_synced_at).length

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <h1 className="font-serif text-3xl font-semibold text-[#0E3A27]">Published</h1>
        <Badge variant="secondary">{resources.length} resources</Badge>
        <span className="text-sm text-[#6b7280]">
          {synced} synced to Compendium
        </span>
      </div>

      {error && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>
      )}

      {!error && resources.length === 0 && (
        <div className="rounded-xl border border-[#d4cfc5] bg-white p-12 text-center">
          <p className="text-[#6b7280]">No published resources yet.</p>
          <p className="text-sm text-[#6b7280] mt-1">Approve items in the review queue to publish them here.</p>
        </div>
      )}

      {resources.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[#d4cfc5] bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[#d4cfc5] bg-[#F8F5EE]">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Resource</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Type</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Quality</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Approved by</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Approved</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Compendium</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8e4dc]">
              {resources.map((r) => (
                <tr key={r.resource_code} className="hover:bg-[#F8F5EE] transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-[#0E3A27] max-w-sm truncate">{r.title}</div>
                    {r.url && <div className="text-xs text-[#6b7280] truncate max-w-sm">{r.url}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline">{TYPE_LABELS[r.resource_type_code] ?? r.resource_type_code}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-bold" style={{ color: qualityColour(r.quality_score) }}>
                      {Math.round(r.quality_score)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-[#4a6741]">{r.editorial_reviewed_by ?? "—"}</td>
                  <td className="px-4 py-3 text-xs text-[#6b7280] whitespace-nowrap">{fmtDate(r.editorial_reviewed_at)}</td>
                  <td className="px-4 py-3">
                    {r.compendium_sync_error ? (
                      <span className="flex items-center gap-1 text-xs text-red-600" title={r.compendium_sync_error}>
                        <AlertCircle size={12} /> Error
                      </span>
                    ) : r.compendium_synced_at ? (
                      <span className="flex items-center gap-1 text-xs text-[#289642]">
                        <CheckCircle size={12} /> Synced
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-[#f59e0b]">
                        <Clock size={12} /> Pending
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
