"use server"

import { redirect } from "next/navigation"
import {
  getReviewQueueItem, getFirestoreDb, FieldValue,
} from "@/lib/firestore"
import { validatePublishChecklist } from "@/lib/checklist"

export interface BulkApproveResult {
  approved: number
  skipped: number
  skippedTitles: string[]
}

export async function bulkApproveAsDrafted(
  itemIds: string[],
  reviewerName: string,
): Promise<BulkApproveResult> {
  const reviewedBy = reviewerName.trim() || "console"
  const db = getFirestoreDb()
  let approved = 0
  let skipped = 0
  const skippedTitles: string[] = []

  for (const itemId of itemIds) {
    const item = await getReviewQueueItem(itemId)
    if (!item || item.status !== "pending") {
      skipped++
      skippedTitles.push(item?.draft_record?.title ?? itemId)
      continue
    }
    const draft = item.draft_record
    const errors = validatePublishChecklist(
      draft as unknown as Record<string, unknown>,
      reviewedBy,
    )
    if (errors.length > 0) {
      skipped++
      skippedTitles.push(draft?.title ?? item.resource_code)
      continue
    }

    const batch = db.batch()
    const resourceRef = db.collection("resources").doc(item.resource_code)
    batch.set(resourceRef, {
      ...draft,
      editorial_badges: (draft.proposed_badges ?? []).slice(0, 3),
      editorial_note: draft.editorial_note?.trim() || null,
      editorial_reviewed_by: reviewedBy,
      editorial_reviewed_at: FieldValue.serverTimestamp(),
      editorial_status: "published",
    })
    batch.update(db.collection("review_queue").doc(itemId), { status: "approved" })
    await batch.commit()
    approved++
  }

  return { approved, skipped, skippedTitles }
}

export async function bulkReject(
  itemIds: string[],
  reason: string,
): Promise<{ rejected: number }> {
  if (!reason.trim()) throw new Error("Rejection reason is required")
  const db = getFirestoreDb()
  let rejected = 0

  for (const itemId of itemIds) {
    const item = await getReviewQueueItem(itemId)
    if (!item || item.status !== "pending") continue

    const batch = db.batch()
    batch.update(db.collection("review_queue").doc(itemId), {
      status: "rejected",
      rejected_reason: reason.trim(),
    })
    if (item.resource_code) {
      batch.set(
        db.collection("resources").doc(item.resource_code),
        { editorial_status: "archived" },
        { merge: true },
      )
    }
    await batch.commit()
    rejected++
  }

  return { rejected }
}

export async function redirectToReviewQueue(queueQuery: string) {
  redirect(queueQuery ? `/review?${queueQuery}` : "/review")
}
