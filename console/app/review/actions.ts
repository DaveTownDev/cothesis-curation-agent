"use server"

import { execFile } from "child_process"
import { promisify } from "util"
import path from "path"
import { writeFile, mkdir } from "fs/promises"
import { redirect } from "next/navigation"
import type { Firestore, WriteBatch } from "firebase-admin/firestore"
import {
  getReviewQueueItem,
  getFirestoreDb,
  FieldValue,
  getPipelineState,
  getDraftAssessment,
  type ResourceDoc,
} from "@/lib/firestore"
import { validatePublishChecklist } from "@/lib/checklist"
import { reviewNextPath } from "@/lib/review-navigation"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import {
  syncBatchToCompendium,
  syncToCompendium,
} from "@/lib/compendium-sync-actions"
import { buildGoldEvalCase, serializeGoldCase } from "@/lib/eval-export"
import { recordEvalFailure } from "@/lib/failure-bucket"

const execFileAsync = promisify(execFile)

function markPipelineRejected(batch: WriteBatch, db: Firestore, resourceCode: string) {
  if (!resourceCode) return
  const now = new Date().toISOString()
  batch.set(
    db.collection("pipeline_state").doc(resourceCode),
    {
      resource_code: resourceCode,
      state: "hitl_rejected",
      current_stage: "hitl_rejected",
      updated_at: now,
      hitl_outcome: "rejected",
    },
    { merge: true },
  )
}

function repoRoot(): string {
  return path.resolve(process.cwd(), "..")
}

function casesDir(): string {
  return path.join(repoRoot(), "eval", "cases")
}

async function loadReviewContext(itemId: string) {
  const item = await getReviewQueueItem(itemId)
  if (!item) throw new Error("Review queue item not found")
  const [pipelineState, draftDoc] = await Promise.all([
    getPipelineState(item.resource_code),
    getDraftAssessment(item.resource_code),
  ])
  return { item, pipelineState, draftDoc }
}

export { syncBatchToCompendium, syncToCompendium }

export interface ApproveResult {
  nextPath: string
  undo: { itemId: string; resourceCode: string }
}

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
}

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
      markPipelineRejected(batch, db, item.resource_code)
    }
    await batch.commit()
    rejected++
  }

  return { rejected }
}

export async function redirectToReviewQueue(queueQuery: string) {
  redirect(queueQuery ? `/review?${queueQuery}` : "/review")
}

export async function approveItem(
  itemId: string,
  badges: string[],
  editorialNote: string,
  reviewerName: string,
  edited: EditedDescriptions,
  taxonomy: TaxonomyEdits,
  nextId: string | null,
  queueQuery: string,
): Promise<ApproveResult> {
  const item = await getReviewQueueItem(itemId)
  if (!item) throw new Error("Review queue item not found")

  const reviewedBy = reviewerName || "console"
  const workingRecord = {
    ...item.draft_record,
    ...edited,
    ...taxonomy,
  }
  const errors = validatePublishChecklist(
    workingRecord as unknown as Record<string, unknown>,
    reviewedBy,
  )
  if (errors.length > 0) {
    throw new Error(`Checklist failed: ${errors.map((e) => e.message).join("; ")}`)
  }

  const db = getFirestoreDb()
  const batch = db.batch()

  const resourceRef = db.collection("resources").doc(item.resource_code)
  batch.set(resourceRef, {
    ...workingRecord,
    editorial_badges: badges,
    editorial_note: editorialNote.trim() || null,
    editorial_reviewed_by: reviewedBy,
    editorial_reviewed_at: FieldValue.serverTimestamp(),
    editorial_status: "published",
  })

  const queueRef = db.collection("review_queue").doc(itemId)
  batch.update(queueRef, { status: "approved" })

  await batch.commit()
  return {
    nextPath: reviewNextPath(nextId, queueQuery),
    undo: { itemId, resourceCode: item.resource_code },
  }
}

export async function rejectItem(
  itemId: string,
  reason: string,
  nextId: string | null,
  queueQuery: string,
): Promise<{ nextPath: string }> {
  const item = await getReviewQueueItem(itemId)
  if (!item) throw new Error("Review queue item not found")

  const db = getFirestoreDb()
  const batch = db.batch()

  const queueRef = db.collection("review_queue").doc(itemId)
  batch.update(queueRef, { status: "rejected", rejected_reason: reason })

  if (item.resource_code) {
    const resourceRef = db.collection("resources").doc(item.resource_code)
    batch.set(resourceRef, { editorial_status: "archived" }, { merge: true })
    markPipelineRejected(batch, db, item.resource_code)
  }

  await batch.commit()
  return { nextPath: reviewNextPath(nextId, queueQuery) }
}

export async function requeueItem(
  itemId: string,
  reason: string,
  stage: string,
  nextId: string | null,
  queueQuery: string,
  draftPatch?: Record<string, unknown>,
): Promise<{ nextPath: string }> {
  const { item, pipelineState } = await loadReviewContext(itemId)
  const db = getFirestoreDb()
  const queueRef = db.collection("review_queue").doc(itemId)
  const updates: Record<string, unknown> = {
    status: "requeued",
    requeue_reason: reason,
    requeue_stage: stage,
    requeued_at: new Date().toISOString(),
  }
  if (draftPatch && Object.keys(draftPatch).length > 0 && item.draft_record) {
    updates.draft_record = { ...item.draft_record, ...draftPatch }
  }
  await queueRef.update(updates)

  if (stage === "classification") {
    await recordEvalFailure({
      resource_code: item.resource_code,
      field: "classification",
      human_label: reason.trim() || "QA requeue for classification",
      agent: "classification",
      origin: "qa_requeue",
      pipeline_run_id: pipelineState?.pipeline_run_id ?? null,
      review_queue_id: itemId,
    })
  }

  return { nextPath: reviewNextPath(nextId, queueQuery) }
}

export async function exportEvalCaseJson(
  itemId: string,
  edited: EditedDescriptions,
  taxonomy: TaxonomyEdits,
  failureMode?: string | null,
): Promise<{ json: string; eval_id: string }> {
  const { item, pipelineState, draftDoc } = await loadReviewContext(itemId)
  const goldCase = buildGoldEvalCase({
    draft: item.draft_record,
    resourceCode: item.resource_code,
    origin: "hitl",
    failureMode,
    taxonomy,
    edited,
    pipelineState,
    draftDoc,
  })
  return { json: serializeGoldCase(goldCase), eval_id: goldCase.eval_id }
}

export interface AddToGoldSetResult {
  eval_id: string
  case_path: string
  aggregated: boolean
  aggregate_note?: string
}

function isLocalDev(): boolean {
  return !process.env.K_SERVICE
}

export async function addToGoldSet(
  itemId: string,
  edited: EditedDescriptions,
  taxonomy: TaxonomyEdits,
  failureMode?: string | null,
): Promise<AddToGoldSetResult> {
  const { json, eval_id } = await exportEvalCaseJson(itemId, edited, taxonomy, failureMode)
  const caseDoc = JSON.parse(json) as Record<string, unknown>

  const db = getFirestoreDb()
  await db.collection("eval_gold_cases").doc(eval_id).set({
    ...caseDoc,
    updated_at: FieldValue.serverTimestamp(),
  })

  let casePath = `eval_gold_cases/${eval_id}`
  let aggregated = false
  let aggregateNote: string | undefined

  if (isLocalDev()) {
    const dir = casesDir()
    await mkdir(dir, { recursive: true })
    const localPath = path.join(dir, `${eval_id}.json`)
    await writeFile(localPath, json, "utf-8")
    casePath = localPath
    try {
      const root = repoRoot()
      const python = path.join(root, ".venv", "bin", "python")
      await execFileAsync(python, ["-m", "scripts.aggregate_gold_set"], { cwd: root })
      aggregated = true
    } catch {
      aggregateNote =
        "Case written to eval/cases; run python -m scripts.aggregate_gold_set to refresh gold_set.json"
    }
  } else {
    aggregateNote =
      "Case stored in Firestore eval_gold_cases; run python -m scripts.export_gold_from_firestore && aggregate locally"
  }

  return {
    eval_id,
    case_path: casePath,
    aggregated,
    aggregate_note: aggregateNote,
  }
}

export async function flagTaxonomyError(
  itemId: string,
  field: string,
  humanLabel: string,
): Promise<{ failure_id: string }> {
  const { item, pipelineState } = await loadReviewContext(itemId)
  const failureId = await recordEvalFailure({
    resource_code: item.resource_code,
    field,
    human_label: humanLabel,
    origin: "hitl_flag",
    pipeline_run_id: pipelineState?.pipeline_run_id ?? null,
    review_queue_id: itemId,
  })
  return { failure_id: failureId }
}

export async function sendToPromptLab(
  itemId: string,
  field: string,
  humanLabel: string,
): Promise<{ failure_id: string }> {
  const { item, pipelineState } = await loadReviewContext(itemId)
  const failureId = await recordEvalFailure({
    resource_code: item.resource_code,
    field,
    human_label: humanLabel,
    origin: "send_to_lab",
    pipeline_run_id: pipelineState?.pipeline_run_id ?? null,
    review_queue_id: itemId,
  })
  return { failure_id: failureId }
}

export async function undoApprove(itemId: string, resourceCode: string): Promise<void> {
  const item = await getReviewQueueItem(itemId)
  if (!item) throw new Error("Review queue item not found")
  if (item.status !== "approved") throw new Error("This approval can no longer be undone")

  const db = getFirestoreDb()
  const batch = db.batch()
  batch.update(db.collection("review_queue").doc(itemId), { status: "pending" })
  batch.set(
    db.collection("resources").doc(resourceCode),
    { editorial_status: "proposed" },
    { merge: true },
  )
  await batch.commit()
}

export async function reopenForReview(resourceCode: string): Promise<{ queueId: string }> {
  const db = getFirestoreDb()
  const resourceSnap = await db.collection("resources").doc(resourceCode).get()
  if (!resourceSnap.exists) throw new Error("Resource not found")

  const data = resourceSnap.data() as ResourceDoc

  const existing = await db
    .collection("review_queue")
    .where("resource_code", "==", resourceCode)
    .where("status", "==", "pending")
    .limit(1)
    .get()
  if (!existing.empty) {
    return { queueId: existing.docs[0].id }
  }

  const draft = {
    ...data,
    editorial_status: "proposed",
    proposed_badges: data.editorial_badges ?? data.proposed_badges ?? [],
  }

  await db.collection("resources").doc(resourceCode).set(
    { editorial_status: "in_review" },
    { merge: true },
  )

  const ref = await db.collection("review_queue").add({
    resource_code: resourceCode,
    routing: "review_needed",
    reason: "Reopened from published for amendment",
    draft_record: draft,
    panel_result: {},
    status: "pending",
    queued_at: new Date().toISOString(),
  })

  return { queueId: ref.id }
}
