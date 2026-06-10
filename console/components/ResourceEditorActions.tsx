"use client"

import { useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { BadgeList } from "@/components/BadgeList"
import type { ChecklistError } from "@/lib/checklist"
import type { TaxonomyEdits } from "@/lib/taxonomy"
import type { EditableResourceSource } from "@/lib/firestore"
import {
  publishResource,
  republishResource,
  saveResourceEdits,
  unpublishResource,
  pushResourceToCompendium,
} from "@/app/resources/actions"
import { CheckCircle, EyeOff, Save, Upload, RotateCcw } from "lucide-react"

interface EditedDescriptions {
  editorial_description: string
  summary: string
  editorial_description_plain: string
  url: string
}

interface Props {
  resourceCode: string
  source: EditableResourceSource
  proposedBadges: string[]
  editorialNote: string
  taxonomy: TaxonomyEdits
  checklistErrors: ChecklistError[]
  edited: EditedDescriptions
  queueItemId?: string
  reviewerName: string
  onReviewerNameChange: (name: string) => void
}

export function ResourceEditorActions({
  resourceCode,
  source,
  proposedBadges,
  editorialNote,
  taxonomy,
  checklistErrors,
  edited,
  queueItemId,
  reviewerName,
  onReviewerNameChange,
}: Props) {
  const router = useRouter()
  const [pending, startTransition] = useTransition()
  const [ratifiedBadges, setRatifiedBadges] = useState<string[]>(proposedBadges.slice(0, 3))
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const canPublish = checklistErrors.length === 0
  const isPublished = source === "published"
  const isArchived = source === "archived"

  function run(action: () => Promise<void>) {
    setError(null)
    setMessage(null)
    startTransition(async () => {
      try {
        await action()
        router.refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Action failed")
      }
    })
  }

  function handleSave() {
    run(async () => {
      await saveResourceEdits(
        resourceCode, edited, taxonomy, editorialNote, ratifiedBadges, reviewerName, queueItemId,
      )
      setMessage("Draft saved")
    })
  }

  function handlePublish() {
    run(async () => {
      const result = await publishResource(
        resourceCode, edited, taxonomy, editorialNote, ratifiedBadges, reviewerName, queueItemId,
      )
      if (!result.ok) throw new Error(result.error ?? "Publish sync failed")
      setMessage(result.compendium_url ? "Published and synced to Compendium" : "Published (sync pending URL)")
    })
  }

  function handleUnpublish() {
    run(async () => {
      const result = await unpublishResource(resourceCode)
      if (result.compendiumWarning) {
        setMessage(`Unpublished locally. Compendium: ${result.compendiumWarning}`)
      } else {
        setMessage("Unpublished — hidden from live site")
      }
    })
  }

  function handleRepublish() {
    run(async () => {
      const result = await republishResource(resourceCode)
      if (!result.ok) throw new Error(result.error ?? "Republish sync failed")
      setMessage(result.compendium_url ? "Live again on Compendium" : "Republished (sync pending URL)")
    })
  }

  function handlePush() {
    run(async () => {
      const result = await pushResourceToCompendium(resourceCode)
      if (!result.ok) throw new Error(result.error ?? "Sync failed")
      setMessage(result.compendium_url ? "Pushed to Compendium" : "Sync accepted (awaiting URL)")
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-[var(--text-body)]">
        <span>Editing as:</span>
        <input
          className="h-7 px-2 text-xs rounded border border-[var(--border-primary)] flex-1 min-w-0"
          value={reviewerName}
          onChange={(e) => onReviewerNameChange(e.target.value)}
          placeholder="Your name"
        />
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>
      )}
      {message && (
        <div className="rounded-md border border-[var(--green-primary)] bg-[#f0faf2] px-3 py-2 text-xs text-[var(--text-primary)]">
          {message}
        </div>
      )}

      {checklistErrors.length > 0 && (
        <ul className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2 space-y-1">
          {checklistErrors.map((e) => <li key={e.field}>{e.message}</li>)}
        </ul>
      )}

      <div>
        <p className="text-xs font-medium text-[var(--text-body)] mb-2">Editorial badges (max 3)</p>
        <BadgeList proposed={ratifiedBadges} onChange={setRatifiedBadges} />
      </div>

      <div className="flex flex-col gap-2">
        <Button size="sm" variant="secondary" disabled={pending} onClick={handleSave}>
          <Save size={14} /> Save draft
        </Button>

        {!isPublished && !isArchived && (
          <Button size="sm" disabled={!canPublish || pending} onClick={handlePublish}>
            <CheckCircle size={14} /> Publish & sync
          </Button>
        )}

        {isPublished && (
          <>
            <Button size="sm" variant="outline" disabled={pending} onClick={handlePush}>
              <Upload size={14} /> Push changes to live site
            </Button>
            <Button size="sm" variant="outline" disabled={pending} onClick={handleUnpublish} className="text-red-600 border-red-200">
              <EyeOff size={14} /> Unpublish (hide on site)
            </Button>
          </>
        )}

        {isArchived && (
          <Button size="sm" disabled={!canPublish || pending} onClick={handleRepublish}>
            <RotateCcw size={14} /> Republish to live site
          </Button>
        )}
      </div>

      <p className="text-[10px] text-[var(--text-body)] leading-relaxed">
        Unpublish hides the record on the live Compendium when the visibility API is available.
        Records are never deleted — users may have bookmarked them.
      </p>
    </div>
  )
}
