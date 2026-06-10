import Link from "next/link"
import { requireAuth } from "@/lib/auth"
import { getPipelineRuns } from "@/lib/firestore"
import { PipelineSubBar } from "@/components/PipelineSubBar"

export const metadata = { title: "Pipeline — CoThesis" }

export const revalidate = 0

const STAGE_COLOURS: Record<string, string> = {
  discovered: "#9ca3af", appraised: "#03848F", classified: "#0ea5e9",
  edited: "#8b5cf6", reconciled: "#6366f1", qc_panel: "#f59e0b",
  arbiter: "#ec4899", auto_accept: "#289642", review_needed: "#f59e0b",
  auto_exclude: "#dc2626", published: "#289642",
}

const ROUTING_COLOURS: Record<string, string> = {
  auto_accept: "#289642", review_needed: "#f59e0b", auto_exclude: "#dc2626",
}

function fmtDate(v?: string): string {
  if (!v) return "—"
  try {
    return new Date(v).toLocaleDateString("en-AU", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
    })
  } catch {
    return "—"
  }
}

export default async function PipelinePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string>>
}) {
  await requireAuth()
  const sp = await searchParams

  let runs: Awaited<ReturnType<typeof getPipelineRuns>> = []
  let error: string | null = null
  try {
    runs = await getPipelineRuns({ stage: sp.stage || undefined, limit: 200 })
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

      {runs.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[#d4cfc5] bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[#d4cfc5] bg-[#F8F5EE]">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Resource code</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Stage</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Routing</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Composite</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Run ID</th>
                <th className="px-4 py-3 text-left font-medium text-[#6b7280]">Updated</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8e4dc]">
              {runs.map((run) => {
                const stage = run.current_stage ?? run.state ?? "unknown"
                const routing = run.arbiter_decision?.routing
                return (
                  <tr key={run.id} className="hover:bg-[#F8F5EE] transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-[#0E3A27] max-w-[200px] truncate">
                      {run.resource_code}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs font-medium rounded px-2 py-0.5"
                        style={{ backgroundColor: `${STAGE_COLOURS[stage] ?? "#9ca3af"}20`, color: STAGE_COLOURS[stage] ?? "#6b7280" }}
                      >
                        {stage}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {routing ? (
                        <span className="text-xs font-medium capitalize" style={{ color: ROUTING_COLOURS[routing] ?? "#6b7280" }}>
                          {routing.replace(/_/g, " ")}
                        </span>
                      ) : <span className="text-[#9ca3af] text-xs">—</span>}
                    </td>
                    <td className="px-4 py-3 text-xs text-[#4a6741]">
                      {run.arbiter_decision?.composite_score?.toFixed(1) ?? "—"}
                    </td>
                    <td className="px-4 py-3 font-mono text-[10px] text-[#9ca3af] max-w-[140px] truncate">
                      {run.pipeline_run_id ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-[#6b7280] whitespace-nowrap">{fmtDate(run.updated_at)}</td>
                    <td className="px-4 py-3">
                      {routing === "review_needed" && (
                        <Link
                          href="/review"
                          className="text-xs text-[#289642] font-medium hover:underline whitespace-nowrap"
                        >
                          View queue
                        </Link>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
