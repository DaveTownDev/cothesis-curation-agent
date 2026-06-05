"use client"

import { useState } from "react"
import { Pencil, Check, X } from "lucide-react"
import type { DraftRecord } from "@/lib/firestore"

interface EditableFieldProps {
  label: string
  value: string
  accent?: string
  bg?: string
  onChange: (v: string) => void
}

function EditableField({ label, value, accent = "#6b7280", bg, onChange }: EditableFieldProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const edited = value !== (draft === value ? value : draft)

  const commit = () => { onChange(draft); setEditing(false) }
  const cancel = () => { setDraft(value); setEditing(false) }

  return (
    <section className={bg ? `rounded-lg border-l-4 px-5 py-4 ${bg}` : ""} style={bg ? { borderColor: accent } : {}}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest" style={{ color: accent }}>
          {label}
          {edited && <span className="ml-2 text-[10px] normal-case tracking-normal text-[#f59e0b]">(edited)</span>}
        </h3>
        {!editing ? (
          <button onClick={() => { setDraft(value); setEditing(true) }} className="text-[#6b7280] hover:text-[#0E3A27]">
            <Pencil size={12} />
          </button>
        ) : (
          <div className="flex gap-1">
            <button onClick={commit} className="text-[#289642] hover:text-[#1f7834]"><Check size={12} /></button>
            <button onClick={cancel} className="text-[#6b7280] hover:text-red-500"><X size={12} /></button>
          </div>
        )}
      </div>
      {editing ? (
        <div>
          <textarea
            autoFocus
            className="w-full rounded border border-[#d4cfc5] px-3 py-2 text-sm text-[#0E3A27] focus:outline-none focus:ring-1 focus:ring-[#289642] resize-y min-h-[80px]"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <p className="text-[10px] text-[#6b7280] mt-1 text-right">{draft.length} chars</p>
        </div>
      ) : (
        <p className="text-[#0E3A27] leading-relaxed text-sm">{value || <span className="italic text-[#9ca3af]">Empty</span>}</p>
      )}
    </section>
  )
}

interface Props {
  record: DraftRecord
  editorialNote: string
  onEditShort: (v: string) => void
  onEditLong: (v: string) => void
  onEditPlain: (v: string) => void
  onEditNote: (v: string) => void
}

export function DescriptionSlots({
  record,
  editorialNote,
  onEditShort,
  onEditLong,
  onEditPlain,
  onEditNote,
}: Props) {
  return (
    <div className="space-y-4">
      <EditableField
        label="Editorial description (short)"
        value={record.editorial_description}
        accent="#6b7280"
        onChange={onEditShort}
      />
      <EditableField
        label="AI summary (long)"
        value={record.summary}
        accent="#6b7280"
        onChange={onEditLong}
      />
      <EditableField
        label="Plain language version"
        value={record.editorial_description_plain}
        accent="#03848F"
        bg="bg-[#f0f9fa]"
        onChange={onEditPlain}
      />
      <EditableField
        label="Editor's note (optional, featured resources only)"
        value={editorialNote}
        accent="#289642"
        bg="bg-[#f0faf2]"
        onChange={onEditNote}
      />
    </div>
  )
}
