"use client"

import { useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { reopenForReview } from "@/app/review/actions"
import { recordSessionStat } from "@/lib/session-stats"
import { CheckCircle, Clock, AlertCircle, RotateCcw } from "lucide-react"

export interface PublishedRow {
  resource_code: string
  title: string
  url?: string
  resource_type_code: string
  quality_score: number
  editorial_reviewed_by?: string
  editorial_reviewed_at?: string
  compendium_synced_at?: string | null
  compendium_sync_error?: string | null
}

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

export function PublishedResourcesTable({ resources }: { resources: PublishedRow[] }) {
  const router = useRouter()
  const [pending, startTransition] = useTransition()
  const [reopening, setReopening] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  function handleReopen(resourceCode: string) {
    setError(null)
    setReopening(resourceCode)
    startTransition(async () => {
      try {
        const { queueId } = await reopenForReview(resourceCode)
        recordSessionStat("reopened")
        router.push(`/review/${queueId}`)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not reopen resource")
        setReopening(null)
      }
    })
  }

  return (
    <>
      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}
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
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Actions</th>
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
                <td className="px-4 py-3">
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-xs h-7"
                    disabled={pending && reopening === r.resource_code}
                    onClick={() => handleReopen(r.resource_code)}
                  >
                    <RotateCcw size={12} />
                    {pending && reopening === r.resource_code ? "Opening…" : "Reopen"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-[#6b7280]">
        Reopening sends the resource back to the review queue with its current published fields as the draft.
        {" "}
        <Link href="/review" className="text-[#03848F] hover:underline">Go to queue</Link>
      </p>
    </>
  )
}
