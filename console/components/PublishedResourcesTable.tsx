"use client"

import { useMemo, useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { reopenForReview, syncBatchToCompendium, syncToCompendium } from "@/app/review/actions"
import { CompendiumSyncBadge } from "@/components/CompendiumSyncBadge"
import { needsCompendiumResync } from "@/lib/compendium-sync"
import { recordSessionStat } from "@/lib/session-stats"
import { RotateCcw, Upload } from "lucide-react"

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
  compendium_url?: string | null
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

function needsSync(r: PublishedRow): boolean {
  return needsCompendiumResync(r)
}

export function PublishedResourcesTable({ resources }: { resources: PublishedRow[] }) {
  const router = useRouter()
  const [pending, startTransition] = useTransition()
  const [reopening, setReopening] = useState<string | null>(null)
  const [syncing, setSyncing] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)

  const unsyncedSelected = useMemo(
    () => resources.filter((r) => selected.has(r.resource_code) && needsSync(r)),
    [resources, selected],
  )

  const allSelected = resources.length > 0 && selected.size === resources.length

  function toggleAll() {
    if (allSelected) setSelected(new Set())
    else setSelected(new Set(resources.map((r) => r.resource_code)))
  }

  function toggleOne(code: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

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

  function handleSyncOne(resourceCode: string) {
    setError(null)
    setSyncMessage(null)
    setSyncing(resourceCode)
    startTransition(async () => {
      try {
        const result = await syncToCompendium(resourceCode)
        if (!result.ok) setError(result.error ?? "Sync failed")
        else setSyncMessage(result.compendium_url ? "Synced to Compendium" : "Marked synced (awaiting Compendium URL)")
        router.refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Sync failed")
      } finally {
        setSyncing(null)
      }
    })
  }

  function handleBulkSync() {
    const codes = unsyncedSelected.map((r) => r.resource_code)
    if (codes.length === 0) return
    setError(null)
    setSyncMessage(null)
    startTransition(async () => {
      try {
        const result = await syncBatchToCompendium(codes)
        setSyncMessage(`Synced ${result.synced}, failed ${result.failed}, skipped ${result.skipped}`)
        setSelected(new Set())
        router.refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Batch sync failed")
      }
    })
  }

  return (
    <>
      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}
      {syncMessage && (
        <div className="rounded-md border border-[#289642] bg-[#f0faf2] px-4 py-3 text-sm text-[#0E3A27]">{syncMessage}</div>
      )}

      {selected.size > 0 && (
        <div className="sticky top-0 z-30 flex items-center justify-between gap-3 rounded-lg border border-[#03848F] bg-[#f0f9fa] px-4 py-2 text-sm">
          <span className="text-[#0E3A27] font-medium">{selected.size} selected</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setSelected(new Set())}>
              Clear
            </Button>
            <Button
              size="sm"
              onClick={handleBulkSync}
              disabled={pending || unsyncedSelected.length === 0}
            >
              <Upload size={12} />
              Sync to Compendium ({unsyncedSelected.length})
            </Button>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-[#d4cfc5] bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-[#d4cfc5] bg-[#F8F5EE]">
            <tr>
              <th className="px-3 py-3 w-10">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleAll}
                  aria-label="Select all"
                  className="rounded border-[#d4cfc5]"
                />
              </th>
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
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selected.has(r.resource_code)}
                    onChange={() => toggleOne(r.resource_code)}
                    aria-label={`Select ${r.title}`}
                    className="rounded border-[#d4cfc5]"
                  />
                </td>
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
                  <CompendiumSyncBadge
                    syncedAt={r.compendium_synced_at}
                    syncError={r.compendium_sync_error}
                    compendiumUrl={r.compendium_url}
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1.5">
                    {needsSync(r) && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7"
                        disabled={pending && syncing === r.resource_code}
                        onClick={() => handleSyncOne(r.resource_code)}
                      >
                        <Upload size={12} />
                        {pending && syncing === r.resource_code ? "Syncing…" : "Sync"}
                      </Button>
                    )}
                    <Button size="sm" variant="outline" className="text-xs h-7" asChild>
                      <Link href={`/pipeline/${encodeURIComponent(r.resource_code)}`}>
                        Edit
                      </Link>
                    </Button>
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
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-[#6b7280]">
        Approve in the review queue auto-syncs to Compendium when credentials are configured.
        Use Sync here to retry failures or backfill older publishes.
        {" "}
        <Link href="/review" className="text-[#03848F] hover:underline">Go to queue</Link>
      </p>
    </>
  )
}
