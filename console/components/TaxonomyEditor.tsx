"use client"

import { useMemo, useState } from "react"
import {
  RESOURCE_TYPES, METHODOLOGY_OPTIONS, SPECIALTY_OPTIONS, SKILL_OPTIONS, THESIS_STAGE_OPTIONS,
  DIFFICULTY_LEVELS, ACCESS_TYPES, subtypesForType, methodologyOptionLabel,
  specialtyOptionLabel, skillOptionLabel, subtypeOptionLabel, thesisStageOptionLabel, type TaxonomyEdits,
} from "@/lib/taxonomy"

interface Props {
  value: TaxonomyEdits
  onChange: (v: TaxonomyEdits) => void
}

const selectCls =
  "w-full h-8 rounded border border-[#d4cfc5] bg-white px-2 text-xs text-[#0E3A27] focus:outline-none focus:ring-1 focus:ring-[#289642]"

const scrollCls = "max-h-28 overflow-y-auto rounded border border-[#e8e4dc] p-1.5 space-y-0.5"

export function TaxonomyEditor({ value, onChange }: Props) {
  const [methFilter, setMethFilter] = useState("")
  const [specFilter, setSpecFilter] = useState("")

  const filteredMeth = useMemo(() => {
    const q = methFilter.trim().toLowerCase()
    if (!q) return METHODOLOGY_OPTIONS
    return METHODOLOGY_OPTIONS.filter(
      (m) => m.code.toLowerCase().includes(q) || m.name.toLowerCase().includes(q),
    )
  }, [methFilter])

  const filteredSpec = useMemo(() => {
    const q = specFilter.trim().toLowerCase()
    if (!q) return SPECIALTY_OPTIONS
    return SPECIALTY_OPTIONS.filter(
      (s) => s.slug.includes(q) || s.name.toLowerCase().includes(q),
    )
  }, [specFilter])

  const subtypeOptions = useMemo(
    () => subtypesForType(value.resource_type_code),
    [value.resource_type_code],
  )

  function toggleCode(
    field: "methodology_codes" | "skill_codes" | "stage_codes" | "discipline_codes",
    code: string,
  ) {
    const set = new Set(value[field])
    if (set.has(code)) set.delete(code)
    else set.add(code)
    onChange({ ...value, [field]: Array.from(set) })
  }

  return (
    <div className="space-y-3 text-xs">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[#4a6741]">
        Taxonomy — edits saved on approve
      </p>

      <label className="block space-y-1">
        <span className="text-[#6b7280]">Resource type</span>
        <select
          className={selectCls}
          value={value.resource_type_code}
          onChange={(e) => {
            const typeCode = e.target.value
            const validSubtypes = subtypesForType(typeCode)
            const keepSubtype = validSubtypes.some((s) => s.code === value.resource_subtype_code)
            onChange({
              ...value,
              resource_type_code: typeCode,
              resource_subtype_code: typeCode === "book_chapter"
                ? null
                : keepSubtype ? value.resource_subtype_code : null,
            })
          }}
        >
          {RESOURCE_TYPES.map(([code, label]) => (
            <option key={code} value={code}>{label}</option>
          ))}
        </select>
      </label>

      {value.resource_type_code !== "book_chapter" && (
        <label className="block space-y-1">
          <span className="text-[#6b7280]">Resource subtype</span>
          <select
            className={selectCls}
            value={value.resource_subtype_code ?? ""}
            onChange={(e) => onChange({
              ...value,
              resource_subtype_code: e.target.value || null,
            })}
          >
            <option value="">— none —</option>
            {subtypeOptions.map((s) => (
              <option key={s.code} value={s.code}>{subtypeOptionLabel(s)}</option>
            ))}
          </select>
        </label>
      )}

      <div>
        <span className="text-[#6b7280] block mb-1">
          Methodologies ({value.methodology_codes.length} selected)
        </span>
        <input
          type="search"
          placeholder="Filter methodologies…"
          value={methFilter}
          onChange={(e) => setMethFilter(e.target.value)}
          className="mb-1 w-full h-7 rounded border border-[#d4cfc5] px-2 text-xs"
        />
        <div className={scrollCls}>
          <div className="flex flex-wrap gap-1">
            {filteredMeth.map((m) => {
              const on = value.methodology_codes.includes(m.code)
              return (
                <button
                  key={m.code}
                  type="button"
                  title={methodologyOptionLabel(m)}
                  onClick={() => toggleCode("methodology_codes", m.code)}
                  className={`rounded px-1.5 py-0.5 text-[10px] leading-snug text-left transition-colors ${
                    on ? "bg-[#289642] text-white" : "bg-[#e8e4dc] text-[#4a6741] hover:bg-[#d4cfc5]"
                  }`}
                >
                  <span className="font-mono">{m.code}</span>
                  <span className="opacity-80"> — {m.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div>
        <span className="text-[#6b7280] block mb-1">
          Foundation skills ({value.skill_codes.length} selected)
        </span>
        <div className={scrollCls}>
          <div className="flex flex-wrap gap-1">
            {SKILL_OPTIONS.map((s) => {
              const on = value.skill_codes.includes(s.code)
              return (
                <button
                  key={s.code}
                  type="button"
                  title={skillOptionLabel(s)}
                  onClick={() => toggleCode("skill_codes", s.code)}
                  className={`rounded px-1.5 py-0.5 text-[10px] leading-snug text-left transition-colors ${
                    on ? "bg-[#c45c26] text-white" : "bg-[#e8e4dc] text-[#4a6741] hover:bg-[#d4cfc5]"
                  }`}
                >
                  <span className="font-mono">{s.code}</span>
                  <span className="opacity-80"> — {s.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div>
        <span className="text-[#6b7280] block mb-1">
          Specialties ({value.discipline_codes.length} selected, max 3)
        </span>
        <input
          type="search"
          placeholder="Filter specialties…"
          value={specFilter}
          onChange={(e) => setSpecFilter(e.target.value)}
          className="mb-1 w-full h-7 rounded border border-[#d4cfc5] px-2 text-xs"
        />
        <div className={scrollCls}>
          <div className="flex flex-wrap gap-1">
            {filteredSpec.map((s) => {
              const on = value.discipline_codes.includes(s.slug)
              return (
                <button
                  key={s.slug}
                  type="button"
                  title={`${specialtyOptionLabel(s)} (${s.slug})`}
                  onClick={() => toggleCode("discipline_codes", s.slug)}
                  className={`rounded px-1.5 py-0.5 text-[10px] leading-snug text-left transition-colors ${
                    on ? "bg-[#6b4fa0] text-white" : "bg-[#e8e4dc] text-[#4a6741] hover:bg-[#d4cfc5]"
                  }`}
                >
                  {specialtyOptionLabel(s)}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div>
        <span className="text-[#6b7280] block mb-1">THESIS stages</span>
        <div className="flex flex-wrap gap-1">
          {THESIS_STAGE_OPTIONS.map((s) => {
            const on = value.stage_codes.includes(s.code)
            return (
              <button
                key={s.code}
                type="button"
                title={thesisStageOptionLabel(s)}
                onClick={() => toggleCode("stage_codes", s.code)}
                className={`rounded px-1.5 py-0.5 text-[10px] leading-snug text-left transition-colors ${
                  on ? "bg-[#03848F] text-white" : "bg-[#e8e4dc] text-[#4a6741] hover:bg-[#d4cfc5]"
                }`}
              >
                <span className="font-mono">{s.code}</span>
                <span className="opacity-80"> — {s.name}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label className="space-y-1">
          <span className="text-[#6b7280]">Difficulty</span>
          <select
            className={selectCls}
            value={value.difficulty_level}
            onChange={(e) => onChange({ ...value, difficulty_level: e.target.value })}
          >
            {DIFFICULTY_LEVELS.map((d) => (
              <option key={d} value={d} className="capitalize">{d}</option>
            ))}
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-[#6b7280]">Access</span>
          <select
            className={selectCls}
            value={value.access_type}
            onChange={(e) => onChange({ ...value, access_type: e.target.value })}
          >
            {ACCESS_TYPES.map((a) => (
              <option key={a} value={a}>{a.replace(/_/g, " ")}</option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}
