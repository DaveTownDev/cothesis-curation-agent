import type { DraftDoc, DraftRecord } from "@/lib/firestore"

/**
 * review_queue.draft_record is the HITL working copy; appraisal-only fields
 * (ai_confidence, quality_dimensions, strengths) live in `drafts` when older
 * pipeline runs omitted them from assembly. Merge for display without mutating
 * the queue doc until the reviewer saves.
 */
export function mergeAppraisalFields(
  draft: DraftRecord,
  draftDoc: DraftDoc | null | undefined,
): DraftRecord {
  if (!draftDoc) return draft

  const merged: DraftRecord = { ...draft }

  if (merged.ai_confidence == null && draftDoc.ai_confidence != null) {
    merged.ai_confidence = draftDoc.ai_confidence
  }
  if (!merged.quality_dimensions && draftDoc.quality_dimensions) {
    merged.quality_dimensions = draftDoc.quality_dimensions
  }
  if (merged.trainee_suitability_score == null && draftDoc.trainee_suitability_score != null) {
    merged.trainee_suitability_score = draftDoc.trainee_suitability_score
  }
  if (!merged.language_detected && draftDoc.language_detected) {
    merged.language_detected = draftDoc.language_detected
  }
  if (!merged.strengths?.length && draftDoc.strengths?.length) {
    merged.strengths = draftDoc.strengths
  }
  if (!merged.limitations?.length && draftDoc.limitations?.length) {
    merged.limitations = draftDoc.limitations
  }

  return merged
}
