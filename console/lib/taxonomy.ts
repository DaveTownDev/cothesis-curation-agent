/** Curator-editable taxonomy options — vocabulary is code authority; live scrape for on-site subset. */
import liveMethodologies from "@/lib/data/taxonomy/live_methodologies.json"
import tagVocabulary from "@/lib/data/taxonomy/tag_vocabulary.json"
import liveSubtypes from "@/lib/data/taxonomy/live_subtypes.json"
import liveSkills from "@/lib/data/taxonomy/live_skills.json"

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

export type SpecialtyOption = { code: string; slug: string; name: string }

type VocabSpecialtyNode = {
  code: string
  level: string
  name: string
  slug?: string
}

export const SPECIALTY_OPTIONS: SpecialtyOption[] = (
  tagVocabulary.taxonomies.specialty.nodes as VocabSpecialtyNode[]
)
  .filter((n) => n.level === "specialty")
  .map((n) => ({
    code: n.code,
    slug: n.slug ?? n.code.toLowerCase(),
    name: n.name.replace(/&amp;/g, "&"),
  }))

export type SubtypeOption = { code: string; name: string; type_code: string }

export const SUBTYPE_OPTIONS: SubtypeOption[] = liveSubtypes.subtypes.map(
  (s) => ({ code: s.code, name: s.name.replace(/&amp;/g, "&"), type_code: s.type_code }),
)

export function subtypesForType(typeCode: string): SubtypeOption[] {
  return SUBTYPE_OPTIONS.filter((s) => s.type_code === typeCode)
}

export type SkillOption = { code: string; name: string; slug: string }

export const SKILL_OPTIONS: SkillOption[] = liveSkills.skills.map(
  (s) => ({ code: s.code, name: s.name, slug: s.slug }),
)

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
  return taxonomyCodeNameLabel(s.code, s.name)
}

export function specialtyLabel(codeOrSlug: string): string {
  const key = codeOrSlug.trim()
  const byCode = SPECIALTY_OPTIONS.find((o) => o.code === key.toUpperCase())
  if (byCode) return specialtyOptionLabel(byCode)
  const bySlug = SPECIALTY_OPTIONS.find((o) => o.slug === key.toLowerCase())
  return bySlug ? specialtyOptionLabel(bySlug) : key
}

export function subtypeOptionLabel(s: SubtypeOption): string {
  return taxonomyCodeNameLabel(s.code, s.name)
}

/** THESIS phases + stages — from canonical tag_vocabulary.json */
export type ThesisStageOption = { code: string; name: string; level: string }

type VocabThesisNode = { code: string; level: string; name: string }

export const THESIS_STAGE_OPTIONS: ThesisStageOption[] = (
  tagVocabulary.taxonomies.thesis.nodes as VocabThesisNode[]
).map((n) => ({ code: n.code, name: n.name, level: n.level }))

/** @deprecated use THESIS_STAGE_OPTIONS — kept for tuple consumers */
export const STAGE_CODES = THESIS_STAGE_OPTIONS.map((s) => [s.code, s.name] as const)

export function thesisStageOptionLabel(s: ThesisStageOption): string {
  return taxonomyCodeNameLabel(s.code, s.name)
}

export function thesisStageLabel(code: string): string {
  const s = THESIS_STAGE_OPTIONS.find((o) => o.code === code)
  return s ? thesisStageOptionLabel(s) : code
}

export function skillOptionLabel(s: SkillOption): string {
  return taxonomyCodeNameLabel(s.code, s.name)
}

export function skillLabel(code: string): string {
  const s = SKILL_OPTIONS.find((o) => o.code === code)
  return s ? skillOptionLabel(s) : code
}

export const DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"] as const

export const ACCESS_TYPES = [
  "free", "freemium", "paid", "subscription", "institutional", "open_access",
] as const

export interface TaxonomyEdits {
  resource_type_code: string
  resource_subtype_code: string | null
  methodology_codes: string[]
  skill_codes: string[]
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
