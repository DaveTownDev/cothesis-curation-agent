// TS port of agents/shared/checklist.py validate_publish_checklist
// Platform methodology codes: SYN-* / OBS-* / EVAL-*; legacy RS-/OD-/EI-/QI- are rejected

const PLATFORM_CODE_PATTERN = /^(SYN|OBS|EVAL)-\d{2}$/

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

  // 2. ≥1 platform methodology code
  const codes = (record.methodology_codes as string[] | undefined) || []
  const platformCodes = codes.filter((c) => PLATFORM_CODE_PATTERN.test(c))
  if (platformCodes.length === 0) {
    errors.push({
      field: "methodology_codes",
      message: "At least one platform methodology code (SYN-xx / OBS-xx / EVAL-xx) required",
    })
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
