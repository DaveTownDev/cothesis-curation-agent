// TS port of agents/shared/checklist.py validate_publish_checklist
// Validates against live Compendium taxonomy (data/taxonomy/*.json)

import { METHODOLOGY_CODES, SPECIALTY_OPTIONS } from "@/lib/taxonomy"

const LEGACY_METHODOLOGY_PREFIXES = ["RS-", "OD-", "EI-", "QI-"] as const
const LIVE_METHODOLOGY_CODES = new Set(METHODOLOGY_CODES)

const METHODOLOGY_OPTIONAL_TYPES = new Set([
  "software",
  "community",
  "funding",
  "dataset",
  "template",
  "visual_reference",
])

function methodologyRequiredForType(resourceType: string | undefined): boolean {
  if (!resourceType) return true
  return !METHODOLOGY_OPTIONAL_TYPES.has(resourceType)
}

const VOCAB_SPECIALTY_CODES = new Set(SPECIALTY_OPTIONS.map((s) => s.code))

function normalizeMethodologyCode(code: string): string {
  return code.trim().toUpperCase()
}

function normalizeSpecialtyCode(value: string): string | null {
  const raw = value.trim()
  if (!raw) return null
  const upper = raw.toUpperCase()
  if (VOCAB_SPECIALTY_CODES.has(upper)) return upper
  const slug = raw.toLowerCase()
  const match = SPECIALTY_OPTIONS.find((s) => s.slug === slug)
  return match?.code ?? null
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

  // 2. ≥1 live platform methodology code (type-aware)
  const codes = (record.methodology_codes as string[] | undefined) || []
  const typeCode = record.resource_type_code as string | undefined
  if (methodologyRequiredForType(typeCode) && codes.length === 0) {
    errors.push({
      field: "methodology_codes",
      message: "At least one platform methodology code required",
    })
  } else if (codes.length > 0) {
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

  // 2b. discipline_codes — validate specialty codes when present (optional field)
  const disciplines = record.discipline_codes as string[] | undefined
  if (disciplines && disciplines.length > 0) {
    for (const raw of disciplines) {
      const norm = normalizeSpecialtyCode(raw)
      if (!norm) {
        errors.push({
          field: "discipline_codes",
          message: `Invalid specialty code '${raw}' (not in vocabulary)`,
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
