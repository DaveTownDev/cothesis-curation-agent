"use client"

import type { QaAudit } from "@/lib/firestore"
import type { QaRecommendation } from "@/lib/qa-recommendations"
import { QaAuditBanner } from "@/components/QaAuditBanner"

interface Props {
  qaAudit?: QaAudit
  itemReason?: string
  currentType?: string
  currentUrl?: string
  onChangeType: (code: string) => void
  onFixUrlAndRequeue: (url: string, rec: QaRecommendation) => void
  onRequeue: (rec: QaRecommendation) => void
  onReject: (reason: string) => void
  onPrefillReject: (reason: string) => void
}

function hasSourceQa(qa?: QaAudit): boolean {
  if (!qa) return false
  return Boolean(
    qa.source_verdict
    || qa.data_quality
    || qa.url_status
    || (qa.source_issues?.length ?? 0) > 0
    || (qa.hallucinations?.length ?? 0) > 0
    || qa.source_notes,
  )
}

export function QaAuditStatus(props: Props) {
  const { qaAudit } = props

  if (hasSourceQa(qaAudit)) {
    return <QaAuditBanner qaAudit={qaAudit!} {...props} />
  }

  return (
    <div className="rounded-md border border-dashed border-[#d4cfc5] bg-[#F8F5EE] px-3 py-2 text-xs text-[#4a5568]">
      <span className="font-semibold text-[#0E3A27]">Source QA audit not run.</span>
      {" "}Pipeline QC scores are in the Panel tab (right column). Post-batch source-accuracy
      review writes <code className="text-[10px]">qa_audit</code> via{" "}
      <code className="text-[10px]">scripts.write_qa_audit</code> after{" "}
      <code className="text-[10px]">scripts.audit_records</code>.
    </div>
  )
}
