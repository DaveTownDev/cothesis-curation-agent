import type { QaAudit } from "@/lib/firestore"

/** True when any QA audit layer has been written to the queue doc. */
export function hasQaAuditData(qa?: QaAudit): boolean {
  if (!qa) return false
  return Boolean(
    qa.source_verdict
    || qa.data_quality
    || qa.url_status
    || (qa.dq_issues?.length ?? 0) > 0
    || (qa.source_issues?.length ?? 0) > 0
    || (qa.hallucinations?.length ?? 0) > 0
    || qa.source_notes,
  )
}

/** Triage filter: source-accuracy fail/warn OR data-quality fail/warn OR dead link. */
export function hasQaIssues(qa?: QaAudit): boolean {
  if (!qa) return false
  const sv = qa.source_verdict
  if (sv === "fail" || sv === "warn") return true
  const dq = qa.data_quality
  if (dq === "fail" || dq === "warn") return true
  const url = qa.url_status
  if (url === "dead" || url === "unreachable") return true
  return false
}

/** Lower rank = needs attention first (attention sort). */
export function qaAttentionRank(qa?: QaAudit): number {
  if (!qa) return 3
  if (qa.source_verdict === "fail" || qa.data_quality === "fail") return 0
  if (
    qa.source_verdict === "warn"
    || qa.data_quality === "warn"
    || qa.url_status === "dead"
    || qa.url_status === "unreachable"
  ) {
    return 1
  }
  if (qa.source_verdict === "pass" || qa.data_quality === "ok") return 2
  return 3
}

export type QaDisplayVerdict = "pass" | "warn" | "fail" | "pending"

/** Badge label for the queue table — prefers source verdict, then data quality. */
export function qaDisplayVerdict(qa?: QaAudit): QaDisplayVerdict {
  if (!qa) return "pending"
  if (qa.source_verdict === "fail" || qa.data_quality === "fail") return "fail"
  if (
    qa.source_verdict === "warn"
    || qa.data_quality === "warn"
    || qa.url_status === "dead"
    || qa.url_status === "unreachable"
  ) {
    return "warn"
  }
  if (qa.source_verdict === "pass" || qa.data_quality === "ok") return "pass"
  return "pending"
}
