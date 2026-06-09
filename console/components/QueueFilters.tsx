"use client"

import { useRouter, useSearchParams, usePathname } from "next/navigation"
import { useCallback } from "react"

const RESOURCE_TYPES = [
  ["", "All types"],
  ["article", "Article"],
  ["book", "Book"],
  ["book_chapter", "Book Chapter"],
  ["video", "Video"],
  ["podcast", "Podcast"],
  ["software", "Software"],
  ["reporting_guideline", "Reporting Guideline"],
  ["course", "Course"],
  ["web_guide", "Web Guide"],
  ["template", "Template"],
  ["visual_reference", "Visual Reference"],
  ["dataset", "Dataset"],
  ["community", "Community"],
  ["funding", "Funding"],
]

const METHODOLOGY_CODES = [
  ["", "All methodologies"],
  ["SYN-01", "SYN-01 — Narrative Systematic Review"],
  ["SYN-02", "SYN-02 — Scoping Review"],
  ["OBS-01", "OBS-01 — Retrospective Chart Review"],
  ["EVAL-01", "EVAL-01 — Clinical Audit"],
]

const QUALITY_BANDS = [
  ["", "All quality"],
  ["green", "High ≥ 80"],
  ["amber", "Mid 60–79"],
  ["red", "Low < 60"],
]

const SORT_OPTIONS = [
  ["attention", "Needs attention"],
  ["newest", "Newest first"],
  ["oldest", "Oldest first"],
  ["quality_desc", "Highest quality"],
  ["quality_asc", "Lowest quality"],
]

const VIEW_OPTIONS = [
  ["comfortable", "Comfortable"],
  ["compact", "Compact"],
]

export function QueueFilters() {
  const router = useRouter()
  const pathname = usePathname()
  const params = useSearchParams()

  const update = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(params.toString())
      if (value) next.set(key, value)
      else next.delete(key)
      router.replace(`${pathname}?${next.toString()}`)
    },
    [params, pathname, router]
  )

  const select =
    "h-8 rounded border border-[#d4cfc5] bg-white px-2 text-sm text-[#0E3A27] focus:outline-none focus:ring-1 focus:ring-[#289642]"

  const hasFilters = ["type", "methodology", "quality", "sort", "view", "preset"].some((k) => {
    const v = params.get(k)
    if (k === "sort") return v && v !== "attention"
    if (k === "view") return v && v !== "comfortable"
    if (k === "preset") return Boolean(v)
    return Boolean(v)
  })

  const clearFilters = () => router.replace(pathname)

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <label className="sr-only" htmlFor="filter-type">Resource type</label>
      <select
        id="filter-type"
        className={select}
        value={params.get("type") ?? ""}
        onChange={(e) => update("type", e.target.value)}
      >
        {RESOURCE_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      <label className="sr-only" htmlFor="filter-methodology">Methodology</label>
      <select
        id="filter-methodology"
        className={select}
        value={params.get("methodology") ?? ""}
        onChange={(e) => update("methodology", e.target.value)}
      >
        {METHODOLOGY_CODES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      <label className="sr-only" htmlFor="filter-quality">Quality band</label>
      <select
        id="filter-quality"
        className={select}
        value={params.get("quality") ?? ""}
        onChange={(e) => update("quality", e.target.value)}
      >
        {QUALITY_BANDS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      <label className="sr-only" htmlFor="filter-sort">Sort order</label>
      <select
        id="filter-sort"
        className={select}
        value={params.get("sort") ?? "attention"}
        onChange={(e) => update("sort", e.target.value)}
      >
        {SORT_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      <label className="sr-only" htmlFor="filter-view">Table density</label>
      <select
        id="filter-view"
        className={select}
        value={params.get("view") ?? "comfortable"}
        onChange={(e) => update("view", e.target.value === "comfortable" ? "" : e.target.value)}
      >
        {VIEW_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
      {hasFilters && (
        <button
          type="button"
          onClick={clearFilters}
          className="text-xs text-[#03848F] hover:underline"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
