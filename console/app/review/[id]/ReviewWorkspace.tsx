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
import { KeyboardHelp } from "@/components/KeyboardHelp"
import { CompendiumCardPreview } from "@/components/CompendiumCardPreview"
import { QaAuditStatus } from "@/components/QaAuditStatus"
import { mergeAppraisalFields } from "@/lib/review-draft"
import type { QaRecommendation } from "@/lib/qa-recommendations"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { validatePublishChecklist } from "@/lib/checklist"
import { isTypingTarget } from "@/lib/keyboard"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import type {
  DraftRecord, PanelResult, PipelineStateDoc, DraftDoc, QaAudit,
} from "@/lib/firestore"

interface Props {
  itemId: string
  draft: DraftRecord
  qaAudit?: QaAudit
  routingReason?: string
  panel: PanelResult | Record<string, unknown>
  pipelineState: PipelineStateDoc | null
  draftDoc: DraftDoc | null
  prevHref: string | null
  nextHref: string | null
  nextId: string | null
  queueQuery: string
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

export function ReviewWorkspace({
  itemId, draft, qaAudit, routingReason, panel, pipelineState, draftDoc,
  prevHref, nextHref, nextId, queueQuery, gcpProjectId,
}: Props) {
  const router = useRouter()
  const actionsRef = useRef<ReviewActionsHandle>(null)
  const [helpOpen, setHelpOpen] = useState(false)
  const [undoPending, setUndoPending] = useState<{
    undo: ApproveResult["undo"]
    nextPath: string
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
  ) => {
    if (undo) {
      setUndoPending({ undo, nextPath })
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

  const displayDraft = useMemo(
    () => mergeAppraisalFields(draft, draftDoc),
    [draft, draftDoc],
  )

  const edited = useMemo(() => ({
    editorial_description: shortDesc,
    summary: longDesc,
    editorial_description_plain: plainDesc,
    url: draftUrl,
  }), [shortDesc, longDesc, plainDesc, draftUrl])

  const liveRecord = useMemo(() => ({
    ...displayDraft,
    ...edited,
    ...taxonomy,
  }), [displayDraft, edited, taxonomy])

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

  const hasStrengths = (displayDraft?.strengths?.length ?? 0) > 0 || (displayDraft?.limitations?.length ?? 0) > 0
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

  useEffect(() => {
    const showHelp = () => setHelpOpen(true)
    window.addEventListener("cothesis-show-shortcuts", showHelp)
    return () => window.removeEventListener("cothesis-show-shortcuts", showHelp)
  }, [])

  return (
    <>
      <QaAuditStatus
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
            qualityScore={displayDraft.quality_score ?? 0}
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
                {displayDraft.strengths && displayDraft.strengths.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-[#289642] uppercase tracking-wide mb-1">Strengths</p>
                    <ul className="space-y-1">
                      {displayDraft.strengths.map((s, i) => (
                        <li key={i} className="text-sm text-[#0E3A27] flex items-start gap-2">
                          <span className="text-[#289642] mt-0.5">+</span>{s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {displayDraft.limitations && displayDraft.limitations.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-[#f59e0b] uppercase tracking-wide mb-1">Limitations</p>
                    <ul className="space-y-1">
                      {displayDraft.limitations.map((l, i) => (
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
          draft={{ ...displayDraft, ...taxonomy }}
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
              qualityScore={displayDraft?.quality_score ?? 0}
              aiConfidence={displayDraft?.ai_confidence ?? 0}
              edited={edited}
              nextId={nextId}
              queueQuery={queueQuery}
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
            />
          )}
        </UndoCountdown>
      )}
    </>
  )
}
