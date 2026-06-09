// TS port of agents/shared/checklist.py validate_publish_checklist
// Validates against live Compendium taxonomy (data/taxonomy/*.json)

import { METHODOLOGY_CODES, SPECIALTY_OPTIONS } from "@/lib/taxonomy"

const LEGACY_METHODOLOGY_PREFIXES = ["RS-", "OD-", "EI-", "QI-"] as const
const LIVE_METHODOLOGY_CODES = new Set(METHODOLOGY_CODES)
const LIVE_SPECIALTY_SLUGS = new Set(SPECIALTY_OPTIONS.map((s) => s.slug))

function normalizeMethodologyCode(code: string): string {
  return code.trim().toUpperCase()
}

function normalizeDisciplineSlug(slug: string): string {
  return slug.trim().toLowerCase()
}

export interface ChecklistError {
  field: string
  message: string
}

export function validatePublishChecklist(
  record: Record<string, unknown>,
  reviewedBy: string
): ChecklistError[] {
  const errors: ChecklistError[] = []

  // 1. editorial_description present
  const desc = record.editorial_description as string | undefined
  if (!desc || desc.trim().length === 0) {
    errors.push({ field: "editorial_description", message: "Editorial description is required" })
  }

  // 2. ≥1 live platform methodology code
  const codes = (record.methodology_codes as string[] | undefined) || []
  if (codes.length === 0) {
    errors.push({
      field: "methodology_codes",
      message: "At least one platform methodology code required",
    })
  } else {
    for (const code of codes) {
      for (const legacy of LEGACY_METHODOLOGY_PREFIXES) {
        if (code.startsWith(legacy)) {
          errors.push({
            field: "methodology_codes",
            message: `Legacy methodology code '${code}' — emit platform codes only`,
          })
        }
      }
      const norm = normalizeMethodologyCode(code)
      if (!LIVE_METHODOLOGY_CODES.has(norm)) {
        errors.push({
          field: "methodology_codes",
          message: `Unknown platform code '${code}' (not in live Compendium taxonomy)`,
        })
      }
    }
  }

  // 2b. discipline_codes — validate slugs when present (optional field)
  const disciplines = record.discipline_codes as string[] | undefined
  if (disciplines && disciplines.length > 0) {
    for (const slug of disciplines) {
      const norm = normalizeDisciplineSlug(slug)
      if (!LIVE_SPECIALTY_SLUGS.has(norm)) {
        errors.push({
          field: "discipline_codes",
          message: `Invalid discipline slug '${slug}' (not in live Compendium taxonomy)`,
        })
      }
    }
  }

  // 3. quality_score ≥ 60
  const qs = record.quality_score as number | undefined
  if (qs === undefined || qs === null) {
    errors.push({ field: "quality_score", message: "quality_score is required" })
  } else if (qs < 60) {
    errors.push({ field: "quality_score", message: `quality_score ${qs} is below minimum (60)` })
  }

  // 4. URL present
  const url = record.url as string | undefined
  if (!url || url.trim().length === 0) {
    errors.push({ field: "url", message: "Resource URL is required" })
  }

  // 5 & 6. editorial_reviewed_by (injected by caller)
  if (!reviewedBy || reviewedBy.trim().length === 0) {
    errors.push({ field: "editorial_reviewed_by", message: "Reviewer identity required" })
  }

  return errors
}
