"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle, XCircle, RotateCcw } from "lucide-react"

interface Props {
  canApprove: boolean
  isPending: boolean
  onApprove: () => void
  onReject: () => void
  onRequeue: () => void
}

export function StickyActionBar({
  canApprove, isPending, onApprove, onReject, onRequeue,
}: Props) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--border-primary)] bg-white/95 backdrop-blur px-4 py-2 shadow-[0_-4px_12px_rgba(45,37,24,0.06)] xl:hidden">
      <div className="flex gap-2 max-w-lg mx-auto">
        <Button
          onClick={onApprove}
          disabled={!canApprove || isPending}
          className="flex-1"
          size="sm"
        >
          <CheckCircle size={14} /> Approve
        </Button>
        <Button variant="outline" size="sm" onClick={onRequeue} disabled={isPending}>
          <RotateCcw size={12} />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onReject}
          disabled={isPending}
          className="text-red-600 border-red-200"
        >
          <XCircle size={12} />
        </Button>
      </div>
    </div>
  )
}
