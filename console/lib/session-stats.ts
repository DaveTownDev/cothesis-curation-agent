/** Browser-local curator session counters (resets daily). */

export interface SessionStats {
  date: string
  approved: number
  rejected: number
  reopened: number
}

const KEY = "cothesis_session_stats"

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export function readSessionStats(): SessionStats {
  if (typeof window === "undefined") {
    return { date: today(), approved: 0, rejected: 0, reopened: 0 }
  }
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { date: today(), approved: 0, rejected: 0, reopened: 0 }
    const parsed = JSON.parse(raw) as SessionStats
    if (parsed.date !== today()) {
      return { date: today(), approved: 0, rejected: 0, reopened: 0 }
    }
    return parsed
  } catch {
    return { date: today(), approved: 0, rejected: 0, reopened: 0 }
  }
}

export function adjustSessionStat(
  field: keyof Omit<SessionStats, "date">,
  delta: number,
): SessionStats {
  const stats = readSessionStats()
  stats[field] = Math.max(0, stats[field] + delta)
  localStorage.setItem(KEY, JSON.stringify(stats))
  window.dispatchEvent(new CustomEvent("cothesis-session-stats"))
  return stats
}

export function recordSessionStat(field: keyof Omit<SessionStats, "date">, delta = 1): SessionStats {
  return adjustSessionStat(field, delta)
}
