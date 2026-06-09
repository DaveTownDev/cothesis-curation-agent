"use client"

import { SHORTCUTS } from "@/lib/keyboard"
import { X } from "lucide-react"

interface Props {
  open: boolean
  onClose: () => void
}

export function KeyboardHelp({ open, onClose }: Props) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-label="Keyboard shortcuts"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl border border-[#d4cfc5] shadow-lg max-w-sm w-full p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-serif text-lg font-semibold text-[#0E3A27]">Keyboard shortcuts</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="text-[#6b7280] hover:text-[#0E3A27]">
            <X size={18} />
          </button>
        </div>
        <ul className="space-y-2">
          {SHORTCUTS.map(({ keys, description }) => (
            <li key={keys} className="flex items-center justify-between gap-4 text-sm">
              <span className="text-[#6b7280]">{description}</span>
              <kbd className="font-mono text-xs bg-[#F8F5EE] border border-[#d4cfc5] rounded px-2 py-0.5 text-[#0E3A27] shrink-0">
                {keys}
              </kbd>
            </li>
          ))}
        </ul>
        <p className="text-[10px] text-[#9ca3af] mt-4">Disabled while typing in a field. Press ? anytime.</p>
      </div>
    </div>
  )
}
