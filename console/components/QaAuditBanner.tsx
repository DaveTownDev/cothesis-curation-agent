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
  const dataQuality = qaAudit.data_quality
  const bannerTone =
    verdict === "fail" || dataQuality === "fail" || qaAudit.url_status === "dead"
      ? "fail"
      : verdict === "warn" || dataQuality === "warn" || qaAudit.url_status === "unreachable"
        ? "warn"
        : "pass"

  return (
    <div
      className="rounded-md border px-3 py-2 text-xs"
      style={{
        backgroundColor: bannerTone === "fail" ? "#fef2f2" : bannerTone === "warn" ? "#fffbeb" : "#f0fdf4",
        borderColor: bannerTone === "fail" ? "#fecaca" : bannerTone === "warn" ? "#fde68a" : "#bbf7d0",
      }}
    >
      <div className="font-semibold text-[#0E3A27]">
        QA audit: source {verdict ?? "—"} · data {dataQuality ?? "—"} · link {qaAudit.url_status ?? "—"}
      </div>
      {(qaAudit.dq_issues?.length ?? 0) > 0 && (
        <ul className="mt-1 list-disc list-inside text-[#4a5568]">
          {qaAudit.dq_issues!.slice(0, 6).map((issue, i) => <li key={i}>{issue}</li>)}
        </ul>
      )}
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
