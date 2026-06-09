import type { QaAudit } from "@/lib/firestore"
import { RESOURCE_TYPES } from "@/lib/taxonomy"
import type { RequeueStage } from "@/lib/requeue"

export type QaRecommendationType = "change_type" | "fix_url" | "requeue" | "reject_preset"

export interface QaRecommendation {
  id: string
  type: QaRecommendationType
  label: string
  description?: string
  resourceTypeCode?: string
  suggestedUrl?: string
  requeueStage?: RequeueStage
  requeueNote?: string
  rejectReason?: string
}

const KNOWN_RESOURCE_TYPES = new Set(RESOURCE_TYPES.map(([code]) => code))

const RESOURCE_TYPE_IN_TEXT =
  /resource[_\s-]*type\s*[=:]\s*([a-z][a-z0-9_]*)/gi

const TYPE_SUGGESTION_HINT =
  /reasonable match|should be|recommend(?:ed)?|better (?:fit|match)|correct type|instead of/i

const DEAD_LINK_HINT =
  /\b404\b|broken provided url|dead link|does not resolve|unverified source|fabricated|url_status[=:\s]*dead/i

const CANONICAL_HINT =
  /canonical(?:\s+(?:url|link|doi))?[^.]{0,80}(?:fetched successfully|found|resolved|reachable|works)/i

const URL_IN_TEXT = /https?:\/\/[^\s\])"'<>]+/gi

const DOI_IN_TEXT = /\b10\.\d{4,9}\/[^\s\])"'<>]+/gi

function normalizeUrl(raw: string): string {
  const trimmed = raw.replace(/[.,;]+$/, "")
  if (trimmed.startsWith("10.")) return `https://doi.org/${trimmed}`
  return trimmed
}

function isKnownResourceType(code: string): boolean {
  return KNOWN_RESOURCE_TYPES.has(code as (typeof RESOURCE_TYPES)[number][0])
}

function extractSuggestedResourceTypes(text: string): string[] {
  const found: string[] = []
  let match: RegExpExecArray | null
  const re = new RegExp(RESOURCE_TYPE_IN_TEXT.source, "gi")
  while ((match = re.exec(text)) !== null) {
    const code = match[1].toLowerCase()
    if (isKnownResourceType(code) && !found.includes(code)) found.push(code)
  }
  return found
}

function extractUrls(text: string): string[] {
  const urls = [...(text.match(URL_IN_TEXT) ?? [])].map(normalizeUrl)
  const dois = [...(text.match(DOI_IN_TEXT) ?? [])].map(normalizeUrl)
  const combined = [...urls, ...dois]
  return [...new Set(combined)]
}

function collectText(qa: QaAudit | undefined, itemReason?: string): string {
  const parts = [
    qa?.source_notes,
    qa?.type_match,
    qa?.url_status,
    qa?.fetchable,
    ...(qa?.source_issues ?? []),
    ...(qa?.hallucinations ?? []),
    ...(qa?.dq_issues ?? []),
    itemReason,
  ].filter(Boolean)
  return parts.join("\n")
}

function addChangeTypeRecommendations(
  recs: QaRecommendation[],
  seen: Set<string>,
  qa: QaAudit,
  text: string,
  currentType?: string,
) {
  const types = extractSuggestedResourceTypes(text)
  const typeMismatch =
    qa.type_match?.toLowerCase() === "no" ||
    /\btype_match[=:\s]*no\b/i.test(text) ||
    /wrong resource_type/i.test(text)

  for (const code of types) {
    if (code === currentType) continue
    const hasHint = TYPE_SUGGESTION_HINT.test(text) || typeMismatch
    if (!hasHint && qa.source_verdict !== "fail") continue
    const id = `change_type:${code}`
    if (seen.has(id)) continue
    seen.add(id)
    recs.push({
      id,
      type: "change_type",
      label: `Change type → ${code.replace(/_/g, " ")}`,
      description: `QA suggests resource_type ${code}`,
      resourceTypeCode: code,
    })
  }

  if (typeMismatch && types.length === 0 && qa.source_verdict !== "pass") {
    const id = "requeue:classification:type"
    if (!seen.has(id)) {
      seen.add(id)
      recs.push({
        id,
        type: "requeue",
        label: "Re-send for classification",
        description: "QA flagged resource type mismatch",
        requeueStage: "classification",
        requeueNote: "QA audit: resource type does not match source",
      })
    }
  }
}

function addFixUrlRecommendation(
  recs: QaRecommendation[],
  seen: Set<string>,
  qa: QaAudit,
  text: string,
  currentUrl?: string,
) {
  const deadish =
    DEAD_LINK_HINT.test(text) ||
    qa.url_status?.toLowerCase() === "dead" ||
    qa.url_code === 404

  if (!deadish) return

  const urls = extractUrls(text)
  const suggested = urls.find((u) => u !== currentUrl) ?? urls[0]
  const hasCanonical = CANONICAL_HINT.test(text) || Boolean(suggested)

  if (!hasCanonical && !suggested) {
    const id = "requeue:classification:url"
    if (!seen.has(id)) {
      seen.add(id)
      recs.push({
        id,
        type: "requeue",
        label: "Re-send — fix URL in pipeline",
        description: "Dead or broken link with no canonical URL in QA notes",
        requeueStage: "classification",
        requeueNote: "QA audit: broken or dead source URL",
      })
    }
    return
  }

  const id = `fix_url:${suggested ?? "manual"}`
  if (seen.has(id)) return
  seen.add(id)
  recs.push({
    id,
    type: "fix_url",
    label: suggested ? "Fix URL & re-send" : "Fix URL & re-send",
    description: suggested
      ? `Use canonical URL: ${suggested.length > 60 ? suggested.slice(0, 60) + "…" : suggested}`
      : "Update URL then re-send to pipeline",
    suggestedUrl: suggested,
    requeueStage: "classification",
    requeueNote: suggested
      ? `QA audit: replace broken URL with ${suggested}`
      : "QA audit: replace broken source URL",
  })
}

function addRejectRecommendations(
  recs: QaRecommendation[],
  seen: Set<string>,
  qa: QaAudit,
  text: string,
) {
  if ((qa.hallucinations?.length ?? 0) > 0) {
    const id = "reject:hallucination"
    if (!seen.has(id)) {
      seen.add(id)
      const sample = qa.hallucinations!.slice(0, 2).join("; ")
      recs.push({
        id,
        type: "reject_preset",
        label: "Reject — hallucinated content",
        description: sample,
        rejectReason: `Hallucinated content: ${sample}`,
      })
    }
  }

  if (
    qa.source_verdict === "fail" &&
    (DEAD_LINK_HINT.test(text) || /fabricated/i.test(text))
  ) {
    const id = "reject:dead_source"
    if (!seen.has(id)) {
      seen.add(id)
      recs.push({
        id,
        type: "reject_preset",
        label: "Reject — dead / fabricated source",
        rejectReason: "Source URL or DOI is dead, unverifiable, or fabricated (QA audit)",
      })
    }
  }

  if (qa.source_verdict === "fail" && qa.description_accurate?.toLowerCase() === "no") {
    const id = "reject:inaccurate"
    if (!seen.has(id)) {
      seen.add(id)
      recs.push({
        id,
        type: "reject_preset",
        label: "Reject — inaccurate description",
        rejectReason: "Editorial description does not match source (QA audit)",
      })
    }
  }
}

/** Derive one-click QA recommendations from audit fields and routing reason. */
export function parseQaRecommendations(
  qa: QaAudit | undefined,
  itemReason?: string,
  currentType?: string,
  currentUrl?: string,
): QaRecommendation[] {
  if (!qa) return []

  const text = collectText(qa, itemReason)
  const recs: QaRecommendation[] = []
  const seen = new Set<string>()

  addChangeTypeRecommendations(recs, seen, qa, text, currentType)
  addFixUrlRecommendation(recs, seen, qa, text, currentUrl)
  addRejectRecommendations(recs, seen, qa, text)

  return recs
}
