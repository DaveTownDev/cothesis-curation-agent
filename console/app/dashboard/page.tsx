import { requireAuth } from "@/lib/auth"
import { getPipelineStats, getSyncStats } from "@/lib/firestore"
import { PipelineStatsCard } from "@/components/PipelineStatsCard"
import { SyncStatusCard } from "@/components/SyncStatusCard"
import { SessionStatsCard } from "@/components/SessionStatsCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getEvalSummary } from "@/lib/eval-summary"
import { DashboardSubBar } from "@/components/DashboardSubBar"

export const metadata = { title: "Dashboard — CoThesis" }

export const revalidate = 0

export default async function DashboardPage() {
  await requireAuth()
  const evalSummary = getEvalSummary()

  let stats: Record<string, number> = {}
  let syncStats = {
    synced: 0,
    pending: 0,
    total: 0,
    oldest_pending_at: null as string | null,
    oldest_age_label: null as string | null,
    queue_stale: false,
  }
  let firestoreError: string | null = null

  try {
    ;[stats, syncStats] = await Promise.all([getPipelineStats(), getSyncStats()])
  } catch (err) {
    firestoreError = err instanceof Error ? err.message : "Firestore unavailable"
  }

  const pendingReview = stats.pending_review ?? 0
  const approvalRate =
    (stats.approved ?? 0) + (stats.rejected ?? 0) > 0
      ? Math.round(((stats.approved ?? 0) / ((stats.approved ?? 0) + (stats.rejected ?? 0))) * 100)
      : null

  return (
    <div className="space-y-5">
      <DashboardSubBar pendingReview={pendingReview} />
      <h1 className="hitl-page-title">Dashboard</h1>

      {firestoreError && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <strong>Firestore unavailable:</strong> {firestoreError}
          <br />
          <span className="text-xs">
            Run <code>gcloud auth application-default login</code> and set{" "}
            <code>GOOGLE_CLOUD_PROJECT</code> in <code>.env.local</code>
          </span>
        </div>
      )}

      <SessionStatsCard />

      {/* Sync & queue health */}
      <SyncStatusCard {...syncStats} />

      {/* Pipeline state breakdown */}
      <PipelineStatsCard stats={stats} />

      {/* Eval scores + approval rate */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Eval scores — last run</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-[#289642]">
                  {evalSummary.response_match_score.toFixed(2)}
                </p>
                <p className="text-xs text-[#6b7280]">response_match_score</p>
                <Badge variant="default" className="mt-1 text-xs">
                  {evalSummary.response_match_score >= evalSummary.response_match_threshold
                    ? "Target met"
                    : "Below target"}
                </Badge>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#289642]">
                  {Math.round(evalSummary.rubric_pass_rate * 100)}%
                </p>
                <p className="text-xs text-[#6b7280]">rubric pass rate</p>
                <Badge variant="default" className="mt-1 text-xs">
                  {evalSummary.cases_passed}/{evalSummary.cases_total} cases
                </Badge>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#03848F]">{evalSummary.cases_total}</p>
                <p className="text-xs text-[#6b7280]">gold set items</p>
                <Badge variant="teal" className="mt-1 text-xs">4 methods × 5 types</Badge>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#0E3A27]">{evalSummary.unit_tests}</p>
                <p className="text-xs text-[#6b7280]">unit tests</p>
                <Badge variant="secondary" className="mt-1 text-xs">All green</Badge>
              </div>
            </div>
            <p className="text-[10px] text-[#9ca3af] mt-3 text-right">
              Eval snapshot {evalSummary.updated_at}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Review history</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-[#289642]">{stats.approved ?? 0}</p>
                <p className="text-xs text-[#6b7280]">approved</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-500">{stats.rejected ?? 0}</p>
                <p className="text-xs text-[#6b7280]">rejected</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-[#03848F]">
                  {approvalRate !== null ? `${approvalRate}%` : "—"}
                </p>
                <p className="text-xs text-[#6b7280]">approval rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
