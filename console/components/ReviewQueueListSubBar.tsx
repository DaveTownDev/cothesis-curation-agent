"use client"

import Link from "next/link"
import { Suspense, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { useSubBar } from "@/components/SubBarContext"
import { TriagePresets } from "@/components/TriagePresets"
import type { TriagePreset } from "@/lib/queue-filters"
import { TRIAGE_PRESETS } from "@/lib/queue-filters"

interface Props {
  itemCount: number
  avgQuality: number | null
  avgQualityColor?: string
  startHref: string | null
  preset: TriagePreset
}

export function ReviewQueueListSubBar({
  itemCount,
  avgQuality,
  avgQualityColor,
  startHref,
  preset,
}: Props) {
  const { setContent } = useSubBar()
  const presetLabel = TRIAGE_PRESETS.find((p) => p.id === preset)?.label ?? "All pending"

  useEffect(() => {
    const left = (
      <div className="flex items-center gap-2 min-w-0 overflow-x-auto">
        <Badge variant="outline" className="text-[0.6875rem] shrink-0">
          {presetLabel}
        </Badge>
        <Suspense fallback={null}>
          <TriagePresets active={preset} />
        </Suspense>
      </div>
    )

    const right = (
      <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
        <Badge variant="secondary" className="text-[0.6875rem]">
          {itemCount} pending
        </Badge>
        {avgQuality !== null && avgQualityColor && (
          <span className="text-xs text-[var(--text-body)] hidden md:inline">
            avg <strong style={{ color: avgQualityColor }}>{avgQuality}</strong>
          </span>
        )}
        {startHref && (
          <Link
            href={startHref}
            className="text-xs font-medium text-[var(--green-primary)] hover:underline"
          >
            Start reviewing →
          </Link>
        )}
      </div>
    )

    setContent({ left, right })
    return () => setContent(null)
  }, [
    itemCount,
    avgQuality,
    avgQualityColor,
    startHref,
    preset,
    presetLabel,
    setContent,
  ])

  return null
}
