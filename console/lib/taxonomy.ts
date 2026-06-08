/** Curator-editable taxonomy options (MVP + platform codes). */

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

export const METHODOLOGY_CODES = [
  "SYN-01", "SYN-02", "OBS-01", "EVAL-01",
] as const

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
  stage_codes: string[]
  difficulty_level: string
  access_type: string
}
