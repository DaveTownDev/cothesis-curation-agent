import Link from "next/link"
import { AlertTriangle } from "lucide-react"

interface Props {
  reason?: string | null
}

/** Surfaces likely duplicate signals from arbiter routing or pipeline skip_reason. */
export function DuplicateHint({ reason }: Props) {
  if (!reason) return null
  const lower = reason.toLowerCase()
  if (!lower.includes("duplicate")) return null

  const match = reason.match(/duplicate of\s+([a-z0-9-]+)/i)
  const existingCode = match?.[1]

  return (
    <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900 flex items-start gap-2">
      <AlertTriangle size={14} className="shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold">Possible duplicate</p>
        <p className="mt-0.5 text-amber-800">{reason}</p>
        {existingCode && (
          <Link
            href={`/resources`}
            className="inline-block mt-1 text-[#03848F] hover:underline"
          >
            Check published list for {existingCode}
          </Link>
        )}
      </div>
    </div>
  )
}
