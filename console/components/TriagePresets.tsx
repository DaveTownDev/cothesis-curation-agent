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
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border ${
              on
                ? "bg-[#0E3A27] text-white border-[#0E3A27]"
                : "bg-white text-[#4a6741] border-[#d4cfc5] hover:border-[#289642] hover:text-[#0E3A27]"
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
