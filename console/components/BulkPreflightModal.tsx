"use client"

import { Button } from "@/components/ui/button"
import { X, CheckCircle, AlertCircle } from "lucide-react"

export interface BulkRowStatus {
  id: string
  title: string
  canApprove: boolean
  errors: string[]
}

interface Props {
  open: boolean
  mode: "approve" | "reject"
  rows: BulkRowStatus[]
  rejectReason: string
  onRejectReasonChange: (v: string) => void
  onConfirm: () => void
  onClose: () => void
  isPending: boolean
}

export function BulkPreflightModal({
  open, mode, rows, rejectReason, onRejectReasonChange,
  onConfirm, onClose, isPending,
}: Props) {
  if (!open) return null

  const ready = rows.filter((r) => r.canApprove)
  const blocked = rows.filter((r) => !r.canApprove)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-label="Bulk action confirmation"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl border border-[#d4cfc5] shadow-lg max-w-md w-full max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#e8e4dc]">
          <h2 className="font-serif text-lg font-semibold text-[#0E3A27]">
            {mode === "approve" ? "Bulk approve" : "Bulk reject"}
          </h2>
          <button type="button" onClick={onClose} aria-label="Close" className="text-[#6b7280]">
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 overflow-y-auto flex-1 space-y-3 text-sm">
          {mode === "approve" ? (
            <>
              <p className="text-[#6b7280]">
                Publishes <strong>{ready.length}</strong> item{ready.length !== 1 ? "s" : ""} as drafted
                (no inline edits). Skips <strong>{blocked.length}</strong> failing checklist.
              </p>
              {ready.length > 0 && (
                <ul className="space-y-1">
                  {ready.slice(0, 8).map((r) => (
                    <li key={r.id} className="flex items-start gap-2 text-[#289642] text-xs">
                      <CheckCircle size={12} className="mt-0.5 shrink-0" />
                      <span className="line-clamp-1">{r.title}</span>
                    </li>
                  ))}
                  {ready.length > 8 && (
                    <li className="text-xs text-[#9ca3af]">+ {ready.length - 8} more</li>
                  )}
                </ul>
              )}
              {blocked.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-red-600 mb-1">Will skip:</p>
                  <ul className="space-y-1">
                    {blocked.slice(0, 5).map((r) => (
                      <li key={r.id} className="flex items-start gap-2 text-xs text-[#6b7280]">
                        <AlertCircle size={12} className="mt-0.5 shrink-0 text-red-500" />
                        <span>
                          <span className="line-clamp-1">{r.title}</span>
                          <span className="text-red-600"> — {r.errors[0]}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <>
              <p className="text-[#6b7280]">
                Reject <strong>{rows.length}</strong> selected item{rows.length !== 1 ? "s" : ""} and archive resources.
              </p>
              <textarea
                className="w-full rounded border border-[#d4cfc5] px-3 py-2 text-sm text-[#0E3A27] focus:outline-none focus:ring-1 focus:ring-[#289642] resize-none"
                rows={3}
                placeholder="Required: shared rejection reason…"
                value={rejectReason}
                onChange={(e) => onRejectReasonChange(e.target.value)}
              />
            </>
          )}
        </div>

        <div className="px-5 py-4 border-t border-[#e8e4dc] flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button
            size="sm"
            variant={mode === "reject" ? "destructive" : "default"}
            disabled={
              isPending ||
              (mode === "approve" && ready.length === 0) ||
              (mode === "reject" && !rejectReason.trim())
            }
            onClick={onConfirm}
          >
            {isPending
              ? "Working…"
              : mode === "approve"
              ? `Approve ${ready.length}`
              : `Reject ${rows.length}`}
          </Button>
        </div>
      </div>
    </div>
  )
}
