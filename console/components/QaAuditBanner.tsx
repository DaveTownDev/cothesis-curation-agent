"use client"

import type { QaAudit } from "@/lib/firestore"
import { parseQaRecommendations } from "@/lib/qa-recommendations"
import { QaQuickActions } from "@/components/QaQuickActions"
import type { QaRecommendation } from "@/lib/qa-recommendations"

interface Props {
  qaAudit: QaAudit
  itemReason?: string
  currentType?: string
  currentUrl?: string
  onChangeType: (code: string) => void
  onFixUrlAndRequeue: (url: string, rec: QaRecommendation) => void
  onRequeue: (rec: QaRecommendation) => void
  onReject: (reason: string) => void
  onPrefillReject: (reason: string) => void
}

export function QaAuditBanner({
  qaAudit,
  itemReason,
  currentType,
  currentUrl,
  onChangeType,
  onFixUrlAndRequeue,
  onRequeue,
  onReject,
  onPrefillReject,
}: Props) {
  const recommendations = parseQaRecommendations(qaAudit, itemReason, currentType, currentUrl)
  const verdict = qaAudit.source_verdict

  return (
    <div
      className="rounded-md border px-3 py-2 text-xs"
      style={{
        backgroundColor: verdict === "fail" ? "#fef2f2" : verdict === "warn" ? "#fffbeb" : "#f0fdf4",
        borderColor: verdict === "fail" ? "#fecaca" : verdict === "warn" ? "#fde68a" : "#bbf7d0",
      }}
    >
      <div className="font-semibold text-[#0E3A27]">
        QA audit: source {verdict ?? "—"} · link {qaAudit.url_status ?? "—"}
      </div>
      {qaAudit.source_notes && <p className="mt-1 text-[#4a5568]">{qaAudit.source_notes}</p>}
      {(qaAudit.hallucinations?.length ?? 0) > 0 && (
        <ul className="mt-1 list-disc list-inside text-red-700">
          {qaAudit.hallucinations!.map((h, i) => <li key={i}>{h}</li>)}
        </ul>
      )}
      <QaQuickActions
        recommendations={recommendations}
        onChangeType={onChangeType}
        onFixUrlAndRequeue={onFixUrlAndRequeue}
        onRequeue={onRequeue}
        onReject={onReject}
        onPrefillReject={onPrefillReject}
      />
    </div>
  )
}
