import type { Metadata } from "next"
import { notFound, redirect } from "next/navigation"
import Link from "next/link"
import { requireAuth } from "@/lib/auth"
import {
  getReviewQueueItem, getFirestoreDb, FieldValue,
  getPipelineState, getDraftAssessment,
} from "@/lib/firestore"
import { validatePublishChecklist } from "@/lib/checklist"
import { ReviewWorkspace } from "./ReviewWorkspace"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, ExternalLink } from "lucide-react"

const TYPE_LABELS: Record<string, string> = {
  article: "Article", book: "Book", book_chapter: "Book chapter", video: "Video",
  podcast: "Podcast", software: "Software", reporting_guideline: "Guideline",
  course: "Course", web_guide: "Web guide", template: "Template",
  visual_reference: "Visual", dataset: "Dataset", community: "Community", funding: "Funding",
}

// ── Server Actions ──────────────────────────────────────────────────────────

async function approveItem(
  itemId: string,
  badges: string[],
  editorialNote: string,
  reviewerName: string,
  edited: { editorial_description: string; summary: string; editorial_description_plain: string }
) {
  "use server"
  const item = await getReviewQueueItem(itemId)
  if (!item) throw new Error("Review queue item not found")

  const reviewedBy = reviewerName || "console"
  const workingRecord = {
    ...item.draft_record,
    editorial_description: edited.editorial_description,
    summary: edited.summary,
    editorial_description_plain: edited.editorial_description_plain,
  }
  const errors = validatePublishChecklist(
    workingRecord as unknown as Record<string, unknown>,
    reviewedBy
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
  redirect("/review")
}

async function rejectItem(itemId: string, reason: string) {
  "use server"
  const item = await getReviewQueueItem(itemId)
  if (!item) throw new Error("Review queue item not found")

  const db = getFirestoreDb()
  const batch = db.batch()

  const queueRef = db.collection("review_queue").doc(itemId)
  batch.update(queueRef, { status: "rejected", rejected_reason: reason })

  if (item.resource_code) {
    const resourceRef = db.collection("resources").doc(item.resource_code)
    batch.set(resourceRef, { editorial_status: "archived" }, { merge: true })
  }

  await batch.commit()
  redirect("/review")
}

async function requeueItem(itemId: string, reason: string) {
  "use server"
  const db = getFirestoreDb()
  const queueRef = db.collection("review_queue").doc(itemId)
  await queueRef.update({
    status: "pending",
    requeue_reason: reason,
    queued_at: new Date().toISOString(),
  })
  redirect("/review")
}

// ── Page ────────────────────────────────────────────────────────────────────

export const revalidate = 0

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  const item = await getReviewQueueItem(id)
  const title = item?.draft_record?.title ?? item?.resource_code ?? "Review"
  return { title: `${title} — CoThesis` }
}

export default async function ReviewDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  await requireAuth()
  const { id } = await params

  const item = await getReviewQueueItem(id)
  if (!item) notFound()

  const draft = item.draft_record
  const resourceCode = item.resource_code || draft?.resource_code || ""

  const [pipelineState, draftDoc] = await Promise.all([
    resourceCode ? getPipelineState(resourceCode).catch(() => null) : Promise.resolve(null),
    resourceCode ? getDraftAssessment(resourceCode).catch(() => null) : Promise.resolve(null),
  ])

  const checklistErrors = validatePublishChecklist(
    draft as unknown as Record<string, unknown>,
    "console"
  )

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3">
        <Link href="/review" className="flex items-center gap-1 text-sm text-[#6b7280] hover:text-[#0E3A27]">
          <ArrowLeft size={14} /> Review queue
        </Link>
        {item.routing && <Badge variant="outline" className="text-xs">{item.routing}</Badge>}
      </div>

      {/* Resource header */}
      <div className="bg-white rounded-xl border border-[#d4cfc5] px-5 py-4">
        <h1 className="font-serif text-2xl font-semibold text-[#0E3A27] leading-tight">
          {draft?.title ?? resourceCode}
        </h1>
        {draft?.url && (
          <a
            href={draft.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-[#03848F] hover:underline flex items-center gap-1 mt-1"
          >
            {draft.url.length > 80 ? draft.url.slice(0, 80) + "…" : draft.url}
            <ExternalLink size={12} />
          </a>
        )}
        <div className="flex flex-wrap gap-2 mt-2">
          {draft?.resource_type_code && (
            <Badge variant="outline">{TYPE_LABELS[draft.resource_type_code] ?? draft.resource_type_code}</Badge>
          )}
          {draft?.resource_subtype_code && (
            <Badge variant="secondary" className="text-xs">{draft.resource_subtype_code}</Badge>
          )}
          {draft?.difficulty_level && (
            <Badge variant="secondary" className="text-xs capitalize">{draft.difficulty_level}</Badge>
          )}
          {draft?.access_type && (
            <Badge variant="secondary" className="text-xs capitalize">{draft.access_type.replace(/_/g, " ")}</Badge>
          )}
          {draft?.language_detected && draft.language_detected !== "en" && (
            <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-800">
              {draft.language_detected.toUpperCase()}
            </Badge>
          )}
        </div>

        {item.reason && (
          <div className="mt-3 rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
            <span className="font-semibold">Routing reason: </span>{item.reason}
          </div>
        )}
        {item.requeue_reason && (
          <div className="mt-2 rounded-md bg-blue-50 border border-blue-200 px-3 py-2 text-xs text-blue-800">
            <span className="font-semibold">Send-back note: </span>{item.requeue_reason}
          </div>
        )}
        {item.qa_audit && (
          <div className="mt-2 rounded-md border px-3 py-2 text-xs"
            style={{
              backgroundColor: item.qa_audit.source_verdict === "fail" ? "#fef2f2"
                : item.qa_audit.source_verdict === "warn" ? "#fffbeb" : "#f0fdf4",
              borderColor: item.qa_audit.source_verdict === "fail" ? "#fecaca"
                : item.qa_audit.source_verdict === "warn" ? "#fde68a" : "#bbf7d0",
            }}>
            <div className="font-semibold text-[#0E3A27]">
              QA audit: source {item.qa_audit.source_verdict ?? "—"} · link {item.qa_audit.url_status ?? "—"}
              {item.qa_audit.type_match ? ` · type-match ${item.qa_audit.type_match}` : ""}
              {item.qa_audit.methodology_plausible ? ` · methodology ${item.qa_audit.methodology_plausible}` : ""}
            </div>
            {item.qa_audit.source_notes && <p className="mt-1 text-[#4a5568]">{item.qa_audit.source_notes}</p>}
            {(item.qa_audit.source_issues?.length ?? 0) > 0 && (
              <ul className="mt-1 list-disc list-inside text-[#6b7280]">
                {item.qa_audit.source_issues!.slice(0, 4).map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            )}
            {(item.qa_audit.hallucinations?.length ?? 0) > 0 && (
              <p className="mt-1 text-red-700"><span className="font-semibold">Possible hallucinations:</span> {item.qa_audit.hallucinations!.length}</p>
            )}
          </div>
        )}
      </div>

      {/* Interactive 3-pane workspace (client) */}
      <ReviewWorkspace
        itemId={id}
        draft={draft}
        panel={item.panel_result}
        pipelineState={pipelineState}
        draftDoc={draftDoc}
        checklistErrors={checklistErrors}
        approveAction={approveItem}
        rejectAction={rejectItem}
        requeueAction={requeueItem}
      />
    </div>
  )
}
