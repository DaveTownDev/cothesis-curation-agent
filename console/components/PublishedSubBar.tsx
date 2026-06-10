"use client"

import { useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { useSubBar } from "@/components/SubBarContext"

export function PublishedSubBar({
  total,
  synced,
}: {
  total: number
  synced: number
}) {
  const { setContent } = useSubBar()

  useEffect(() => {
    const right = (
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="text-[0.6875rem]">
          {total} resources
        </Badge>
        <span className="text-xs text-[var(--text-body)]">
          {synced} synced to Compendium
        </span>
      </div>
    )

    setContent({ right })
    return () => setContent(null)
  }, [total, synced, setContent])

  return null
}
