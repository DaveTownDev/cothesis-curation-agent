/** Curator-editable taxonomy options — synced from data/taxonomy/*.json. */
import liveMethodologies from "@/lib/data/taxonomy/live_methodologies.json"
import liveSpecialties from "@/lib/data/taxonomy/live_specialties.json"
import liveSubtypes from "@/lib/data/taxonomy/live_subtypes.json"

export const RESOURCE_TYPES = [
  ["article", "Article"],
  ["book", "Book"],
  ["book_chapter", "Book chapter"],
  ["video", "Video"],
  ["podcast", "Podcast"],
  ["software", "Software"],
  ["reporting_guideline", "Reporting guideline"],
  ["course", "Course"],
  ["web_guide", "Web guide"],
  ["template", "Template"],
  ["visual_reference", "Visual reference"],
  ["dataset", "Dataset"],
  ["community", "Community"],
  ["funding", "Funding"],
] as const

export type MethodologyOption = { code: string; name: string; slug: string }

export const METHODOLOGY_OPTIONS: MethodologyOption[] = liveMethodologies.methodologies.map(
  (m) => ({ code: m.code, name: m.name, slug: m.slug }),
)

/** @deprecated use METHODOLOGY_OPTIONS — kept for simple code-only consumers */
export const METHODOLOGY_CODES = METHODOLOGY_OPTIONS.map((m) => m.code)

export type SpecialtyOption = { slug: string; name: string }

export const SPECIALTY_OPTIONS: SpecialtyOption[] = liveSpecialties.specialties.map(
  (s) => ({ slug: s.slug, name: s.name.replace(/&amp;/g, "&") }),
)

export type SubtypeOption = { code: string; name: string; type_code: string }

export const SUBTYPE_OPTIONS: SubtypeOption[] = liveSubtypes.subtypes.map(
  (s) => ({ code: s.code, name: s.name.replace(/&amp;/g, "&"), type_code: s.type_code }),
)

export function subtypesForType(typeCode: string): SubtypeOption[] {
  return SUBTYPE_OPTIONS.filter((s) => s.type_code === typeCode)
}

/** Display label for code + human name (dropdowns, chips, filters). */
export function taxonomyCodeNameLabel(code: string, name: string): string {
  return `${code} — ${name}`
}

export function methodologyOptionLabel(m: MethodologyOption): string {
  return taxonomyCodeNameLabel(m.code, m.name)
}

export function methodologyLabel(code: string): string {
  const m = METHODOLOGY_OPTIONS.find((o) => o.code === code)
  return m ? methodologyOptionLabel(m) : code
}

export function specialtyOptionLabel(s: SpecialtyOption): string {
  return s.name
}

export function specialtyLabel(slug: string): string {
  const s = SPECIALTY_OPTIONS.find((o) => o.slug === slug)
  return s ? specialtyOptionLabel(s) : slug
}

export function subtypeOptionLabel(s: SubtypeOption): string {
  return taxonomyCodeNameLabel(s.code, s.name)
}

/** THESIS phase codes — names from cothesis_thesis_stages.json / docs/TAXONOMY.md */
export type ThesisStageOption = { code: string; name: string }

export const THESIS_STAGE_OPTIONS: ThesisStageOption[] = [
  { code: "TH", name: "Theory" },
  { code: "HI", name: "History" },
  { code: "EV", name: "Evaluate" },
  { code: "ST", name: "Study" },
  { code: "IN", name: "Interpret" },
  { code: "SH", name: "Share" },
]

/** @deprecated use THESIS_STAGE_OPTIONS — kept for tuple consumers */
export const STAGE_CODES = THESIS_STAGE_OPTIONS.map((s) => [s.code, s.name] as const)

export function thesisStageOptionLabel(s: ThesisStageOption): string {
  return taxonomyCodeNameLabel(s.code, s.name)
}

export function thesisStageLabel(code: string): string {
  const s = THESIS_STAGE_OPTIONS.find((o) => o.code === code)
  return s ? thesisStageOptionLabel(s) : code
}

export const DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"] as const

export const ACCESS_TYPES = [
  "free", "freemium", "paid", "subscription", "institutional", "open_access",
] as const

export interface TaxonomyEdits {
  resource_type_code: string
  resource_subtype_code: string | null
  methodology_codes: string[]
  discipline_codes: string[]
  stage_codes: string[]
  difficulty_level: string
  access_type: string
}

export function methodologyFilterOptions(): [string, string][] {
  return [
    ["", "All methodologies"],
    ...METHODOLOGY_OPTIONS.map((m) => [m.code, methodologyOptionLabel(m)] as [string, string]),
  ]
}
