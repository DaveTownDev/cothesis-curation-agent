"use client"

import Link from "next/link"
import { useEffect } from "react"
import { ArrowRight, ClipboardList } from "lucide-react"
import { useSubBar } from "@/components/SubBarContext"

export function DashboardSubBar({ pendingReview }: { pendingReview: number }) {
  const { setContent } = useSubBar()

  useEffect(() => {
    const right =
      pendingReview > 0 ? (
        <Link href="/review" className="hitl-nav-cta flex items-center gap-1.5 text-xs">
          <ClipboardList size={14} />
          {pendingReview} awaiting review
          <ArrowRight size={12} />
        </Link>
      ) : (
        <span className="text-xs text-[var(--text-body)]">Queue clear</span>
      )

    setContent({ right })
    return () => setContent(null)
  }, [pendingReview, setContent])

  return null
}
