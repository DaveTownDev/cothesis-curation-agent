import Link from "next/link"
import { AlertCircle, CheckCircle, Clock, ExternalLink } from "lucide-react"

interface Props {
  syncedAt?: string | null
  syncError?: string | null
  compendiumUrl?: string | null
  compact?: boolean
}

export function CompendiumSyncBadge({
  syncedAt, syncError, compendiumUrl, compact = false,
}: Props) {
  if (syncError) {
    return (
      <span className="flex items-center gap-1 text-xs text-red-600" title={syncError}>
        <AlertCircle size={12} />
        {compact ? "Error" : "Sync error"}
      </span>
    )
  }

  if (compendiumUrl) {
    return (
      <Link
        href={compendiumUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-1 text-xs text-[#03848F] hover:underline"
        onClick={(e) => e.stopPropagation()}
      >
        <CheckCircle size={12} />
        View in Compendium
        <ExternalLink size={10} />
      </Link>
    )
  }

  if (syncedAt) {
    return (
      <span className="flex items-center gap-1 text-xs text-[#f59e0b]" title="Synced without Compendium URL — retry sync">
        <Clock size={12} />
        {compact ? "Re-sync" : "Synced — retry for URL"}
      </span>
    )
  }

  return (
    <span className="flex items-center gap-1 text-xs text-[#f59e0b]">
      <Clock size={12} />
      Pending sync
    </span>
  )
}
