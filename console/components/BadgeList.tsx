"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"

const BADGE_LABELS: Record<string, string> = {
  editors_choice: "Editor's Choice",
  best_free: "Best Free",
  best_beginners: "Best for Beginners",
  best_time_poor: "Best for Time-Poor",
  essential: "Essential",
  expert_pick: "Expert Pick",
}

const ALL_BADGES = Object.keys(BADGE_LABELS)

interface Props {
  proposed: string[]
  onChange: (selected: string[]) => void
}

export function BadgeList({ proposed, onChange }: Props) {
  const [selected, setSelected] = useState<string[]>(proposed.slice(0, 3))

  function toggle(badge: string) {
    setSelected((prev) => {
      const next = prev.includes(badge)
        ? prev.filter((b) => b !== badge)
        : prev.length < 3
        ? [...prev, badge]
        : prev
      onChange(next)
      return next
    })
  }

  return (
    <div>
      <p className="text-xs text-[#6b7280] mb-2">
        AI proposed: {proposed.length > 0 ? proposed.join(", ") : "none"} — select up to 3 to
        ratify
      </p>
      <div className="flex flex-wrap gap-2">
        {ALL_BADGES.map((badge) => {
          const isSelected = selected.includes(badge)
          const isProposed = proposed.includes(badge)
          return (
            <button
              key={badge}
              type="button"
              onClick={() => toggle(badge)}
              className="focus:outline-none"
            >
              <Badge
                variant={isSelected ? "default" : isProposed ? "secondary" : "outline"}
                className={`cursor-pointer ${
                  isSelected
                    ? "ring-2 ring-[#289642] ring-offset-1"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                {BADGE_LABELS[badge]}
              </Badge>
            </button>
          )
        })}
      </div>
    </div>
  )
}
