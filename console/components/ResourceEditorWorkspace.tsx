"use client"

import { useMemo, useState } from "react"
import { DescriptionSlots } from "@/components/DescriptionSlots"
import { PipelineInspector } from "@/components/PipelineInspector"
import { TaxonomyEditor } from "@/components/TaxonomyEditor"
import { CompendiumCardPreview } from "@/components/CompendiumCardPreview"
import { ResourceEditorActions } from "@/components/ResourceEditorActions"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { validatePublishChecklist } from "@/lib/checklist"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import type {
  DraftRecord, PanelResult, PipelineStateDoc, DraftDoc, EditableResourceSource,
} from "@/lib/firestore"

interface Props {
  resourceCode: string
  draft: DraftRecord
  source: EditableResourceSource
  panel: PanelResult | Record<string, unknown>
  pipelineState: PipelineStateDoc | null
  draftDoc: DraftDoc | null
  queueItemId?: string
  gcpProjectId: string
}

function initialTaxonomy(draft: DraftRecord): TaxonomyEdits {
  return {
    resource_type_code: draft.resource_type_code ?? "article",
    resource_subtype_code: draft.resource_subtype_code ?? null,
    methodology_codes: [...(draft.methodology_codes ?? [])],
    skill_codes: [...(draft.skill_codes ?? [])],
    discipline_codes: [...(draft.discipline_codes ?? [])],
    domain_codes: [...(draft.domain_codes ?? [])],
    stage_codes: [...(draft.stage_codes ?? [])],
    difficulty_level: draft.difficulty_level ?? "intermediate",
    access_type: draft.access_type ?? "free",
  }
}

export function ResourceEditorWorkspace({
  resourceCode, draft, source, panel, pipelineState, draftDoc, queueItemId, gcpProjectId,
}: Props) {
  const [shortDesc, setShortDesc] = useState(draft?.editorial_description ?? "")
  const [longDesc, setLongDesc] = useState(draft?.summary ?? "")
  const [plainDesc, setPlainDesc] = useState(draft?.editorial_description_plain ?? "")
  const [editorialNote, setEditorialNote] = useState(draft?.editorial_note ?? "")
  const [draftUrl] = useState(draft?.url ?? "")
  const [taxonomy, setTaxonomy] = useState<TaxonomyEdits>(() => initialTaxonomy(draft))
  const [reviewerName, setReviewerName] = useState<string>(() => {
    if (typeof window !== "undefined") return localStorage.getItem("cothesis_reviewer") ?? ""
    return ""
  })

  const edited = useMemo(() => ({
    editorial_description: shortDesc,
    summary: longDesc,
    editorial_description_plain: plainDesc,
    url: draftUrl,
  }), [shortDesc, longDesc, plainDesc, draftUrl])

  const liveRecord = useMemo(() => ({
    ...draft,
    ...edited,
    ...taxonomy,
  }), [draft, edited, taxonomy])

  const liveErrors = useMemo(
    () => validatePublishChecklist(liveRecord as unknown as Record<string, unknown>, reviewerName || "console"),
    [liveRecord, reviewerName],
  )

  const badges = (draft as DraftRecord & { editorial_badges?: string[] })?.editorial_badges
    ?? draft?.proposed_badges ?? []

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px_300px] gap-4 items-start">
      <div className="space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Descriptions — click any field to edit</CardTitle>
          </CardHeader>
          <CardContent>
            <DescriptionSlots
              record={{ ...draft, editorial_description: shortDesc, summary: longDesc, editorial_description_plain: plainDesc }}
              editorialNote={editorialNote}
              onEditShort={setShortDesc}
              onEditLong={setLongDesc}
              onEditPlain={setPlainDesc}
              onEditNote={setEditorialNote}
            />
          </CardContent>
        </Card>

        <CompendiumCardPreview
          title={draft.title ?? ""}
          shortDescription={shortDesc}
          plainDescription={plainDesc}
          summary={longDesc}
          badges={badges.slice(0, 3)}
          methodologyCodes={taxonomy.methodology_codes}
          qualityScore={draft.quality_score ?? 0}
          resourceType={taxonomy.resource_type_code}
        />

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Taxonomy</CardTitle></CardHeader>
          <CardContent>
            <TaxonomyEditor value={taxonomy} onChange={setTaxonomy} />
          </CardContent>
        </Card>
      </div>

      <PipelineInspector
        draft={liveRecord}
        pipelineState={pipelineState}
        draftDoc={draftDoc}
        panel={panel}
        gcpProjectId={gcpProjectId}
      />

      <Card className="xl:sticky xl:top-20 xl:self-start">
        <CardHeader className="pb-2"><CardTitle className="text-sm">Catalog actions</CardTitle></CardHeader>
        <CardContent>
          <ResourceEditorActions
            resourceCode={resourceCode}
            source={source}
            proposedBadges={badges}
            editorialNote={editorialNote}
            taxonomy={taxonomy}
            checklistErrors={liveErrors}
            edited={edited}
            queueItemId={queueItemId}
            reviewerName={reviewerName}
            onReviewerNameChange={(name) => {
              setReviewerName(name)
              if (typeof window !== "undefined") localStorage.setItem("cothesis_reviewer", name)
            }}
          />
        </CardContent>
      </Card>
    </div>
  )
}
