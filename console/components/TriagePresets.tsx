"use client"

import { useRouter, useSearchParams, usePathname } from "next/navigation"
import { TRIAGE_PRESETS, type TriagePreset } from "@/lib/queue-filters"

interface Props {
  active: TriagePreset
}

export function TriagePresets({ active }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()

  function setPreset(id: TriagePreset) {
    const next = new URLSearchParams(params.toString())
    if (id === "all") next.delete("preset")
    else next.set("preset", id)
    router.replace(`${pathname}?${next.toString()}`)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {TRIAGE_PRESETS.map(({ id, label, description }) => {
        const on = active === id
        return (
          <button
            key={id}
            type="button"
            title={description}
            onClick={() => setPreset(id)}
            className={`rounded-[var(--radius-signature)] px-2 py-0.5 text-[0.6875rem] font-medium transition-colors border ${
              on
                ? "bg-[var(--bg-forest)] text-white border-[var(--bg-forest)]"
                : "bg-white text-[var(--text-body)] border-[var(--border-primary)] hover:border-[var(--green-primary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
