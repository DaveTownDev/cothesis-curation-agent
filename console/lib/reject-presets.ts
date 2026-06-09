/** Curator quick-pick reasons for rejecting a review queue item. */

export interface RejectPreset {
  id: string
  label: string
  reason: string
}

export const REJECT_PRESETS: RejectPreset[] = [
  {
    id: "hallucinated",
    label: "Hallucinated reference",
    reason: "Hallucinated reference — content not supported by the cited source",
  },
  {
    id: "not_relevant",
    label: "Not relevant",
    reason: "Not relevant to CoThesis compendium scope",
  },
  {
    id: "duplicate",
    label: "Duplicate",
    reason: "Duplicate of an existing compendium resource",
  },
  {
    id: "dead_source",
    label: "Dead / fabricated source",
    reason: "Source URL or DOI is dead, unverifiable, or fabricated",
  },
  {
    id: "wrong_classification",
    label: "Unfixable classification",
    reason: "Classification errors cannot be corrected — resource outside MVP methodologies",
  },
]
