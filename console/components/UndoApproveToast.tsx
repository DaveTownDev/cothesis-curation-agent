"use client"

import { Button } from "@/components/ui/button"
import { RotateCcw } from "lucide-react"

interface Props {
  visible: boolean
  resourceTitle: string
  secondsLeft: number
  onUndo: () => void
  onDismiss: () => void
  isUndoing: boolean
}

export function UndoApproveToast({
  visible, resourceTitle, secondsLeft, onUndo, onDismiss, isUndoing,
}: Props) {
  if (!visible) return null
  return (
    <div className="fixed bottom-20 xl:bottom-6 left-1/2 -translate-x-1/2 z-50 w-[min(100%,24rem)]">
      <div className="rounded-lg border border-[#289642] bg-white shadow-lg px-4 py-3 flex items-center gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[#0E3A27] truncate">Published</p>
          <p className="text-xs text-[#6b7280] truncate">{resourceTitle}</p>
        </div>
        <Button size="sm" variant="outline" onClick={onUndo} disabled={isUndoing} className="shrink-0 text-xs">
          <RotateCcw size={12} /> Undo
        </Button>
        <button
          type="button"
          onClick={onDismiss}
          className="text-xs text-[#9ca3af] hover:text-[#0E3A27] shrink-0"
        >
          {secondsLeft}s
        </button>
      </div>
    </div>
  )
}
