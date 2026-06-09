import type { Metadata } from "next"
import { notFound } from "next/navigation"
import Link from "next/link"
import { requireAuth } from "@/lib/auth"
import {
  getReviewQueueItem,
  getPipelineState, getDraftAssessment, getReviewQueue,
} from "@/lib/firestore"
import {
  parseReviewQueueFilters, queueQueryString, reviewDetailHref,
} from "@/lib/queue-filters"
import { approveItem, rejectItem, requeueItem } from "@/app/review/actions"
import { ReviewWorkspace } from "./ReviewWorkspace"
import { DuplicateHint } from "@/components/DuplicateHint"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, ExternalLink } from "lucide-react"

const TYPE_LABELS: Record<string, string> = {
  article: "Article", book: "Book", book_chapter: "Book chapter", video: "Video",
  podcast: "Podcast", software: "Software", reporting_guideline: "Guideline",
  course: "Course", web_guide: "Web guide", template: "Template",
  visual_reference: "Visual", dataset: "Dataset", community: "Community", funding: "Funding",
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
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<Record<string, string | undefined>>
}) {
  await requireAuth()
  const { id } = await params
  const sp = await searchParams

  const item = await getReviewQueueItem(id)
  if (!item) notFound()

  const draft = item.draft_record
  const resourceCode = item.resource_code || draft?.resource_code || ""
  const queueQuery = queueQueryString(sp)
  const filters = parseReviewQueueFilters(sp)
  const queueItems = await getReviewQueue(filters)
  const ids = queueItems.map((i) => i.id)
  const idx = ids.indexOf(id)
  const position = idx >= 0 ? idx + 1 : 1
  const total = ids.length || 1
  const prevId = idx > 0 ? ids[idx - 1] : null
  const nextId = idx >= 0 && idx < ids.length - 1 ? ids[idx + 1] : null
  const prevHref = prevId ? reviewDetailHref(prevId, sp) : null
  const nextHref = nextId ? reviewDetailHref(nextId, sp) : null

  const [pipelineState, draftDoc] = await Promise.all([
    resourceCode ? getPipelineState(resourceCode).catch(() => null) : Promise.resolve(null),
    resourceCode ? getDraftAssessment(resourceCode).catch(() => null) : Promise.resolve(null),
  ])

  const gcpProjectId = process.env.GOOGLE_CLOUD_PROJECT ?? "cothesis-curation-agent"

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link
          href={queueQuery ? `/review?${queueQuery}` : "/review"}
          className="flex items-center gap-1 text-sm text-[#6b7280] hover:text-[#0E3A27]"
        >
          <ArrowLeft size={14} /> Review queue
        </Link>
        {item.routing && <Badge variant="outline" className="text-xs">{item.routing}</Badge>}
      </div>

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
        </div>

        {item.reason && (
          <div className="mt-3 rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
            <span className="font-semibold">Routing reason: </span>{item.reason}
          </div>
        )}
        <DuplicateHint reason={item.reason} />
        <DuplicateHint reason={pipelineState?.skip_reason} />
      </div>

      <ReviewWorkspace
        itemId={id}
        draft={draft}
        qaAudit={item.qa_audit}
        routingReason={item.reason}
        panel={item.panel_result}
        pipelineState={pipelineState}
        draftDoc={draftDoc}
        queuePosition={position}
        queueTotal={total}
        prevHref={prevHref}
        nextHref={nextHref}
        nextId={nextId}
        queueQuery={queueQuery}
        gcpProjectId={gcpProjectId}
        approveAction={approveItem}
        rejectAction={rejectItem}
        requeueAction={requeueItem}
      />
    </div>
  )
}
