import { requireAuth } from "@/lib/auth"
import { getPipelineRuns, getResourceLiveStatusMap } from "@/lib/firestore"
import { PipelineSubBar } from "@/components/PipelineSubBar"
import { PipelineRunsTable, type PipelineRunRow } from "@/components/PipelineRunsTable"

export const metadata = { title: "Pipeline — CoThesis" }

export const revalidate = 0

export default async function PipelinePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string>>
}) {
  await requireAuth()
  const sp = await searchParams

  let runs: PipelineRunRow[] = []
  let error: string | null = null
  try {
    const pipelineRuns = await getPipelineRuns({ stage: sp.stage || undefined, limit: 200 })
    const statusMap = await getResourceLiveStatusMap(pipelineRuns.map((r) => r.resource_code))
    runs = pipelineRuns.map((run) => {
      const stage = run.current_stage ?? run.state ?? "unknown"
      return {
        id: run.id,
        resource_code: run.resource_code,
        stage,
        routing: run.arbiter_decision?.routing,
        composite: run.arbiter_decision?.composite_score,
        pipeline_run_id: run.pipeline_run_id,
        updated_at: run.updated_at,
        live: statusMap[run.resource_code],
      }
    })
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load pipeline runs"
  }

  return (
    <div className="space-y-5">
      <PipelineSubBar count={runs.length} />
      <h1 className="hitl-page-title">Pipeline runs</h1>

      {error && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>
      )}

      {!error && runs.length === 0 && (
        <div className="rounded-xl border border-[#d4cfc5] bg-white p-12 text-center">
          <p className="text-[#6b7280]">No pipeline runs recorded yet.</p>
          <p className="text-sm text-[#6b7280] mt-1">
            Each resource the pipeline processes writes a state record here, regardless of routing outcome.
          </p>
        </div>
      )}

      {runs.length > 0 && <PipelineRunsTable runs={runs} />}
    </div>
  )
}
