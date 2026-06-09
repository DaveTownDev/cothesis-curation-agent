import { initializeApp, getApps, cert, type App } from "firebase-admin/app"
import { getFirestore, type Firestore, FieldValue } from "firebase-admin/firestore"

let app: App
let db: Firestore

function getFirestoreDb(): Firestore {
  if (db) return db

  if (!getApps().length) {
    const projectId = process.env.GOOGLE_CLOUD_PROJECT
    if (!projectId) throw new Error("GOOGLE_CLOUD_PROJECT env var required")

    const serviceAccount = process.env.GOOGLE_APPLICATION_CREDENTIALS_JSON
    if (serviceAccount) {
      app = initializeApp({ credential: cert(JSON.parse(serviceAccount)) })
    } else {
      app = initializeApp({ projectId })
    }
  } else {
    app = getApps()[0]!
  }

  db = getFirestore(app)
  return db
}

export { getFirestoreDb, FieldValue }

// ── Interfaces ───────────────────────────────────────────────────────────────

export interface QualityDimension {
  score: number
  weight: number
  reasoning: string
}

export interface PanelScore {
  dimension: string
  score: number
  pass: boolean
  reasoning: string
}

export interface PanelResult {
  panel_scores?: PanelScore[]
  panel_agreement?: number
  overall_pass?: boolean
  avg_score?: number
  summary?: string
}

export interface ArbiterDecision {
  routing: "auto_accept" | "review_needed" | "auto_exclude"
  composite_score: number
  reason: string
}

export interface ClassificationResult {
  resource_type_code: string
  resource_subtype_code?: string | null
  methodology_codes: string[]
  stage_codes: string[]
  skill_codes: string[]
  relevance_score: number
  classification_confidence: number
  relevance_reasoning?: string | null
  access_type: string
  skip_reason?: string | null
  discipline_codes: string[]
  difficulty_level?: string | null
}

export interface DraftRecord {
  resource_code: string
  title: string
  url: string
  resource_type_code: string
  resource_subtype_code?: string | null
  editorial_description: string
  editorial_description_plain: string
  summary: string
  editorial_note?: string | null
  methodology_codes: string[]
  discipline_codes: string[]
  stage_codes: string[]
  difficulty_level: string
  access_type: string
  skill_codes: string[]
  quality_score: number
  ai_confidence: number
  relevance_score: number
  classification_confidence: number
  proposed_badges: string[]
  strengths?: string[]
  limitations?: string[]
  requires_human_review: boolean
  editorial_status: string
  quality_dimensions?: Record<string, QualityDimension>
  trainee_suitability_score?: number | null
  language_detected?: string | null
  alternative_titles?: string[]
  type_fields?: Record<string, unknown>
  enrichment_sources?: string[]
  enrichment_pending_keys?: string[]
  field_provenance?: Record<string, FieldProvenanceEntry>
  content_format?: string
  time_to_consume?: string
}

export interface FieldProvenanceEntry {
  source?: string
  timestamp?: string
  value?: unknown
}

export interface QaAudit {
  checked_at?: string
  data_quality?: "ok" | "warn" | "fail"
  dq_issues?: string[]
  url_status?: string
  url_code?: number | null
  source_verdict?: "pass" | "warn" | "fail"
  fetchable?: string
  type_match?: string
  methodology_plausible?: string
  description_accurate?: string
  source_issues?: string[]
  hallucinations?: string[]
  source_notes?: string
}

export interface ReviewQueueItem {
  id: string
  resource_code: string
  routing: string
  reason: string
  panel_result: PanelResult | Record<string, unknown>
  draft_record: DraftRecord
  status: "pending" | "approved" | "rejected" | "requeued"
  queued_at: string
  rejected_reason?: string
  requeue_reason?: string
  requeue_stage?: string
  qa_audit?: QaAudit
}

export interface PipelineStateDoc {
  id: string
  resource_code: string
  // Legacy "state" field (old pipeline_state docs) or "current_stage" (new)
  state?: string
  current_stage?: string
  updated_at: string
  pipeline_run_id?: string
  arbiter_decision?: ArbiterDecision
  classification_result?: ClassificationResult
  // Stage timestamps
  discovered_at?: string
  appraised_at?: string
  classified_at?: string
  edited_at?: string
  reconciled_at?: string
  qc_panel_at?: string
  arbiter_decision_at?: string
  skip_reason?: string | null
  ai_assessment_id?: string | null
}

export interface DraftDoc {
  resource_code: string
  model_version?: string
  assessment_prompt_version?: string
  assessed_at?: string
  quality_score: number
  ai_confidence: number
  trainee_suitability_score?: number | null
  language_detected?: string | null
  strengths?: string[]
  limitations?: string[]
  pipeline_run_id?: string
}

export interface ResourceDoc extends DraftRecord {
  editorial_badges?: string[]
  editorial_reviewed_by?: string
  editorial_reviewed_at?: string
  compendium_synced_at?: string | null
  compendium_batch_id?: string | null
  compendium_sync_error?: string | null
}

export interface ReviewQueueFilters {
  type?: string
  minQuality?: number
  maxQuality?: number
  methodology?: string
  sortBy?: "newest" | "oldest" | "quality_asc" | "quality_desc" | "attention"
  preset?: string
  limit?: number
}

// ── Review queue queries ─────────────────────────────────────────────────────

export async function getReviewQueue(
  filters: ReviewQueueFilters = {}
): Promise<ReviewQueueItem[]> {
  const db = getFirestoreDb()
  let query = db
    .collection("review_queue")
    .where("status", "==", "pending") as FirebaseFirestore.Query

  query = query.limit(filters.limit ?? 200)

  const snap = await query.get()
  let items = snap.docs
    .map((d) => ({ id: d.id, ...d.data() } as ReviewQueueItem))
    .filter((i) => i.status === "pending")

  // Client-side sort + filters (no composite Firestore index required)
  const dateSort = filters.sortBy === "oldest" ? "asc" : "desc"
  if (filters.sortBy === "oldest" || filters.sortBy === "newest" || !filters.sortBy) {
    items.sort((a, b) => {
      const ta = new Date(a.queued_at).getTime()
      const tb = new Date(b.queued_at).getTime()
      return dateSort === "asc" ? ta - tb : tb - ta
    })
  }

  // Client-side filters
  if (filters.type) {
    items = items.filter((i) => i.draft_record?.resource_type_code === filters.type)
  }
  if (filters.methodology) {
    items = items.filter((i) =>
      i.draft_record?.methodology_codes?.includes(filters.methodology!)
    )
  }
  if (filters.minQuality !== undefined) {
    items = items.filter((i) => (i.draft_record?.quality_score ?? 0) >= filters.minQuality!)
  }
  if (filters.maxQuality !== undefined) {
    items = items.filter((i) => (i.draft_record?.quality_score ?? 0) <= filters.maxQuality!)
  }
  if (filters.sortBy === "quality_asc") {
    items.sort((a, b) => (a.draft_record?.quality_score ?? 0) - (b.draft_record?.quality_score ?? 0))
  } else if (filters.sortBy === "quality_desc") {
    items.sort((a, b) => (b.draft_record?.quality_score ?? 0) - (a.draft_record?.quality_score ?? 0))
  }

  if (filters.preset === "qa_issues") {
    items = items.filter((i) => {
      const v = i.qa_audit?.source_verdict
      return v === "fail" || v === "warn"
    })
  } else if (filters.preset === "low_confidence") {
    items = items.filter((i) => {
      const d = i.draft_record
      return (d?.classification_confidence ?? 1) < 0.5 || (d?.ai_confidence ?? 100) < 70
    })
  } else if (filters.preset === "ready_to_clear") {
    items = items.filter((i) => {
      const d = i.draft_record
      const qa = i.qa_audit?.source_verdict
      return (
        (qa === "pass" || !qa) &&
        (d?.quality_score ?? 0) >= 80 &&
        (d?.ai_confidence ?? 0) >= 70 &&
        (d?.classification_confidence ?? 0) >= 0.5
      )
    })
  }

  if (filters.sortBy === "attention") {
    const qaRank = (v?: string) => (v === "fail" ? 0 : v === "warn" ? 1 : 2)
    items.sort((a, b) => {
      const qa = qaRank(a.qa_audit?.source_verdict) - qaRank(b.qa_audit?.source_verdict)
      if (qa !== 0) return qa
      const conf =
        (a.draft_record?.classification_confidence ?? 1) -
        (b.draft_record?.classification_confidence ?? 1)
      if (conf !== 0) return conf
      return new Date(a.queued_at).getTime() - new Date(b.queued_at).getTime()
    })
  }

  return items
}

export async function getReviewQueueItem(id: string): Promise<ReviewQueueItem | null> {
  const db = getFirestoreDb()
  const doc = await db.collection("review_queue").doc(id).get()
  if (!doc.exists) return null
  return { id: doc.id, ...doc.data() } as ReviewQueueItem
}

// ── Pipeline state queries ───────────────────────────────────────────────────

export async function getPipelineState(
  resource_code: string
): Promise<PipelineStateDoc | null> {
  const db = getFirestoreDb()
  const snap = await db
    .collection("pipeline_state")
    .where("resource_code", "==", resource_code)
    .limit(1)
    .get()
  if (snap.empty) return null
  const doc = snap.docs[0]
  return { id: doc.id, ...doc.data() } as PipelineStateDoc
}

export async function getPipelineRuns(opts: {
  stage?: string
  limit?: number
} = {}): Promise<PipelineStateDoc[]> {
  const db = getFirestoreDb()
  if (opts.stage) {
    // where-only (no composite index); sort client-side
    const snap = await db
      .collection("pipeline_state")
      .where("state", "==", opts.stage)
      .limit(opts.limit ?? 200)
      .get()
    const docs = snap.docs.map((d) => ({ id: d.id, ...d.data() } as PipelineStateDoc))
    docs.sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? ""))
    return docs
  }
  // No filter → single-field orderBy uses the automatic index
  const snap = await db
    .collection("pipeline_state")
    .orderBy("updated_at", "desc")
    .limit(opts.limit ?? 100)
    .get()
  return snap.docs.map((d) => ({ id: d.id, ...d.data() } as PipelineStateDoc))
}

// ── Draft assessment queries ─────────────────────────────────────────────────

export async function getDraftAssessment(
  resource_code: string
): Promise<DraftDoc | null> {
  const db = getFirestoreDb()
  // where-only (no composite index); newest selected client-side
  const snap = await db
    .collection("drafts")
    .where("resource_code", "==", resource_code)
    .get()
  if (snap.empty) return null
  const docs = snap.docs.map((d) => d.data() as DraftDoc)
  docs.sort((a, b) => (b.assessed_at ?? "").localeCompare(a.assessed_at ?? ""))
  return docs[0]
}

// ── Resources queries ────────────────────────────────────────────────────────

export async function getPublishedResources(limit = 200): Promise<ResourceDoc[]> {
  const db = getFirestoreDb()
  // where-only (no composite index); sort by review date client-side
  const snap = await db
    .collection("resources")
    .where("editorial_status", "==", "published")
    .limit(limit)
    .get()
  const docs = snap.docs.map((d) => ({ ...d.data() } as ResourceDoc))
  docs.sort((a, b) => (b.editorial_reviewed_at ?? "").localeCompare(a.editorial_reviewed_at ?? ""))
  return docs
}

function queueAgeLabel(isoString: string, nowMs: number): string {
  const ms = nowMs - new Date(isoString).getTime()
  const h = Math.floor(ms / 3_600_000)
  const m = Math.floor((ms % 3_600_000) / 60_000)
  if (h >= 24) return `${Math.floor(h / 24)}d`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

export async function getSyncStats(): Promise<{
  synced: number
  pending: number
  total: number
  oldest_pending_at: string | null
  oldest_age_label: string | null
  queue_stale: boolean
}> {
  const db = getFirestoreDb()
  const [resourcesSnap, queueSnap] = await Promise.all([
    db.collection("resources").where("editorial_status", "==", "published").get(),
    // No orderBy → avoids a composite index; oldest computed client-side
    db.collection("review_queue").where("status", "==", "pending").get(),
  ])

  const resources = resourcesSnap.docs.map((d) => d.data())
  const synced = resources.filter((r) => r.compendium_synced_at).length
  const total = resources.length

  let oldest_pending_at: string | null = null
  queueSnap.docs.forEach((d) => {
    const qa = d.data().queued_at as string | undefined
    if (qa && (oldest_pending_at === null || qa < oldest_pending_at)) {
      oldest_pending_at = qa
    }
  })

  const nowMs = Date.now()
  const oldest_age_label = oldest_pending_at
    ? queueAgeLabel(oldest_pending_at, nowMs)
    : null
  const queue_stale = oldest_pending_at
    ? nowMs - new Date(oldest_pending_at).getTime() > 24 * 3_600_000
    : false

  return {
    synced,
    pending: total - synced,
    total,
    oldest_pending_at,
    oldest_age_label,
    queue_stale,
  }
}

// ── Dashboard stats ──────────────────────────────────────────────────────────

export async function getPipelineStats(): Promise<Record<string, number>> {
  const db = getFirestoreDb()
  const [pipelineSnap, queueSnap, resourcesSnap, approvedSnap, rejectedSnap] =
    await Promise.all([
      db.collection("pipeline_state").get(),
      db.collection("review_queue").where("status", "==", "pending").get(),
      db.collection("resources").get(),
      db.collection("review_queue").where("status", "==", "approved").get(),
      db.collection("review_queue").where("status", "==", "rejected").get(),
    ])

  const stateCounts: Record<string, number> = {}
  pipelineSnap.docs.forEach((d) => {
    const state: string = (d.data().state as string) || "unknown"
    stateCounts[state] = (stateCounts[state] || 0) + 1
  })

  return {
    ...stateCounts,
    pending_review: queueSnap.size,
    published: resourcesSnap.size,
    approved: approvedSnap.size,
    rejected: rejectedSnap.size,
  }
}
