"use client"

const BADGE_LABELS: Record<string, string> = {
  editors_choice: "Editor's Choice",
  best_free: "Best Free",
  best_beginners: "Best for Beginners",
  best_time_poor: "Best for Time-Poor",
  essential: "Essential",
  expert_pick: "Expert Pick",
}

interface Props {
  title: string
  shortDescription: string
  plainDescription: string
  summary: string
  badges: string[]
  methodologyCodes: string[]
  qualityScore: number
  resourceType: string
}

export function CompendiumCardPreview({
  title, shortDescription, plainDescription, summary, badges,
  methodologyCodes, qualityScore, resourceType,
}: Props) {
  const showQuality = qualityScore >= 60

  return (
    <div className="rounded-xl border-2 border-dashed border-[#d4cfc5] bg-[#FDFCF8] p-4 space-y-3">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-[#9ca3af]">
        Compendium card preview
      </p>

      <div className="rounded-lg border border-[#e8e4dc] bg-white p-4 shadow-sm space-y-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-serif text-lg font-semibold text-[#0E3A27] leading-snug">
            {title || "Untitled resource"}
          </h3>
          {showQuality && (
            <span
              className="text-xs font-bold shrink-0 rounded px-1.5 py-0.5"
              style={{
                color: qualityScore >= 80 ? "#289642" : "#f59e0b",
                backgroundColor: qualityScore >= 80 ? "#28964215" : "#f59e0b15",
              }}
            >
              {qualityScore}
            </span>
          )}
        </div>

        <p className="text-xs text-[#6b7280] capitalize">{resourceType.replace(/_/g, " ")}</p>

        {methodologyCodes.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {methodologyCodes.map((c) => (
              <span key={c} className="text-[10px] bg-[#e8e4dc] text-[#4a6741] rounded px-1.5 py-0.5">
                {c}
              </span>
            ))}
          </div>
        )}

        <p className="text-sm text-[#0E3A27] leading-relaxed">
          {shortDescription || <span className="italic text-[#9ca3af]">No short description</span>}
        </p>

        {plainDescription && (
          <div className="rounded-lg border-l-4 border-[#03848F] bg-[#f0f9fa] px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-[#03848F] mb-1">
              In plain language
            </p>
            <p className="text-sm text-[#0E3A27] leading-relaxed">{plainDescription}</p>
          </div>
        )}

        {summary && (
          <p className="text-xs text-[#6b7280] leading-relaxed line-clamp-3">{summary}</p>
        )}

        {badges.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {badges.map((b) => (
              <span
                key={b}
                className="text-[10px] font-medium bg-[#289642] text-white rounded-full px-2 py-0.5"
              >
                {BADGE_LABELS[b] ?? b}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
