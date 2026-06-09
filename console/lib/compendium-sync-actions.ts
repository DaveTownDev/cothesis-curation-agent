"use server"

import { FieldValue, getFirestoreDb, type ResourceDoc } from "@/lib/firestore"
import {
  getCompendiumConfig,
  postToCompendium,
  type BatchSyncResult,
  type CompendiumRecordInput,
  type ItemSyncResult,
  type ResourceSyncOutcome,
} from "@/lib/compendium-sync"

const BATCH_SIZE = 50

function syncUpdate(outcome: ResourceSyncOutcome, batchId: string): Record<string, unknown> {
  const update: Record<string, unknown> = {
    compendium_synced_at: FieldValue.serverTimestamp(),
    compendium_batch_id: batchId,
    compendium_sync_error: null,
  }
  if (outcome.compendium_id) update.compendium_id = outcome.compendium_id
  if (outcome.compendium_url) update.compendium_url = outcome.compendium_url
  return update
}

async function loadPublishedResource(resourceCode: string): Promise<(ResourceDoc & { _doc_id: string }) | null> {
  const db = getFirestoreDb()
  const snap = await db.collection("resources").doc(resourceCode).get()
  if (!snap.exists) return null
  const data = snap.data() as ResourceDoc
  if (data.editorial_status !== "published") return null
  return { ...data, _doc_id: snap.id }
}

export async function syncToCompendium(resourceCode: string): Promise<ItemSyncResult> {
  const config = getCompendiumConfig()
  if (!config) {
    return {
      resource_code: resourceCode,
      ok: false,
      error: "Compendium sync not configured (COMPENDIUM_IMPORT_URL + IMPORT_API_KEY)",
    }
  }

  const record = await loadPublishedResource(resourceCode)
  if (!record) {
    return { resource_code: resourceCode, ok: false, error: "Published resource not found" }
  }
  if (record.compendium_synced_at && !record.compendium_sync_error) {
    return {
      resource_code: resourceCode,
      ok: true,
      skipped: true,
      compendium_id: record.compendium_id ?? null,
      compendium_url: record.compendium_url ?? null,
    }
  }

  const db = getFirestoreDb()
  try {
    const batch = await postToCompendium([record as CompendiumRecordInput], config)
    const outcome = batch.outcomes[0] ?? { compendium_id: null, compendium_url: null }
    await db.collection("resources").doc(record._doc_id).update(syncUpdate(outcome, batch.import_batch_id))
    return {
      resource_code: resourceCode,
      ok: true,
      compendium_id: outcome.compendium_id,
      compendium_url: outcome.compendium_url,
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    await db.collection("resources").doc(record._doc_id).update({ compendium_sync_error: message })
    return { resource_code: resourceCode, ok: false, error: message }
  }
}

export async function syncBatchToCompendium(resourceCodes: string[]): Promise<BatchSyncResult> {
  const config = getCompendiumConfig()
  const results: ItemSyncResult[] = []
  let synced = 0
  let failed = 0
  let skipped = 0

  if (!config) {
    return {
      synced: 0,
      failed: resourceCodes.length,
      skipped: 0,
      results: resourceCodes.map((code) => ({
        resource_code: code,
        ok: false,
        error: "Compendium sync not configured (COMPENDIUM_IMPORT_URL + IMPORT_API_KEY)",
      })),
    }
  }

  const db = getFirestoreDb()
  const toSync: Array<ResourceDoc & { _doc_id: string }> = []

  for (const code of resourceCodes) {
    const record = await loadPublishedResource(code)
    if (!record) {
      failed++
      results.push({ resource_code: code, ok: false, error: "Published resource not found" })
      continue
    }
    if (record.compendium_synced_at && !record.compendium_sync_error) {
      skipped++
      results.push({
        resource_code: code,
        ok: true,
        skipped: true,
        compendium_id: record.compendium_id ?? null,
        compendium_url: record.compendium_url ?? null,
      })
      continue
    }
    toSync.push(record)
  }

  for (let i = 0; i < toSync.length; i += BATCH_SIZE) {
    const chunk = toSync.slice(i, i + BATCH_SIZE)
    try {
      const batch = await postToCompendium(chunk as CompendiumRecordInput[], config)
      for (let j = 0; j < chunk.length; j++) {
        const record = chunk[j]!
        const outcome = batch.outcomes[j] ?? { compendium_id: null, compendium_url: null }
        await db.collection("resources").doc(record._doc_id).update(syncUpdate(outcome, batch.import_batch_id))
        synced++
        results.push({
          resource_code: record.resource_code ?? record._doc_id,
          ok: true,
          compendium_id: outcome.compendium_id,
          compendium_url: outcome.compendium_url,
        })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      for (const record of chunk) {
        await db.collection("resources").doc(record._doc_id).update({ compendium_sync_error: message })
        failed++
        results.push({
          resource_code: record.resource_code ?? record._doc_id,
          ok: false,
          error: message,
        })
      }
    }
  }

  return { synced, failed, skipped, results }
}

/** Fire-and-forget helper for approve paths — never throws. */
export async function trySyncAfterApprove(resourceCode: string): Promise<ItemSyncResult> {
  try {
    return await syncToCompendium(resourceCode)
  } catch (err) {
    return {
      resource_code: resourceCode,
      ok: false,
      error: err instanceof Error ? err.message : String(err),
    }
  }
}
