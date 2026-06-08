"use client"

import { useState } from "react"
import { DescriptionSlots } from "@/components/DescriptionSlots"
import { PipelineInspector } from "@/components/PipelineInspector"
import { ReviewActions } from "@/components/ReviewActions"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { ChecklistError } from "@/lib/checklist"
import type {
  DraftRecord, PanelResult, PipelineStateDoc, DraftDoc,
} from "@/lib/firestore"

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
}

interface Props {
  itemId: string
  draft: DraftRecord
  panel: PanelResult | Record<string, unknown>
  pipelineState: PipelineStateDoc | null
  draftDoc: DraftDoc | null
  checklistErrors: ChecklistError[]
  approveAction: (
    itemId: string, badges: string[], editorialNote: string,
    reviewerName: string, edited: EditedDescriptions
  ) => Promise<void>
  rejectAction: (itemId: string, reason: string) => Promise<void>
  requeueAction: (itemId: string, reason: string) => Promise<void>
}

export function ReviewWorkspace({
  itemId, draft, panel, pipelineState, draftDoc,
  checklistErrors, approveAction, rejectAction, requeueAction,
}: Props) {
  // Shared editable state — edits flow from DescriptionSlots into the approve action
  const [shortDesc, setShortDesc] = useState(draft?.editorial_description ?? "")
  const [longDesc, setLongDesc] = useState(draft?.summary ?? "")
  const [plainDesc, setPlainDesc] = useState(draft?.editorial_description_plain ?? "")
  const [editorialNote, setEditorialNote] = useState(draft?.editorial_note ?? "")

  const edited: EditedDescriptions = {
    editorial_description: shortDesc,
    summary: longDesc,
    editorial_description_plain: plainDesc,
  }

  // Recompute checklist client-side as the curator edits (short desc is the main gated field)
  const liveErrors = checklistErrors.filter((e) => {
    if (e.field === "editorial_description") return shortDesc.trim().length === 0
    return true
  })

  const hasStrengths = (draft?.strengths?.length ?? 0) > 0 || (draft?.limitations?.length ?? 0) > 0
  const hasAltTitles = (draft?.alternative_titles?.length ?? 0) > 0
  const hasTypeFields = draft?.type_fields && Object.keys(draft.type_fields).length > 0

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px_300px] gap-4 items-start">
      {/* LEFT — descriptions + extra cards */}
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

        {hasStrengths && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Strengths & limitations</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {draft.strengths && draft.strengths.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-[#289642] uppercase tracking-wide mb-1">Strengths</p>
                  <ul className="space-y-1">
                    {draft.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-[#0E3A27] flex items-start gap-2">
                        <span className="text-[#289642] mt-0.5">+</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {draft.limitations && draft.limitations.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-[#f59e0b] uppercase tracking-wide mb-1">Limitations</p>
                  <ul className="space-y-1">
                    {draft.limitations.map((l, i) => (
                      <li key={i} className="text-sm text-[#0E3A27] flex items-start gap-2">
                        <span className="text-[#f59e0b] mt-0.5">−</span>{l}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {hasAltTitles && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Alternative titles (search surface)</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {draft.alternative_titles!.map((t, i) => (
                  <span key={i} className="text-xs bg-[#e8e4dc] text-[#4a6741] rounded px-2 py-0.5">{t}</span>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {hasTypeFields && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Type-specific metadata</CardTitle></CardHeader>
            <CardContent>
              <dl className="space-y-1">
                {Object.entries(draft.type_fields!).map(([k, v]) => (
                  <div key={k} className="flex gap-2 text-xs">
                    <dt className="font-medium text-[#4a6741] w-32 shrink-0">{k}</dt>
                    <dd className="text-[#0E3A27]">{String(v)}</dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>
        )}
      </div>

      {/* CENTER — pipeline inspector */}
      <PipelineInspector draft={draft} panel={panel} pipelineState={pipelineState} draftDoc={draftDoc} />

      {/* RIGHT — decision */}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Decision</CardTitle></CardHeader>
        <CardContent>
          <ReviewActions
            itemId={itemId}
            proposedBadges={draft?.proposed_badges ?? []}
            editorialNote={editorialNote}
            checklistErrors={liveErrors}
            qualityScore={draft?.quality_score ?? 0}
            aiConfidence={draft?.ai_confidence ?? 0}
            edited={edited}
            approveAction={approveAction}
            rejectAction={rejectAction}
            requeueAction={requeueAction}
          />
        </CardContent>
      </Card>
    </div>
  )
}
