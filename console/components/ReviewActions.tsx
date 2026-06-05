"use client"

import { useState, useTransition } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { BadgeList } from "@/components/BadgeList"
import type { ChecklistError } from "@/lib/checklist"
import { CheckCircle, XCircle, AlertCircle, RotateCcw, Pencil } from "lucide-react"

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
}

interface Props {
  itemId: string
  proposedBadges: string[]
  checklistErrors: ChecklistError[]
  qualityScore: number
  aiConfidence: number
  edited: EditedDescriptions
  approveAction: (
    itemId: string,
    badges: string[],
    editorialNote: string,
    reviewerName: string,
    edited: EditedDescriptions
  ) => Promise<void>
  rejectAction: (itemId: string, reason: string) => Promise<void>
  requeueAction: (itemId: string, reason: string) => Promise<void>
}

const THRESHOLD_OK = (q: number, c: number) => q >= 80 && c >= 70
const THRESHOLD_BORDER = (q: number, c: number) => (q >= 60 && q < 80) || (c >= 50 && c < 70)

export function ReviewActions({
  itemId, proposedBadges, checklistErrors, qualityScore, aiConfidence,
  edited, approveAction, rejectAction, requeueAction,
}: Props) {
  const [ratifiedBadges, setRatifiedBadges] = useState<string[]>(proposedBadges.slice(0, 3))
  const [editorialNote, setEditorialNote] = useState("")
  const [reviewerName, setReviewerName] = useState<string>(() => {
    if (typeof window !== "undefined") return localStorage.getItem("cothesis_reviewer") ?? ""
    return ""
  })
  const [editingReviewer, setEditingReviewer] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [requeueing, setRequeueing] = useState(false)
  const [requeueReason, setRequeueReason] = useState("")
  const [isPending, startTransition] = useTransition()

  const canApprove = checklistErrors.length === 0

  function saveReviewer(name: string) {
    if (typeof window !== "undefined") localStorage.setItem("cothesis_reviewer", name)
    setReviewerName(name)
    setEditingReviewer(false)
  }

  function handleApprove() {
    startTransition(() => {
      approveAction(itemId, ratifiedBadges, editorialNote, reviewerName || "console", edited)
    })
  }
  function handleReject() {
    if (!rejectReason.trim()) return
    startTransition(() => { rejectAction(itemId, rejectReason) })
  }
  function handleRequeue() {
    if (!requeueReason.trim()) return
    startTransition(() => { requeueAction(itemId, requeueReason) })
  }

  const autoOk = THRESHOLD_OK(qualityScore, aiConfidence)
  const autoBorder = THRESHOLD_BORDER(qualityScore, aiConfidence)

  return (
    <div className="space-y-5">
      {/* Reviewer identity */}
      <div className="flex items-center gap-2 text-xs text-[#6b7280]">
        <span>Reviewing as:</span>
        {editingReviewer ? (
          <form onSubmit={(e) => { e.preventDefault(); saveReviewer(reviewerName) }} className="flex gap-1">
            <input
              autoFocus
              className="h-6 px-2 text-xs rounded border border-[#d4cfc5] text-[#0E3A27] focus:outline-none focus:ring-1 focus:ring-[#289642]"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              placeholder="Your name"
            />
            <button type="submit" className="text-[#289642]"><CheckCircle size={12} /></button>
          </form>
        ) : (
          <button
            className="flex items-center gap-1 font-medium text-[#0E3A27] hover:text-[#289642]"
            onClick={() => setEditingReviewer(true)}
          >
            {reviewerName || "anonymous"} <Pencil size={10} />
          </button>
        )}
      </div>

      {/* Quality threshold indicator */}
      <div className={`text-xs rounded px-3 py-2 ${autoOk ? "bg-green-50 text-green-800" : autoBorder ? "bg-amber-50 text-amber-800" : "bg-red-50 text-red-800"}`}>
        {autoOk
          ? `✓ Quality ${qualityScore}, confidence ${Math.round(aiConfidence)} — auto-accept thresholds met`
          : autoBorder
          ? `⚠ Borderline — quality ${qualityScore}, confidence ${Math.round(aiConfidence)}`
          : `✗ Below threshold — quality ${qualityScore}, confidence ${Math.round(aiConfidence)}`}
      </div>

      {/* Badges */}
      <div>
        <h3 className="text-sm font-semibold text-[#0E3A27] mb-2">Ratify badges</h3>
        <BadgeList proposed={proposedBadges} onChange={setRatifiedBadges} />
      </div>

      {/* Publish checklist */}
      <div className="rounded-md border border-[#d4cfc5] p-3 space-y-1.5">
        <h3 className="text-xs font-semibold text-[#4a6741] uppercase tracking-wide mb-2">Publish checklist</h3>
        {checklistErrors.length === 0 ? (
          <div className="flex items-center gap-2 text-[#289642] text-sm">
            <CheckCircle size={14} /> All checks passed
          </div>
        ) : (
          checklistErrors.map((e, i) => (
            <div key={i} className="flex items-start gap-2 text-[#dc2626] text-xs">
              <AlertCircle size={12} className="mt-0.5 shrink-0" />
              <span><span className="font-medium">{e.field}:</span> {e.message}</span>
            </div>
          ))
        )}
      </div>

      {/* Action buttons */}
      {!rejecting && !requeueing && (
        <div className="space-y-2">
          <Button onClick={handleApprove} disabled={!canApprove || isPending} className="w-full">
            <CheckCircle size={14} />
            {isPending ? "Publishing…" : "Approve & publish"}
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setRequeueing(true)} disabled={isPending} className="flex-1 text-xs">
              <RotateCcw size={12} /> Send back
            </Button>
            <Button variant="outline" onClick={() => setRejecting(true)} disabled={isPending} className="flex-1 text-xs text-red-600 border-red-200 hover:bg-red-50">
              <XCircle size={12} /> Reject
            </Button>
          </div>
        </div>
      )}

      {/* Send back form */}
      {requeueing && (
        <div className="space-y-2 rounded-md border border-[#03848F] p-3">
          <h3 className="text-xs font-semibold text-[#03848F]">Send back to pipeline</h3>
          <Textarea
            placeholder="Note for pipeline (e.g. reclassify as book, check DOI…)"
            value={requeueReason}
            onChange={(e) => setRequeueReason(e.target.value)}
            rows={2}
            className="text-xs"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleRequeue} disabled={!requeueReason.trim() || isPending}>
              {isPending ? "Sending…" : "Send back"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setRequeueing(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {/* Reject form */}
      {rejecting && (
        <div className="space-y-2 rounded-md border border-red-300 p-3">
          <h3 className="text-xs font-semibold text-red-600">Reject resource</h3>
          <Textarea
            placeholder="Required: reason for rejection…"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={2}
            className="text-xs"
          />
          <div className="flex gap-2">
            <Button variant="destructive" size="sm" onClick={handleReject} disabled={!rejectReason.trim() || isPending}>
              {isPending ? "Rejecting…" : "Confirm rejection"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setRejecting(false)}>Cancel</Button>
          </div>
        </div>
      )}
    </div>
  )
}
