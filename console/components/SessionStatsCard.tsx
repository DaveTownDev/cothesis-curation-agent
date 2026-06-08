"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { readSessionStats, type SessionStats } from "@/lib/session-stats"

export function SessionStatsCard() {
  const [stats, setStats] = useState<SessionStats | null>(null)

  useEffect(() => {
    setStats(readSessionStats())
    const refresh = () => setStats(readSessionStats())
    window.addEventListener("cothesis-session-stats", refresh)
    return () => window.removeEventListener("cothesis-session-stats", refresh)
  }, [])

  if (!stats) return null

  const total = stats.approved + stats.rejected + stats.reopened
  if (total === 0) return null

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Your session today</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 text-center text-sm">
          <div>
            <p className="text-2xl font-bold text-[#289642]">{stats.approved}</p>
            <p className="text-xs text-[#6b7280]">approved</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-500">{stats.rejected}</p>
            <p className="text-xs text-[#6b7280]">rejected</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-[#03848F]">{stats.reopened}</p>
            <p className="text-xs text-[#6b7280]">reopened</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
