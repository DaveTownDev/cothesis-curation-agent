"use client"

import Link from "next/link"
import { useMemo, useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { CompendiumSyncBadge } from "@/components/CompendiumSyncBadge"
import { syncBatchToCompendium, syncToCompendium } from "@/app/review/actions"
import type { ResourceLiveStatus } from "@/lib/firestore"
import { needsCompendiumResync } from "@/lib/compendium-sync"
import { Upload } from "lucide-react"

export interface PipelineRunRow {
  id: string
  resource_code: string
  stage: string
  routing?: string
  composite?: number
  pipeline_run_id?: string
  updated_at?: string
  live?: ResourceLiveStatus
}

const STAGE_COLOURS: Record<string, string> = {
  discovered: "#9ca3af", appraised: "#03848F", classified: "#0ea5e9",
  edited: "#8b5cf6", reconciled: "#6366f1", qc_panel: "#f59e0b",
  arbiter: "#ec4899", auto_accept: "#289642", review_needed: "#f59e0b",
  auto_exclude: "#dc2626", published: "#289642",
}

const ROUTING_COLOURS: Record<string, string> = {
  auto_accept: "#289642", review_needed: "#f59e0b", auto_exclude: "#dc2626",
}

function fmtDate(v?: string): string {
  if (!v) return "—"
  try {
    return new Date(v).toLocaleDateString("en-AU", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
    })
  } catch {
    return "—"
  }
}

function isPublished(live?: ResourceLiveStatus): boolean {
  return live?.editorial_status === "published"
}

function canPushToLive(live?: ResourceLiveStatus): boolean {
  return isPublished(live) && needsCompendiumResync(live ?? {})
}

export function PipelineRunsTable({ runs }: { runs: PipelineRunRow[] }) {
  const router = useRouter()
  const [pending, startTransition] = useTransition()
  const [syncing, setSyncing] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const pushableSelected = useMemo(
    () => runs.filter((r) => selected.has(r.resource_code) && canPushToLive(r.live)),
    [runs, selected],
  )

  const allSelected = runs.length > 0 && selected.size === runs.length

  function toggleAll() {
    if (allSelected) setSelected(new Set())
    else setSelected(new Set(runs.map((r) => r.resource_code)))
  }

  function toggleOne(code: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  function handlePushOne(resourceCode: string) {
    setError(null)
    setMessage(null)
    setSyncing(resourceCode)
    startTransition(async () => {
      try {
        const result = await syncToCompendium(resourceCode)
        if (!result.ok) setError(result.error ?? "Push failed")
        else setMessage(result.compendium_url ? "Pushed to Compendium" : "Push accepted (awaiting URL)")
        router.refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Push failed")
      } finally {
        setSyncing(null)
      }
    })
  }

  function handleBulkPush() {
    const codes = pushableSelected.map((r) => r.resource_code)
    if (codes.length === 0) return
    setError(null)
    setMessage(null)
    startTransition(async () => {
      try {
        const result = await syncBatchToCompendium(codes)
        setMessage(`Pushed ${result.synced}, failed ${result.failed}, skipped ${result.skipped}`)
        setSelected(new Set())
        router.refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Batch push failed")
      }
    })
  }

  return (
    <>
      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}
      {message && (
        <div className="rounded-md border border-[#289642] bg-[#f0faf2] px-4 py-3 text-sm text-[#0E3A27]">{message}</div>
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
              onClick={handleBulkPush}
              disabled={pending || pushableSelected.length === 0}
            >
              <Upload size={12} />
              Push to live ({pushableSelected.length})
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
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Resource code</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Stage</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Routing</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Composite</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Live status</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Run ID</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Updated</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#e8e4dc]">
            {runs.map((run) => (
              <tr key={run.id} className="hover:bg-[#F8F5EE] transition-colors">
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selected.has(run.resource_code)}
                    onChange={() => toggleOne(run.resource_code)}
                    aria-label={`Select ${run.resource_code}`}
                    className="rounded border-[#d4cfc5]"
                  />
                </td>
                <td className="px-4 py-3 font-mono text-xs text-[#0E3A27] max-w-[200px] truncate">
                  {run.resource_code}
                </td>
                <td className="px-4 py-3">
                  <span
                    className="text-xs font-medium rounded px-2 py-0.5"
                    style={{
                      backgroundColor: `${STAGE_COLOURS[run.stage] ?? "#9ca3af"}20`,
                      color: STAGE_COLOURS[run.stage] ?? "#6b7280",
                    }}
                  >
                    {run.stage}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {run.routing ? (
                    <span
                      className="text-xs font-medium capitalize"
                      style={{ color: ROUTING_COLOURS[run.routing] ?? "#6b7280" }}
                    >
                      {run.routing.replace(/_/g, " ")}
                    </span>
                  ) : (
                    <span className="text-[#9ca3af] text-xs">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-[#4a6741]">
                  {run.composite?.toFixed(1) ?? "—"}
                </td>
                <td className="px-4 py-3">
                  {isPublished(run.live) ? (
                    <CompendiumSyncBadge
                      syncedAt={run.live?.compendium_synced_at}
                      syncError={run.live?.compendium_sync_error}
                      compendiumUrl={run.live?.compendium_url}
                      compact
                    />
                  ) : (
                    <span className="text-xs text-[#9ca3af]">Not published</span>
                  )}
                </td>
                <td className="px-4 py-3 font-mono text-[10px] text-[#9ca3af] max-w-[140px] truncate">
                  {run.pipeline_run_id ?? "—"}
                </td>
                <td className="px-4 py-3 text-xs text-[#6b7280] whitespace-nowrap">{fmtDate(run.updated_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1.5">
                    {canPushToLive(run.live) && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7"
                        disabled={pending && syncing === run.resource_code}
                        onClick={() => handlePushOne(run.resource_code)}
                      >
                        <Upload size={12} />
                        {pending && syncing === run.resource_code ? "Pushing…" : "Push to live"}
                      </Button>
                    )}
                    <Link
                      href={`/pipeline/${encodeURIComponent(run.resource_code)}`}
                      className="text-xs text-[var(--green-primary)] font-medium hover:underline whitespace-nowrap inline-flex items-center h-7"
                    >
                      View / edit
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-[#6b7280]">
        Approve in the review queue publishes to Firestore only. Use Push to live when you are ready to sync to Compendium.
      </p>
    </>
  )
}
