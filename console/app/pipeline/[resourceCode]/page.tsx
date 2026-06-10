import type { Metadata } from "next"
import { notFound } from "next/navigation"
import Link from "next/link"
import { requireAuth } from "@/lib/auth"
import {
  getEditableResource,
  getPipelineState,
  getDraftAssessment,
  getReviewQueueItem,
} from "@/lib/firestore"
import { ResourceEditorWorkspace } from "@/components/ResourceEditorWorkspace"
import { PipelineRecordSubBar } from "@/components/PipelineRecordSubBar"
import { Badge } from "@/components/ui/badge"
import { ExternalLink } from "lucide-react"

export const revalidate = 0

const TYPE_LABELS: Record<string, string> = {
  article: "Article", book: "Book", book_chapter: "Book chapter", video: "Video",
  podcast: "Podcast", software: "Software", reporting_guideline: "Guideline",
  course: "Course", web_guide: "Web guide", template: "Template",
  visual_reference: "Visual", dataset: "Dataset", community: "Community", funding: "Funding",
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ resourceCode: string }>
}): Promise<Metadata> {
  const { resourceCode } = await params
  const editable = await getEditableResource(decodeURIComponent(resourceCode))
  const title = editable?.draft?.title ?? resourceCode
  return { title: `${title} — CoThesis` }
}

export default async function PipelineRecordPage({
  params,
}: {
  params: Promise<{ resourceCode: string }>
}) {
  await requireAuth()
  const { resourceCode: rawCode } = await params
  const resourceCode = decodeURIComponent(rawCode)

  const editable = await getEditableResource(resourceCode)
  if (!editable) notFound()

  const draft = editable.draft
  const [pipelineState, draftDoc] = await Promise.all([
    getPipelineState(resourceCode).catch(() => null),
    getDraftAssessment(resourceCode).catch(() => null),
  ])

  let panel: Record<string, unknown> = {}
  if (editable.queue_item_id) {
    const item = await getReviewQueueItem(editable.queue_item_id)
    panel = (item?.panel_result ?? {}) as Record<string, unknown>
  }

  const gcpProjectId = process.env.GOOGLE_CLOUD_PROJECT ?? "cothesis-curation-agent"
  const routing = pipelineState?.arbiter_decision?.routing

  return (
    <div className="space-y-4">
      <PipelineRecordSubBar
        resourceCode={resourceCode}
        source={editable.source}
        routing={routing}
      />

      <div className="hitl-card px-4 py-3">
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
            {draft.url.length > 80 ? `${draft.url.slice(0, 80)}…` : draft.url}
            <ExternalLink size={12} />
          </a>
        )}
        <div className="flex flex-wrap gap-2 mt-2">
          {draft?.resource_type_code && (
            <Badge variant="outline">{TYPE_LABELS[draft.resource_type_code] ?? draft.resource_type_code}</Badge>
          )}
          {editable.source === "queue" && editable.queue_item_id && (
            <Link href={`/review/${editable.queue_item_id}`} className="text-xs text-[var(--green-primary)] hover:underline">
              Open in review queue →
            </Link>
          )}
        </div>
      </div>

      <ResourceEditorWorkspace
        resourceCode={resourceCode}
        draft={draft}
        source={editable.source}
        panel={panel}
        pipelineState={pipelineState}
        draftDoc={draftDoc}
        queueItemId={editable.queue_item_id}
        gcpProjectId={gcpProjectId}
      />
    </div>
  )
}
