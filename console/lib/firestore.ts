import { initializeApp, getApps, cert, type App } from "firebase-admin/app"
import { getFirestore, type Firestore, FieldValue } from "firebase-admin/firestore"
import { hasQaIssues, qaAttentionRank } from "@/lib/qa-issues"

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
  requeued_at?: string
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
  quality_dimensions?: Record<string, QualityDimension>
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
  compendium_id?: string | null
  compendium_url?: string | null
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

// ── Prompt improvement loop collections (docs/SCHEMA.md P3-01) ───────────────

export type FailureOrigin = "hitl_flag" | "qa_requeue" | "send_to_lab" | "benchmark"

export interface EvalFailureBucketDoc {
  resource_code: string
  agent: string
  field: string
  human_label: string
  prompt_version: string
  created_at: string
  origin: FailureOrigin
  pipeline_run_id?: string | null
  review_queue_id?: string | null
  consumed_by_lab_run_id?: string | null
}

export type ProposalStatus = "pending" | "approved" | "rejected" | "merged"

export interface EvalDelta {
  baseline_path?: string
  subset_cases?: number
  passed?: boolean
  rubric_scores?: Record<string, number>
  response_match_score?: number | null
  notes?: string
}

export interface PromptProposalDoc {
  id: string
  status: ProposalStatus
  target_prompt_file: string
  unified_diff: string
  rationale: string
  failure_bucket_ids: string[]
  eval_delta?: EvalDelta | null
  lab_run_id?: string | null
  created_at: string
  reviewed_at?: string | null
  reviewed_by?: string | null
  review_notes?: string | null
}

export type LabRunStatus = "running" | "succeeded" | "failed" | "cancelled"

export interface PromptLabRunDoc {
  id: string
  status: LabRunStatus
  started_at: string
  completed_at?: string | null
  failure_bucket_ids: string[]
  max_cases: number
  proposal_ids: string[]
  model_version?: string | null
  error?: string | null
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
    // Human review queue — auto_accept is recorded in pipeline_state only.
    .filter((i) => i.routing !== "auto_accept")

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
    items = items.filter((i) => hasQaIssues(i.qa_audit))
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
    items.sort((a, b) => {
      const qa = qaAttentionRank(a.qa_audit) - qaAttentionRank(b.qa_audit)
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

// ── Firestore value helpers ──────────────────────────────────────────────────

/** Coerce Firestore Timestamp / Date / ISO string to ms for sorting. */
function sortableTime(value: unknown): number {
  if (value == null || value === "") return 0
  if (typeof value === "string") {
    const t = new Date(value).getTime()
    return Number.isNaN(t) ? 0 : t
  }
  if (typeof value === "number") return value
  if (value instanceof Date) return value.getTime()
  if (typeof value === "object") {
    const v = value as { toDate?: () => Date; toMillis?: () => number; _seconds?: number }
    if (typeof v.toDate === "function") return v.toDate().getTime()
    if (typeof v.toMillis === "function") return v.toMillis()
    if (typeof v._seconds === "number") return v._seconds * 1000
  }
  return 0
}

function compareTimeDesc(a: unknown, b: unknown): number {
  return sortableTime(b) - sortableTime(a)
}

/** Serialize Firestore timestamp fields for client components / JSON. */
export function serializeFirestoreDate(value: unknown): string | undefined {
  const ms = sortableTime(value)
  return ms > 0 ? new Date(ms).toISOString() : undefined
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
    docs.sort((a, b) => compareTimeDesc(a.updated_at, b.updated_at))
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
  docs.sort((a, b) => compareTimeDesc(a.assessed_at, b.assessed_at))
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
  const docs = snap.docs.map((d) => ({
    resource_code: d.id,
    ...d.data(),
  } as ResourceDoc))
  docs.sort((a, b) => compareTimeDesc(a.editorial_reviewed_at, b.editorial_reviewed_at))
  return docs
}

export async function getResourceRecord(resourceCode: string): Promise<ResourceDoc | null> {
  const db = getFirestoreDb()
  const snap = await db.collection("resources").doc(resourceCode).get()
  if (!snap.exists) return null
  return { resource_code: resourceCode, ...snap.data() } as ResourceDoc
}

export interface ResourceLiveStatus {
  editorial_status?: string
  compendium_synced_at?: string | null
  compendium_sync_error?: string | null
  compendium_url?: string | null
  compendium_id?: string | null
}

export async function getResourceLiveStatusMap(
  resourceCodes: string[],
): Promise<Record<string, ResourceLiveStatus>> {
  const db = getFirestoreDb()
  const unique = [...new Set(resourceCodes.filter(Boolean))]
  const map: Record<string, ResourceLiveStatus> = {}
  const CHUNK = 100

  for (let i = 0; i < unique.length; i += CHUNK) {
    const chunk = unique.slice(i, i + CHUNK)
    const refs = chunk.map((code) => db.collection("resources").doc(code))
    const snaps = await db.getAll(...refs)
    for (const snap of snaps) {
      if (!snap.exists) continue
      const data = snap.data()!
      map[snap.id] = {
        editorial_status: data.editorial_status as string | undefined,
        compendium_synced_at: data.compendium_synced_at as string | null | undefined,
        compendium_sync_error: data.compendium_sync_error as string | null | undefined,
        compendium_url: data.compendium_url as string | null | undefined,
        compendium_id: data.compendium_id as string | null | undefined,
      }
    }
  }

  return map
}

export async function getDraftRecordDoc(resourceCode: string): Promise<DraftRecord | null> {
  const db = getFirestoreDb()
  const snap = await db.collection("draft_records").doc(resourceCode).get()
  if (!snap.exists) return null
  return { resource_code: resourceCode, ...snap.data() } as DraftRecord
}

export type EditableResourceSource = "published" | "archived" | "draft" | "queue"

export interface EditableResource {
  resource_code: string
  draft: DraftRecord
  source: EditableResourceSource
  editorial_status: string
  queue_item_id?: string
}

export async function getEditableResource(resourceCode: string): Promise<EditableResource | null> {
  const db = getFirestoreDb()
  const resource = await getResourceRecord(resourceCode)
  if (resource?.title) {
    const status = resource.editorial_status ?? "proposed"
    const source: EditableResourceSource =
      status === "published" ? "published" : status === "archived" ? "archived" : "draft"
    return { resource_code: resourceCode, draft: resource as unknown as DraftRecord, source, editorial_status: status }
  }

  const draftRecord = await getDraftRecordDoc(resourceCode)
  if (draftRecord?.title) {
    return {
      resource_code: resourceCode,
      draft: draftRecord,
      source: "draft",
      editorial_status: draftRecord.editorial_status ?? "proposed",
    }
  }

  for (const status of ["pending", "approved", "rejected"] as const) {
    const queueSnap = await db
      .collection("review_queue")
      .where("resource_code", "==", resourceCode)
      .where("status", "==", status)
      .limit(1)
      .get()
    if (!queueSnap.empty) {
      const doc = queueSnap.docs[0]!
      const data = doc.data()
      const draft = data.draft_record as DraftRecord | undefined
      if (draft?.title) {
        return {
          resource_code: resourceCode,
          draft: { ...draft, resource_code: resourceCode },
          source: status === "pending" ? "queue" : "draft",
          editorial_status: status === "approved" ? "published" : "proposed",
          queue_item_id: status === "pending" ? doc.id : undefined,
        }
      }
    }
  }

  const pipeline = await getPipelineState(resourceCode)
  if (pipeline?.classification_result) {
    const cr = pipeline.classification_result
    const minimal = {
      resource_code: resourceCode,
      title: resourceCode.replace(/-/g, " "),
      url: "",
      resource_type_code: cr.resource_type_code ?? "article",
      resource_subtype_code: cr.resource_subtype_code ?? null,
      editorial_description: "",
      editorial_description_plain: "",
      summary: "",
      methodology_codes: [...(cr.methodology_codes ?? [])],
      discipline_codes: [...(cr.discipline_codes ?? [])],
      stage_codes: [...(cr.stage_codes ?? [])],
      skill_codes: [...(cr.skill_codes ?? [])],
      difficulty_level: cr.difficulty_level ?? "intermediate",
      access_type: cr.access_type ?? "free",
      quality_score: 0,
      ai_confidence: 0,
      relevance_score: cr.relevance_score ?? 0,
      classification_confidence: cr.classification_confidence ?? 0,
      proposed_badges: [],
      requires_human_review: true,
      editorial_status: "proposed",
    } as DraftRecord
    return {
      resource_code: resourceCode,
      draft: minimal,
      source: "draft",
      editorial_status: "proposed",
    }
  }

  return null
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
  const synced = resources.filter(
    (r) => r.compendium_synced_at && r.compendium_id && r.compendium_url && !r.compendium_sync_error,
  ).length
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

// ── Prompt lab queries ───────────────────────────────────────────────────────

export async function getPromptProposals(
  status?: ProposalStatus,
  limit = 50,
): Promise<PromptProposalDoc[]> {
  const db = getFirestoreDb()
  let query = db.collection("prompt_proposals") as FirebaseFirestore.Query
  if (status) {
    query = query.where("status", "==", status)
  }
  const snap = await query.limit(limit).get()
  const docs = snap.docs.map((d) => ({
    id: d.id,
    ...d.data(),
    created_at: serializeFirestoreDate(d.data().created_at) ?? String(d.data().created_at ?? ""),
    reviewed_at: serializeFirestoreDate(d.data().reviewed_at) ?? null,
  })) as PromptProposalDoc[]
  docs.sort((a, b) => sortableTime(b.created_at) - sortableTime(a.created_at))
  return docs
}

export async function getPromptProposal(id: string): Promise<PromptProposalDoc | null> {
  const db = getFirestoreDb()
  const snap = await db.collection("prompt_proposals").doc(id).get()
  if (!snap.exists) return null
  const data = snap.data()!
  return {
    id: snap.id,
    ...data,
    created_at: serializeFirestoreDate(data.created_at) ?? String(data.created_at ?? ""),
    reviewed_at: serializeFirestoreDate(data.reviewed_at) ?? null,
  } as PromptProposalDoc
}

export async function getRecentEvalFailures(limit = 20): Promise<Array<EvalFailureBucketDoc & { id: string }>> {
  const db = getFirestoreDb()
  const snap = await db.collection("eval_failure_bucket").limit(limit).get()
  const docs = snap.docs.map((d) => ({
    id: d.id,
    ...d.data(),
    created_at: serializeFirestoreDate(d.data().created_at) ?? String(d.data().created_at ?? ""),
  })) as Array<EvalFailureBucketDoc & { id: string }>
  docs.sort((a, b) => sortableTime(b.created_at) - sortableTime(a.created_at))
  return docs
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
