import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Props {
  stats: Record<string, number>
}

const STATE_LABELS: Record<string, string> = {
  discovered: "Discovered",
  appraised: "Appraised",
  classified: "Classified",
  edited: "Edited",
  reconciled: "Reconciled",
  qc_panel: "QC Panel",
  arbiter: "Arbiter",
  auto_accept: "Auto-accepted",
  review_needed: "Sent to review",
  auto_exclude: "Auto-excluded",
  published: "Published",
  pending_review: "Pending human review",
}

const STATE_COLOURS: Record<string, string> = {
  published: "#289642",
  pending_review: "#f59e0b",
  auto_exclude: "#dc2626",
  auto_accept: "#03848F",
}

export function PipelineStatsCard({ stats }: Props) {
  const entries = Object.entries(stats).filter(([, v]) => v > 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline state</CardTitle>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-[#6b7280]">No pipeline data yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {entries.map(([state, count]) => (
              <div
                key={state}
                className="rounded-md border border-[#d4cfc5] px-3 py-2 text-center"
              >
                <p
                  className="text-2xl font-bold"
                  style={{ color: STATE_COLOURS[state] || "#0E3A27" }}
                >
                  {count}
                </p>
                <p className="text-xs text-[#6b7280] mt-0.5">
                  {STATE_LABELS[state] ?? state.replace(/_/g, " ")}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
