import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, Clock, AlertCircle } from "lucide-react"

interface Props {
  synced: number
  pending: number
  total: number
  oldest_age_label: string | null
  queue_stale: boolean
}

export function SyncStatusCard({
  synced, pending, total,
  oldest_age_label, queue_stale,
}: Props) {
  const pct = total > 0 ? Math.round((synced / total) * 100) : 0
  const oldestAge = oldest_age_label ?? null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-[#4a6741]">Compendium sync</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-[#289642]" />
            <span className="text-2xl font-bold text-[#0E3A27]">{synced}</span>
            <span className="text-sm text-[#6b7c68]">/ {total} synced</span>
          </div>
          {pending > 0 && (
            <p className="text-xs text-[#f59e0b] mt-1 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {pending} pending sync
            </p>
          )}
          <div className="mt-2 h-1.5 bg-[#e8e4dc] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#289642] rounded-full transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-[#4a6741]">Oldest queued item</CardTitle>
        </CardHeader>
        <CardContent>
          {oldestAge ? (
            <div className="flex items-center gap-2">
              {queue_stale ? (
                <AlertCircle className="h-4 w-4 text-red-500" />
              ) : (
                <Clock className="h-4 w-4 text-[#03848F]" />
              )}
              <span className={`text-2xl font-bold ${queue_stale ? "text-red-600" : "text-[#0E3A27]"}`}>
                {oldestAge}
              </span>
            </div>
          ) : (
            <p className="text-sm text-[#6b7c68]">Queue empty</p>
          )}
          {queue_stale && (
            <p className="text-xs text-red-500 mt-1">Items waiting &gt;24h</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-[#4a6741]">Sync coverage</CardTitle>
        </CardHeader>
        <CardContent>
          <span className="text-2xl font-bold text-[#0E3A27]">{pct}%</span>
          <p className="text-xs text-[#6b7c68] mt-1">of published resources in Compendium</p>
        </CardContent>
      </Card>
    </div>
  )
}
