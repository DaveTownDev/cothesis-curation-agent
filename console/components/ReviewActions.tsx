"use client"

import { forwardRef, useImperativeHandle, useState, useTransition } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { BadgeList } from "@/components/BadgeList"
import type { ChecklistError } from "@/lib/checklist"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import { REQUEUE_STAGES, formatRequeueReason, type RequeueStage } from "@/lib/requeue"
import { REJECT_PRESETS } from "@/lib/reject-presets"
import { recordSessionStat } from "@/lib/session-stats"
import type { ApproveResult } from "@/app/review/actions"
import { CheckCircle, XCircle, AlertCircle, RotateCcw, Pencil } from "lucide-react"

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
}

export interface ReviewActionsHandle {
  approve: () => void
  openReject: () => void
  openRequeue: () => void
  closeForms: () => void
  prefillReject: (reason: string) => void
  quickReject: (reason: string) => void
  quickRequeue: (stage: RequeueStage, note: string, draftPatch?: Record<string, unknown>) => void
}

interface Props {
  itemId: string
  proposedBadges: string[]
  editorialNote: string
  taxonomy: TaxonomyEdits
  checklistErrors: ChecklistError[]
  qualityScore: number
  aiConfidence: number
  edited: EditedDescriptions
  nextId: string | null
  queueQuery: string
  approveAction: (
    itemId: string,
    badges: string[],
    editorialNote: string,
    reviewerName: string,
    edited: EditedDescriptions,
    taxonomy: TaxonomyEdits,
    nextId: string | null,
    queueQuery: string,
  ) => Promise<ApproveResult>
  rejectAction: (
    itemId: string,
    reason: string,
    nextId: string | null,
    queueQuery: string,
  ) => Promise<{ nextPath: string }>
  requeueAction: (
    itemId: string,
    reason: string,
    stage: string,
    nextId: string | null,
    queueQuery: string,
    draftPatch?: Record<string, unknown>,
  ) => Promise<{ nextPath: string }>
  onNavigate: (nextPath: string, undo?: ApproveResult["undo"], sync?: ApproveResult["sync"]) => void
}

const THRESHOLD_OK = (q: number, c: number) => q >= 80 && c >= 70
const THRESHOLD_BORDER = (q: number, c: number) => (q >= 60 && q < 80) || (c >= 50 && c < 70)

export const ReviewActions = forwardRef<ReviewActionsHandle, Props>(function ReviewActions({
  itemId, proposedBadges, editorialNote, taxonomy, checklistErrors, qualityScore, aiConfidence,
  edited, nextId, queueQuery,
  approveAction, rejectAction, requeueAction, onNavigate,
}, ref) {
  const [ratifiedBadges, setRatifiedBadges] = useState<string[]>(proposedBadges.slice(0, 3))
  const [actionError, setActionError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [reviewerName, setReviewerName] = useState<string>(() => {
    if (typeof window !== "undefined") return localStorage.getItem("cothesis_reviewer") ?? ""
    return ""
  })
  const [editingReviewer, setEditingReviewer] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [requeueing, setRequeueing] = useState(false)
  const [requeueReason, setRequeueReason] = useState("")
  const [requeueStage, setRequeueStage] = useState<RequeueStage>("classification")
  const [isPending, startTransition] = useTransition()

  const canApprove = checklistErrors.length === 0

  function saveReviewer(name: string) {
    if (typeof window !== "undefined") localStorage.setItem("cothesis_reviewer", name)
    setReviewerName(name)
    setEditingReviewer(false)
  }

  async function runAction<T>(action: () => Promise<T>, onSuccess: (result: T) => void) {
    setActionError(null)
    setSubmitted(true)
    try {
      const result = await action()
      onSuccess(result)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed — try again")
      setSubmitted(false)
    }
  }

  function handleApprove() {
    if (!canApprove || isPending || submitted) return
    startTransition(() => {
      void runAction(
        () => approveAction(
          itemId, ratifiedBadges, editorialNote, reviewerName || "console",
          edited, taxonomy, nextId, queueQuery,
        ),
        (result) => {
          recordSessionStat("approved")
          onNavigate(result.nextPath, result.undo, result.sync)
        },
      )
    })
  }

  function handleReject() {
    if (!rejectReason.trim()) return
    startTransition(() => {
      void runAction(
        () => rejectAction(itemId, rejectReason, nextId, queueQuery),
        (result) => {
          recordSessionStat("rejected")
          onNavigate(result.nextPath)
        },
      )
    })
  }

  function handleRequeue() {
    const note = requeueReason.trim()
    if (requeueStage === "other" && !note) return
    const reason = formatRequeueReason(requeueStage, note)
    startTransition(() => {
      void runAction(
        () => requeueAction(itemId, reason, requeueStage, nextId, queueQuery),
        (result) => onNavigate(result.nextPath),
      )
    })
  }

  function submitRequeue(
    stage: RequeueStage,
    note: string,
    draftPatch?: Record<string, unknown>,
  ) {
    const reason = formatRequeueReason(stage, note.trim())
    startTransition(() => {
      void runAction(
        () => requeueAction(itemId, reason, stage, nextId, queueQuery, draftPatch),
        (result) => onNavigate(result.nextPath),
      )
    })
  }

  function submitReject(reason: string) {
    const trimmed = reason.trim()
    if (!trimmed) return
    startTransition(() => {
      void runAction(
        () => rejectAction(itemId, trimmed, nextId, queueQuery),
        (result) => {
          recordSessionStat("rejected")
          onNavigate(result.nextPath)
        },
      )
    })
  }

  useImperativeHandle(ref, () => ({
    approve: handleApprove,
    openReject: () => { setRejecting(true); setRequeueing(false) },
    openRequeue: () => { setRequeueing(true); setRejecting(false) },
    closeForms: () => { setRejecting(false); setRequeueing(false) },
    prefillReject: (reason: string) => {
      setRejectReason(reason)
      setRejecting(true)
      setRequeueing(false)
    },
    quickReject: (reason: string) => {
      setRejectReason(reason)
      submitReject(reason)
    },
    quickRequeue: (stage: RequeueStage, note: string, draftPatch?: Record<string, unknown>) => {
      setRequeueStage(stage)
      setRequeueReason(note)
      submitRequeue(stage, note, draftPatch)
    },
  }))

  const autoOk = THRESHOLD_OK(qualityScore, aiConfidence)
  const autoBorder = THRESHOLD_BORDER(qualityScore, aiConfidence)

  return (
    <div className="space-y-5">
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
            type="button"
            className="flex items-center gap-1 font-medium text-[#0E3A27] hover:text-[#289642]"
            onClick={() => setEditingReviewer(true)}
          >
            {reviewerName || "anonymous"} <Pencil size={10} />
          </button>
        )}
      </div>

      <div className={`text-xs rounded px-3 py-2 ${autoOk ? "bg-green-50 text-green-800" : autoBorder ? "bg-amber-50 text-amber-800" : "bg-red-50 text-red-800"}`}>
        {autoOk
          ? `✓ Quality ${qualityScore}, confidence ${Math.round(aiConfidence)} — auto-accept thresholds met`
          : autoBorder
          ? `⚠ Borderline — quality ${qualityScore}, confidence ${Math.round(aiConfidence)}`
          : `✗ Below threshold — quality ${qualityScore}, confidence ${Math.round(aiConfidence)}`}
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[#0E3A27] mb-2">Ratify badges</h3>
        <BadgeList proposed={proposedBadges} onChange={setRatifiedBadges} />
      </div>

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

      {actionError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
          {actionError}
        </div>
      )}

      {!rejecting && !requeueing && (
        <div className="space-y-2">
          <Button
            data-action="approve"
            onClick={handleApprove}
            disabled={!canApprove || isPending || submitted}
            className="w-full"
          >
            <CheckCircle size={14} />
            {isPending ? "Publishing…" : "Approve & publish (a)"}
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setRequeueing(true)} disabled={isPending} className="flex-1 text-xs">
              <RotateCcw size={12} /> Send back (b)
            </Button>
            <Button variant="outline" onClick={() => setRejecting(true)} disabled={isPending} className="flex-1 text-xs text-red-600 border-red-200 hover:bg-red-50">
              <XCircle size={12} /> Reject (r)
            </Button>
          </div>
        </div>
      )}

      {requeueing && (
        <div className="space-y-2 rounded-md border border-[#03848F] p-3">
          <h3 className="text-xs font-semibold text-[#03848F]">Send back to pipeline</h3>
          <label className="block text-xs text-[#6b7280]">
            What needs fixing?
            <select
              className="mt-1 w-full h-8 rounded border border-[#d4cfc5] bg-white px-2 text-[#0E3A27] text-xs"
              value={requeueStage}
              onChange={(e) => setRequeueStage(e.target.value as RequeueStage)}
            >
              {REQUEUE_STAGES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </label>
          <Textarea
            placeholder={
              requeueStage === "other"
                ? "Required: describe what the pipeline should redo…"
                : "Optional detail for the pipeline operator…"
            }
            value={requeueReason}
            onChange={(e) => setRequeueReason(e.target.value)}
            rows={2}
            className="text-xs"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleRequeue}
              disabled={(requeueStage === "other" && !requeueReason.trim()) || isPending}
            >
              {isPending ? "Sending…" : "Send back"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setRequeueing(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {rejecting && (
        <div className="space-y-2 rounded-md border border-red-300 p-3">
          <h3 className="text-xs font-semibold text-red-600">Reject resource</h3>
          <div className="flex flex-wrap gap-1.5">
            {REJECT_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className={`text-[10px] rounded-full px-2.5 py-1 border transition-colors ${
                  rejectReason === preset.reason
                    ? "bg-red-100 border-red-300 text-red-800"
                    : "bg-white border-red-200 text-red-700 hover:bg-red-50"
                }`}
                onClick={() => setRejectReason(preset.reason)}
              >
                {preset.label}
              </button>
            ))}
          </div>
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
})
