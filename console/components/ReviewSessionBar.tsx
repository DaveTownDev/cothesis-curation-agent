"use client"

import Link from "next/link"
import { ChevronLeft, ChevronRight, Keyboard } from "lucide-react"

interface Props {
  position: number
  total: number
  prevHref: string | null
  nextHref: string | null
  onShowHelp: () => void
}

export function ReviewSessionBar({
  position, total, prevHref, nextHref, onShowHelp,
}: Props) {
  if (total === 0) return null
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-[#d4cfc5] bg-white px-4 py-2 text-sm">
      <span className="text-[#6b7280]">
        Item <strong className="text-[#0E3A27]">{position}</strong> of{" "}
        <strong className="text-[#0E3A27]">{total}</strong>
        {total > 1 && <span className="hidden sm:inline text-[#9ca3af] ml-1">· auto-advance on approve</span>}
      </span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={onShowHelp}
          className="p-1.5 rounded text-[#6b7280] hover:text-[#0E3A27] hover:bg-[#F8F5EE]"
          title="Keyboard shortcuts (?)"
          aria-label="Keyboard shortcuts"
        >
          <Keyboard size={16} />
        </button>
        {prevHref ? (
          <Link
            href={prevHref}
            className="flex items-center gap-0.5 px-2 py-1 rounded text-[#03848F] hover:bg-[#F8F5EE] text-xs font-medium"
          >
            <ChevronLeft size={14} /> Prev
          </Link>
        ) : (
          <span className="px-2 py-1 text-xs text-[#d4cfc5]">Prev</span>
        )}
        {nextHref ? (
          <Link
            href={nextHref}
            className="flex items-center gap-0.5 px-2 py-1 rounded text-[#03848F] hover:bg-[#F8F5EE] text-xs font-medium"
          >
            Next <ChevronRight size={14} />
          </Link>
        ) : (
          <span className="px-2 py-1 text-xs text-[#d4cfc5]">Next</span>
        )}
      </div>
    </div>
  )
}
