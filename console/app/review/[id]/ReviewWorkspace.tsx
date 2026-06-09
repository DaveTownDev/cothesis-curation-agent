"use client"

import { useCallback, useEffect, useMemo, useRef, useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { undoApprove, type ApproveResult } from "@/app/review/actions"
import { UndoApproveToast } from "@/components/UndoApproveToast"
import { UndoCountdown } from "@/components/UndoCountdown"
import { adjustSessionStat } from "@/lib/session-stats"
import { DescriptionSlots } from "@/components/DescriptionSlots"
import { PipelineInspector } from "@/components/PipelineInspector"
import { ReviewActions, type ReviewActionsHandle } from "@/components/ReviewActions"
import { StickyActionBar } from "@/components/StickyActionBar"
import { TaxonomyEditor } from "@/components/TaxonomyEditor"
import { ReviewSessionBar } from "@/components/ReviewSessionBar"
import { KeyboardHelp } from "@/components/KeyboardHelp"
import { CompendiumCardPreview } from "@/components/CompendiumCardPreview"
import { QaAuditBanner } from "@/components/QaAuditBanner"
import type { QaRecommendation } from "@/lib/qa-recommendations"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { validatePublishChecklist } from "@/lib/checklist"
import { isTypingTarget } from "@/lib/keyboard"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import type {
  DraftRecord, PanelResult, PipelineStateDoc, DraftDoc, QaAudit,
} from "@/lib/firestore"

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
}

interface Props {
  itemId: string
  draft: DraftRecord
  qaAudit?: QaAudit
  routingReason?: string
  panel: PanelResult | Record<string, unknown>
  pipelineState: PipelineStateDoc | null
  draftDoc: DraftDoc | null
  queuePosition: number
  queueTotal: number
  prevHref: string | null
  nextHref: string | null
  nextId: string | null
  queueQuery: string
  gcpProjectId: string
  approveAction: (
    itemId: string, badges: string[], editorialNote: string,
    reviewerName: string, edited: EditedDescriptions, taxonomy: TaxonomyEdits,
    nextId: string | null, queueQuery: string,
  ) => Promise<ApproveResult>
  rejectAction: (itemId: string, reason: string, nextId: string | null, queueQuery: string) => Promise<{ nextPath: string }>
  requeueAction: (
    itemId: string, reason: string, stage: string,
    nextId: string | null, queueQuery: string,
    draftPatch?: Record<string, unknown>,
  ) => Promise<{ nextPath: string }>
}

function initialTaxonomy(draft: DraftRecord): TaxonomyEdits {
  return {
    resource_type_code: draft.resource_type_code ?? "article",
    methodology_codes: [...(draft.methodology_codes ?? [])],
    discipline_codes: [...(draft.discipline_codes ?? [])],
    stage_codes: [...(draft.stage_codes ?? [])],
    difficulty_level: draft.difficulty_level ?? "intermediate",
    access_type: draft.access_type ?? "free",
  }
}

export function ReviewWorkspace({
  itemId, draft, qaAudit, routingReason, panel, pipelineState, draftDoc,
  queuePosition, queueTotal,
  prevHref, nextHref, nextId, queueQuery, gcpProjectId,
  approveAction, rejectAction, requeueAction,
}: Props) {
  const router = useRouter()
  const actionsRef = useRef<ReviewActionsHandle>(null)
  const [helpOpen, setHelpOpen] = useState(false)
  const [undoPending, setUndoPending] = useState<{
    undo: ApproveResult["undo"]
    nextPath: string
    sync?: ApproveResult["sync"]
  } | null>(null)
  const [isUndoing, startUndo] = useTransition()

  const undoPendingRef = useRef(undoPending)
  useEffect(() => {
    undoPendingRef.current = undoPending
  }, [undoPending])

  const finishNavigate = useCallback((nextPath: string) => {
    setUndoPending(null)
    router.push(nextPath)
  }, [router])

  const handleNavigate = useCallback((
    nextPath: string,
    undo?: ApproveResult["undo"],
    sync?: ApproveResult["sync"],
  ) => {
    if (undo) {
      setUndoPending({ undo, nextPath, sync })
    } else {
      router.push(nextPath)
    }
  }, [router])

  const onUndoExpire = useCallback(() => {
    const pending = undoPendingRef.current
    if (pending) finishNavigate(pending.nextPath)
  }, [finishNavigate])

  function handleUndo() {
    if (!undoPending) return
    const { undo, nextPath } = undoPending
    startUndo(async () => {
      try {
        await undoApprove(undo.itemId, undo.resourceCode)
        adjustSessionStat("approved", -1)
        finishNavigate(`/review/${undo.itemId}${queueQuery ? `?${queueQuery}` : ""}`)
      } catch {
        finishNavigate(nextPath)
      }
    })
  }

  const [shortDesc, setShortDesc] = useState(draft?.editorial_description ?? "")
  const [longDesc, setLongDesc] = useState(draft?.summary ?? "")
  const [plainDesc, setPlainDesc] = useState(draft?.editorial_description_plain ?? "")
  const [editorialNote, setEditorialNote] = useState(draft?.editorial_note ?? "")
  const [draftUrl, setDraftUrl] = useState(draft?.url ?? "")
  const [taxonomy, setTaxonomy] = useState<TaxonomyEdits>(() => initialTaxonomy(draft))

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

  const handleQaChangeType = useCallback((code: string) => {
    setTaxonomy((prev) => ({ ...prev, resource_type_code: code }))
  }, [])

  const handleQaFixUrlAndRequeue = useCallback((url: string, rec: QaRecommendation) => {
    setDraftUrl(url)
    const stage = rec.requeueStage ?? "classification"
    const note = rec.requeueNote ?? `QA audit: updated URL to ${url}`
    actionsRef.current?.quickRequeue(stage, note, { url })
  }, [])

  const handleQaRequeue = useCallback((rec: QaRecommendation) => {
    const stage = rec.requeueStage ?? "classification"
    const note = rec.requeueNote ?? "QA audit follow-up"
    actionsRef.current?.quickRequeue(stage, note)
  }, [])

  const handleQaReject = useCallback((reason: string) => {
    actionsRef.current?.quickReject(reason)
  }, [])

  const handleQaPrefillReject = useCallback((reason: string) => {
    actionsRef.current?.prefillReject(reason)
  }, [])

  const liveErrors = useMemo(
    () => validatePublishChecklist(liveRecord as unknown as Record<string, unknown>, "console"),
    [liveRecord],
  )

  const hasStrengths = (draft?.strengths?.length ?? 0) > 0 || (draft?.limitations?.length ?? 0) > 0
  const hasAltTitles = (draft?.alternative_titles?.length ?? 0) > 0
  const hasTypeFields = draft?.type_fields && Object.keys(draft.type_fields).length > 0

  const onKeyDown = useCallback((e: KeyboardEvent) => {
    if (isTypingTarget(e.target)) return
    if (e.key === "?") {
      e.preventDefault()
      setHelpOpen((o) => !o)
      return
    }
    if (e.key === "Escape") {
      actionsRef.current?.closeForms()
      setHelpOpen(false)
      return
    }
    if (e.key === "a" && !e.metaKey && !e.ctrlKey) {
      e.preventDefault()
      actionsRef.current?.approve()
      return
    }
    if (e.key === "r" && !e.metaKey && !e.ctrlKey) {
      e.preventDefault()
      actionsRef.current?.openReject()
      return
    }
    if (e.key === "b" && !e.metaKey && !e.ctrlKey) {
      e.preventDefault()
      actionsRef.current?.openRequeue()
      return
    }
    if ((e.key === "j" || e.key === "ArrowRight") && nextHref) {
      e.preventDefault()
      router.push(nextHref)
      return
    }
    if ((e.key === "k" || e.key === "ArrowLeft") && prevHref) {
      e.preventDefault()
      router.push(prevHref)
    }
  }, [nextHref, prevHref, router])

  useEffect(() => {
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [onKeyDown])

  return (
    <>
      {qaAudit && (
        <QaAuditBanner
          qaAudit={qaAudit}
          itemReason={routingReason}
          currentType={taxonomy.resource_type_code}
          currentUrl={draftUrl}
          onChangeType={handleQaChangeType}
          onFixUrlAndRequeue={handleQaFixUrlAndRequeue}
          onRequeue={handleQaRequeue}
          onReject={handleQaReject}
          onPrefillReject={handleQaPrefillReject}
        />
      )}

      <ReviewSessionBar
        position={queuePosition}
        total={queueTotal}
        prevHref={prevHref}
        nextHref={nextHref}
        onShowHelp={() => setHelpOpen(true)}
      />

      <KeyboardHelp open={helpOpen} onClose={() => setHelpOpen(false)} />

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px_300px] gap-4 items-start pb-20 xl:pb-0">
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
            badges={(draft.proposed_badges ?? []).slice(0, 3)}
            methodologyCodes={taxonomy.methodology_codes}
            qualityScore={draft.quality_score ?? 0}
            resourceType={taxonomy.resource_type_code}
          />

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Taxonomy</CardTitle>
            </CardHeader>
            <CardContent>
              <TaxonomyEditor value={taxonomy} onChange={setTaxonomy} />
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

        <PipelineInspector
          draft={{ ...draft, ...taxonomy }}
          panel={panel}
          pipelineState={pipelineState}
          draftDoc={draftDoc}
          gcpProjectId={gcpProjectId}
        />

        <Card className="xl:sticky xl:top-20 xl:self-start xl:max-h-[calc(100vh-6rem)] xl:overflow-y-auto">
          <CardHeader className="pb-2"><CardTitle className="text-sm">Decision</CardTitle></CardHeader>
          <CardContent>
            <ReviewActions
              ref={actionsRef}
              itemId={itemId}
              proposedBadges={draft?.proposed_badges ?? []}
              editorialNote={editorialNote}
              taxonomy={taxonomy}
              checklistErrors={liveErrors}
              qualityScore={draft?.quality_score ?? 0}
              aiConfidence={draft?.ai_confidence ?? 0}
              edited={edited}
              nextId={nextId}
              queueQuery={queueQuery}
              approveAction={approveAction}
              rejectAction={rejectAction}
              requeueAction={requeueAction}
              onNavigate={handleNavigate}
            />
          </CardContent>
        </Card>
      </div>

      <StickyActionBar
        canApprove={liveErrors.length === 0}
        isPending={false}
        onApprove={() => actionsRef.current?.approve()}
        onReject={() => actionsRef.current?.openReject()}
        onRequeue={() => actionsRef.current?.openRequeue()}
      />

      {undoPending && (
        <UndoCountdown
          key={undoPending.undo.itemId}
          seconds={8}
          onExpire={onUndoExpire}
        >
          {(secondsLeft) => (
            <UndoApproveToast
              visible
              resourceTitle={draft?.title ?? ""}
              secondsLeft={secondsLeft}
              onUndo={handleUndo}
              onDismiss={() => finishNavigate(undoPending.nextPath)}
              isUndoing={isUndoing}
              compendiumUrl={undoPending.sync?.compendium_url}
              syncError={undoPending.sync?.error}
            />
          )}
        </UndoCountdown>
      )}
    </>
  )
}
