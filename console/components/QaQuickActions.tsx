"use client"

import { Button } from "@/components/ui/button"
import type { QaRecommendation } from "@/lib/qa-recommendations"
import { ArrowRightLeft, Link2, RotateCcw, XCircle } from "lucide-react"

interface Props {
  recommendations: QaRecommendation[]
  onChangeType: (code: string) => void
  onFixUrlAndRequeue: (url: string, rec: QaRecommendation) => void
  onRequeue: (rec: QaRecommendation) => void
  onReject: (reason: string) => void
  onPrefillReject: (reason: string) => void
}

const TYPE_ICONS = {
  change_type: ArrowRightLeft,
  fix_url: Link2,
  requeue: RotateCcw,
  reject_preset: XCircle,
} as const

export function QaQuickActions({
  recommendations,
  onChangeType,
  onFixUrlAndRequeue,
  onRequeue,
  onReject,
  onPrefillReject,
}: Props) {
  if (recommendations.length === 0) return null

  function handleClick(rec: QaRecommendation) {
    switch (rec.type) {
      case "change_type":
        if (rec.resourceTypeCode) onChangeType(rec.resourceTypeCode)
        break
      case "fix_url": {
        const url = rec.suggestedUrl?.trim() ?? ""
        if (url) onFixUrlAndRequeue(url, rec)
        else onRequeue(rec)
        break
      }
      case "requeue":
        onRequeue(rec)
        break
      case "reject_preset":
        if (rec.rejectReason) onReject(rec.rejectReason)
        break
    }
  }

  return (
    <div className="mt-2 space-y-2">
      <p className="text-xs font-semibold text-[#0E3A27]">Recommended actions</p>
      <div className="flex flex-wrap gap-1.5">
        {recommendations.map((rec) => {
          const Icon = TYPE_ICONS[rec.type]
          const isReject = rec.type === "reject_preset"
          return (
            <Button
              key={rec.id}
              type="button"
              size="sm"
              variant={isReject ? "outline" : "secondary"}
              className={`text-xs h-7 px-2.5 ${isReject ? "text-red-600 border-red-200 hover:bg-red-50" : ""}`}
              title={rec.description}
              onClick={() => handleClick(rec)}
            >
              <Icon size={12} />
              {rec.label}
            </Button>
          )
        })}
      </div>
      {recommendations.some((r) => r.type === "reject_preset") && (
        <button
          type="button"
          className="text-[10px] text-[#6b7280] hover:text-[#03848F] underline-offset-2 hover:underline"
          onClick={() => {
            const reason = recommendations.find((r) => r.type === "reject_preset")?.rejectReason
            if (reason) onPrefillReject(reason)
          }}
        >
          Prefill reject reason instead of one-click reject
        </button>
      )}
    </div>
  )
}
