"use client"

import Link from "next/link"
import { useEffect } from "react"
import { ArrowLeft, ChevronLeft, ChevronRight, Keyboard } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useSubBar } from "@/components/SubBarContext"

interface Props {
  backHref: string
  routing?: string | null
  position: number
  total: number
  prevHref: string | null
  nextHref: string | null
}

export function ReviewDetailSubBar({
  backHref,
  routing,
  position,
  total,
  prevHref,
  nextHref,
}: Props) {
  const { setContent } = useSubBar()

  useEffect(() => {
    const left = (
      <div className="flex items-center gap-2 min-w-0">
        <Link href={backHref} className="hitl-subbar-back">
          <ArrowLeft size={14} />
          Review queue
        </Link>
        {routing && (
          <Badge variant="outline" className="text-[0.6875rem] capitalize shrink-0">
            {routing.replace(/_/g, " ")}
          </Badge>
        )}
      </div>
    )

    const right = (
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xs text-[var(--text-body)] hidden sm:inline">
          Item <strong className="text-[var(--text-primary)]">{position}</strong> of{" "}
          <strong className="text-[var(--text-primary)]">{total}</strong>
        </span>
        <button
          type="button"
          onClick={() => window.dispatchEvent(new Event("cothesis-show-shortcuts"))}
          className="hitl-subbar-icon-btn"
          title="Keyboard shortcuts (?)"
          aria-label="Keyboard shortcuts"
        >
          <Keyboard size={15} />
        </button>
        {prevHref ? (
          <Link href={prevHref} className="hitl-subbar-nav-btn">
            <ChevronLeft size={14} />
            Prev
          </Link>
        ) : (
          <span className="hitl-subbar-nav-btn is-disabled">Prev</span>
        )}
        {nextHref ? (
          <Link href={nextHref} className="hitl-subbar-nav-btn">
            Next
            <ChevronRight size={14} />
          </Link>
        ) : (
          <span className="hitl-subbar-nav-btn is-disabled">Next</span>
        )}
      </div>
    )

    setContent({ left, right })
    return () => setContent(null)
  }, [backHref, routing, position, total, prevHref, nextHref, setContent])

  return null
}
