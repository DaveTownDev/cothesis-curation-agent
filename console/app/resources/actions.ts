"use server"

import {
  FieldValue,
  getFirestoreDb,
  getReviewQueueItem,
  type DraftRecord,
} from "@/lib/firestore"
import { validatePublishChecklist } from "@/lib/checklist"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import {
  forceSyncToCompendium,
  syncToCompendium,
} from "@/lib/compendium-sync-actions"
import {
  getCompendiumConfig,
  setCompendiumVisibility,
  type ItemSyncResult,
} from "@/lib/compendium-sync"

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
  url: string
}

function buildPatch(
  edited: EditedDescriptions,
  taxonomy: TaxonomyEdits,
  editorialNote: string,
  badges: string[],
  reviewerName: string,
): Record<string, unknown> {
  return {
    ...edited,
    ...taxonomy,
    editorial_note: editorialNote.trim() || null,
    editorial_badges: badges.slice(0, 3),
    proposed_badges: badges.slice(0, 3),
    editorial_reviewed_by: reviewerName.trim() || "console",
    editorial_reviewed_at: FieldValue.serverTimestamp(),
  }
}

export async function saveResourceEdits(
  resourceCode: string,
  edited: EditedDescriptions,
  taxonomy: TaxonomyEdits,
  editorialNote: string,
  badges: string[],
  reviewerName: string,
  queueItemId?: string,
): Promise<void> {
  const db = getFirestoreDb()
  const ref = db.collection("resources").doc(resourceCode)
  const existing = await ref.get()
  const wasPublished = existing.exists && existing.data()?.editorial_status === "published"
  const patch = buildPatch(edited, taxonomy, editorialNote, badges, reviewerName)

  await ref.set(
    {
      ...patch,
      resource_code: resourceCode,
      editorial_status: existing.data()?.editorial_status ?? "in_review",
      ...(wasPublished ? { compendium_synced_at: null, compendium_sync_error: null } : {}),
    },
    { merge: true },
  )

  await db.collection("draft_records").doc(resourceCode).set(
    { ...patch, resource_code: resourceCode },
    { merge: true },
  )

  if (queueItemId) {
    const item = await getReviewQueueItem(queueItemId)
    if (item?.draft_record) {
      await db.collection("review_queue").doc(queueItemId).update({
        draft_record: { ...item.draft_record, ...patch } as DraftRecord,
      })
    }
  }
}

export async function publishResource(
  resourceCode: string,
  edited: EditedDescriptions,
  taxonomy: TaxonomyEdits,
  editorialNote: string,
  badges: string[],
  reviewerName: string,
  queueItemId?: string,
): Promise<ItemSyncResult> {
  const working = { ...edited, ...taxonomy, resource_code: resourceCode }
  const errors = validatePublishChecklist(working as Record<string, unknown>, reviewerName || "console")
  if (errors.length > 0) {
    throw new Error(errors.map((e) => e.message).join("; "))
  }

  await saveResourceEdits(resourceCode, edited, taxonomy, editorialNote, badges, reviewerName, queueItemId)

  const db = getFirestoreDb()
  await db.collection("resources").doc(resourceCode).set(
    { editorial_status: "published" },
    { merge: true },
  )

  return { resource_code: resourceCode, ok: true }
}

export async function unpublishResource(resourceCode: string): Promise<{
  ok: boolean
  compendiumWarning?: string
}> {
  const db = getFirestoreDb()
  const ref = db.collection("resources").doc(resourceCode)
  const snap = await ref.get()
  if (!snap.exists) throw new Error("Resource not found")

  const data = snap.data() ?? {}
  await ref.set(
    {
      editorial_status: "archived",
      unpublished_at: FieldValue.serverTimestamp(),
    },
    { merge: true },
  )

  let compendiumWarning: string | undefined
  const compendiumId = data.compendium_id as string | undefined
  const config = getCompendiumConfig()
  if (compendiumId && config) {
    const vis = await setCompendiumVisibility(config, compendiumId, false)
    if (!vis.ok) compendiumWarning = vis.error
  } else if (compendiumId && !config) {
    compendiumWarning = "Compendium credentials not configured — hidden locally only"
  }

  return { ok: true, compendiumWarning }
}

export async function republishResource(resourceCode: string): Promise<ItemSyncResult> {
  const db = getFirestoreDb()
  const ref = db.collection("resources").doc(resourceCode)
  const snap = await ref.get()
  if (!snap.exists) throw new Error("Resource not found")

  const data = snap.data() ?? {}
  const errors = validatePublishChecklist(data as Record<string, unknown>, String(data.editorial_reviewed_by ?? "console"))
  if (errors.length > 0) {
    throw new Error(errors.map((e) => e.message).join("; "))
  }

  await ref.set({ editorial_status: "published", unpublished_at: null }, { merge: true })

  const compendiumId = data.compendium_id as string | undefined
  const config = getCompendiumConfig()
  if (compendiumId && config) {
    await setCompendiumVisibility(config, compendiumId, true)
  }

  return { resource_code: resourceCode, ok: true }
}

export async function pushResourceToCompendium(resourceCode: string): Promise<ItemSyncResult> {
  return forceSyncToCompendium(resourceCode)
}

export { syncToCompendium }
