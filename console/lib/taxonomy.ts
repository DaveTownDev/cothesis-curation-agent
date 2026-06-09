/** Curator-editable taxonomy options — synced from data/taxonomy/*.json. */
import liveMethodologies from "@/lib/data/taxonomy/live_methodologies.json"
import liveSpecialties from "@/lib/data/taxonomy/live_specialties.json"

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

export const STAGE_CODES = [
  ["TH", "Thesis design"],
  ["HI", "Health impact"],
  ["EV", "Evidence"],
  ["ST", "Statistics"],
  ["IN", "Interpretation"],
  ["SH", "Sharing"],
] as const

export const DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"] as const

export const ACCESS_TYPES = [
  "free", "freemium", "paid", "subscription", "institutional", "open_access",
] as const

export interface TaxonomyEdits {
  resource_type_code: string
  methodology_codes: string[]
  discipline_codes: string[]
  stage_codes: string[]
  difficulty_level: string
  access_type: string
}

export function methodologyFilterOptions(): [string, string][] {
  return [
    ["", "All methodologies"],
    ...METHODOLOGY_OPTIONS.map((m) => [m.code, `${m.code} — ${m.name}`] as [string, string]),
  ]
}
