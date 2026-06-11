"use client"

import { useMemo, useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import type { ReviewQueueItem } from "@/lib/firestore"
import { validatePublishChecklist } from "@/lib/checklist"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { QueueTableRow } from "@/components/QueueTableRow"
import { BulkPreflightModal, type BulkRowStatus } from "@/components/BulkPreflightModal"
import { bulkApproveAsDrafted, bulkReject } from "@/app/review/actions"
import { recordSessionStat } from "@/lib/session-stats"
import { ExternalLink } from "lucide-react"

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
        <div className="h-full rounded-full" style={{ width: `${(value / max) * 100}%`, backgroundColor: colour }} />
      </div>
    </div>
  )
}

function rowStatus(item: ReviewQueueItem): BulkRowStatus {
  const errors = validatePublishChecklist(
    item.draft_record as unknown as Record<string, unknown>,
    "console",
  )
  return {
    id: item.id,
    title: item.draft_record?.title ?? item.resource_code,
    canApprove: errors.length === 0,
    errors: errors.map((e) => e.message),
  }
}

interface Props {
  items: ReviewQueueItem[]
  compact: boolean
  detailQuery: string
}

export function ReviewQueueTable({ items, compact, detailQuery }: Props) {
  const router = useRouter()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [modal, setModal] = useState<"approve" | "reject" | null>(null)
  const [rejectReason, setRejectReason] = useState("")
  const [bulkMessage, setBulkMessage] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  const hrefFor = (id: string) =>
    detailQuery ? `/review/${id}?${detailQuery}` : `/review/${id}`

  const selectedItems = useMemo(
    () => items.filter((i) => selected.has(i.id)),
    [items, selected],
  )
  const bulkRows = useMemo(() => selectedItems.map(rowStatus), [selectedItems])

  const allSelected = items.length > 0 && selected.size === items.length

  function toggleAll() {
    if (allSelected) setSelected(new Set())
    else setSelected(new Set(items.map((i) => i.id)))
  }

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function runBulkApprove() {
    startTransition(async () => {
      const reviewer = localStorage.getItem("cothesis_reviewer") ?? "console"
      const readyIds = bulkRows.filter((r) => r.canApprove).map((r) => r.id)
      const result = await bulkApproveAsDrafted(readyIds, reviewer)
      if (result.approved > 0) recordSessionStat("approved", result.approved)
      if (result.approved > 0) {
        setBulkMessage(`Approved ${result.approved}${result.skipped > 0 ? `, skipped ${result.skipped}` : ""}. Push to live from Pipeline or Published.`)
      }
      setModal(null)
      setSelected(new Set())
      router.refresh()
    })
  }

  function runBulkReject() {
    startTransition(async () => {
      const result = await bulkReject(selectedItems.map((i) => i.id), rejectReason)
      if (result.rejected > 0) recordSessionStat("rejected", result.rejected)
      setModal(null)
      setRejectReason("")
      setSelected(new Set())
      router.refresh()
    })
  }

  return (
    <>
      {bulkMessage && (
        <div className="rounded-md border border-[#289642] bg-[#f0faf2] px-4 py-2 text-sm text-[#0E3A27]">
          {bulkMessage}
        </div>
      )}
      {selected.size > 0 && (
        <div className="sticky top-0 z-30 flex items-center justify-between gap-3 rounded-lg border border-[#289642] bg-[#f0faf2] px-4 py-2 text-sm">
          <span className="text-[#0E3A27] font-medium">{selected.size} selected</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => setSelected(new Set())}>
              Clear
            </Button>
            <Button size="sm" onClick={() => setModal("approve")}>
              Approve as drafted
            </Button>
            <Button size="sm" variant="destructive" onClick={() => setModal("reject")}>
              Reject
            </Button>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-[#d4cfc5] bg-white overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
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
              {compact && (
                <th className="px-4 py-3 text-left font-medium text-[#6b7280] max-w-xs">Plain language</th>
              )}
              {!compact && (
                <>
                  <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Signals</th>
                  <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Reason</th>
                  <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Queued</th>
                </>
              )}
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Quality</th>
              <th className="px-4 py-3 text-left font-medium text-[#6b7280]">QA</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-[#e8e4dc]">
            {items.map((item) => {
              const draft = item.draft_record
              const score = draft?.quality_score
              const rel = draft?.relevance_score
              const conf = draft?.classification_confidence
              const isSelected = selected.has(item.id)
              return (
                <QueueTableRow key={item.id} href={hrefFor(item.id)}>
                  <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleOne(item.id)}
                      aria-label={`Select ${draft?.title ?? item.resource_code}`}
                      className="rounded border-[#d4cfc5]"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-[#0E3A27] max-w-sm truncate">
                      {draft?.title ?? item.resource_code}
                    </div>
                    {draft?.methodology_codes?.length > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {draft.methodology_codes.map((c) => (
                          <span key={c} className="text-[10px] bg-[#e8e4dc] text-[#4a6741] rounded px-1">{c}</span>
                        ))}
                      </div>
                    )}
                  </td>
                  {compact && (
                    <td className="px-4 py-3 max-w-xs">
                      <p className="text-xs text-[#4a5568] line-clamp-2 leading-relaxed">
                        {draft?.editorial_description_plain || "—"}
                      </p>
                    </td>
                  )}
                  {!compact && (
                    <>
                      <td className="px-4 py-3">
                        <Badge variant="outline">
                          {TYPE_LABELS[draft?.resource_type_code] ?? draft?.resource_type_code}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 space-y-1">
                        {rel !== undefined && <MiniBar value={rel} max={1} colour="#03848F" />}
                        {conf !== undefined && <MiniBar value={conf} max={1} colour="#289642" />}
                      </td>
                      <td className="px-4 py-3 max-w-[200px]">
                        <span className="text-[#6b7280] text-xs line-clamp-2">{item.reason}</span>
                      </td>
                      <td className="px-4 py-3 text-xs text-[#6b7280] whitespace-nowrap">
                        {new Date(item.queued_at).toLocaleDateString("en-AU", {
                          day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
                        })}
                      </td>
                    </>
                  )}
                  <td className="px-4 py-3">
                    {score !== undefined ? (
                      <span className="font-bold text-sm" style={{ color: qualityColour(score) }}>
                        {score}
                      </span>
                    ) : <span className="text-[#6b7280]">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {item.qa_audit?.source_verdict ? (
                      <span
                        className="text-[10px] font-semibold rounded px-1.5 py-0.5"
                        style={{
                          backgroundColor: item.qa_audit.source_verdict === "pass" ? "#28964220"
                            : item.qa_audit.source_verdict === "warn" ? "#f59e0b20" : "#dc262620",
                          color: item.qa_audit.source_verdict === "pass" ? "#289642"
                            : item.qa_audit.source_verdict === "warn" ? "#b45309" : "#dc2626",
                        }}
                        title={item.qa_audit.source_notes ?? ""}
                      >
                        {item.qa_audit.source_verdict.toUpperCase()}
                      </span>
                    ) : <span className="text-[#9ca3af] text-xs" title="Source QA not run">pending</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1 text-[#289642] text-sm font-medium whitespace-nowrap">
                      Review <ExternalLink size={12} />
                    </span>
                  </td>
                </QueueTableRow>
              )
            })}
          </tbody>
        </table>
      </div>

      <BulkPreflightModal
        open={modal !== null}
        mode={modal ?? "approve"}
        rows={bulkRows}
        rejectReason={rejectReason}
        onRejectReasonChange={setRejectReason}
        onConfirm={modal === "approve" ? runBulkApprove : runBulkReject}
        onClose={() => { setModal(null); setRejectReason("") }}
        isPending={isPending}
      />
    </>
  )
}
