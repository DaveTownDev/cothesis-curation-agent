import { requireAuth } from "@/lib/auth"
import { getPublishedResources } from "@/lib/firestore"
import { PublishedResourcesTable } from "@/components/PublishedResourcesTable"
import { Badge } from "@/components/ui/badge"

export const metadata = { title: "Published — CoThesis" }

export const revalidate = 0

export default async function ResourcesPage() {
  await requireAuth()

  let resources: Awaited<ReturnType<typeof getPublishedResources>> = []
  let error: string | null = null
  try {
    resources = await getPublishedResources(200)
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load resources"
  }

  const synced = resources.filter((r) => r.compendium_synced_at).length

  const rows = resources.map((r) => ({
    resource_code: r.resource_code,
    title: r.title,
    url: r.url,
    resource_type_code: r.resource_type_code,
    quality_score: r.quality_score,
    editorial_reviewed_by: r.editorial_reviewed_by,
    editorial_reviewed_at: r.editorial_reviewed_at,
    compendium_synced_at: r.compendium_synced_at,
    compendium_sync_error: r.compendium_sync_error,
    compendium_url: r.compendium_url,
  }))

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        <div>
          <p className="hitl-eyebrow">Compendium sync</p>
          <h1 className="hitl-page-title">Published</h1>
        </div>
        <Badge variant="secondary">{resources.length} resources</Badge>
        <span className="text-xs text-[var(--text-body)]">
          {synced} synced to Compendium
        </span>
      </div>

      {error && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>
      )}

      {!error && resources.length === 0 && (
        <div className="rounded-xl border border-[#d4cfc5] bg-white p-12 text-center">
          <p className="text-[#6b7280]">No published resources yet.</p>
          <p className="text-sm text-[#6b7280] mt-1">Approve items in the review queue to publish them here.</p>
        </div>
      )}

      {rows.length > 0 && <PublishedResourcesTable resources={rows} />}
    </div>
  )
}
