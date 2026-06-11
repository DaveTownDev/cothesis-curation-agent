/**
 * Build ADK-shaped gold eval cases from HITL review data.
 * Shape validated against eval/schemas/gold_case.schema.json (P2-01).
 */
import { draftRecordToVocabularyTags, type CompendiumRecordInput } from "@/lib/compendium-sync"
import type { DraftDoc, DraftRecord, PipelineStateDoc } from "@/lib/firestore"

export const PROMPT_VERSIONS: Record<string, string> = {
  appraisal: "appraisal@1.0.0",
  classification: "classification@1.0.0",
  discovery: "discovery@1.0.0",
  editorial: "editorial@1.0.0",
  reconciliation: "reconciliation@1.0.0",
  qc_panel: "qc_panel@1.0.0",
  arbiter: "arbiter@1.0.0",
}

export type GoldCaseOrigin = "seed" | "hitl" | "synthetic"

export interface GoldCaseSource {
  resource_code: string
  origin: GoldCaseOrigin
  prompt_versions?: Record<string, string>
  failure_mode?: string | null
}

export interface ExpectedClassification {
  resource_type_code: string
  resource_subtype_code?: string | null
  methodology_codes: string[]
  skill_codes: string[]
  stage_codes: string[]
  discipline_codes: string[]
  domain_codes?: string[]
  tags: ReturnType<typeof draftRecordToVocabularyTags>
}

export interface GoldEvalCase {
  eval_id: string
  source: GoldCaseSource
  expected_classification: ExpectedClassification
  conversation: Array<Record<string, unknown>>
  conversation_scenario: null
  session_input: null
  creation_timestamp: number
  rubrics: null
  final_session_state: Record<string, unknown>
}

const STANDARD_RUBRICS = [
  {
    rubric_id: "e070ae9b",
    rubric_content: { text_property: "Response identifies at least one resource with a title and URL" },
    description: null,
    type: null,
  },
  {
    rubric_id: "66568629",
    rubric_content: { text_property: "Response includes a quality score between 0 and 100" },
    description: null,
    type: null,
  },
  {
    rubric_id: "c8d993e7",
    rubric_content: {
      text_property: "Response uses platform methodology codes with SYN-, OBS-, or EVAL- prefix",
    },
    description: null,
    type: null,
  },
  {
    rubric_id: "674eb443",
    rubric_content: {
      text_property: "Response states or implies the resource has been processed through the pipeline",
    },
    description: null,
    type: null,
  },
  {
    rubric_id: "f15b0e06",
    rubric_content: { text_property: "Response does not include legacy RS- or OD- methodology codes" },
    description: null,
    type: null,
  },
]

function textPart(text: string) {
  return {
    media_resolution: null,
    code_execution_result: null,
    executable_code: null,
    file_data: null,
    function_call: null,
    function_response: null,
    inline_data: null,
    text,
    thought: null,
    thought_signature: null,
    video_metadata: null,
    tool_call: null,
    tool_response: null,
    part_metadata: null,
  }
}

function buildUserPrompt(draft: DraftRecord): string {
  const meth = draft.methodology_codes?.length
    ? draft.methodology_codes.join(", ")
    : "none specified"
  return (
    `Curate one ${draft.resource_type_code} resource titled "${draft.title}". ` +
    `URL: ${draft.url || "n/a"}. Focus methodologies: ${meth}.`
  )
}

function buildFinalResponse(draft: DraftRecord): string {
  const meth = draft.methodology_codes?.join(", ") || "none"
  const stages = draft.stage_codes?.join(", ") || "none"
  return (
    `Processed ${draft.resource_type_code} "${draft.title}". ` +
    `Quality score ${draft.quality_score}, AI confidence ${draft.ai_confidence}. ` +
    `Methodology codes: ${meth}. Thesis stages: ${stages}. ` +
    `Draft record created with editorial_status=${draft.editorial_status}.`
  )
}

function mergedDraft(
  draft: DraftRecord,
  taxonomy?: Partial<DraftRecord>,
  edited?: Partial<DraftRecord>,
): DraftRecord {
  return { ...draft, ...edited, ...taxonomy }
}

export function buildExpectedClassification(draft: DraftRecord): ExpectedClassification {
  const record: CompendiumRecordInput = {
    resource_type_code: draft.resource_type_code,
    resource_subtype_code: draft.resource_subtype_code,
    methodology_codes: draft.methodology_codes ?? [],
    discipline_codes: draft.discipline_codes ?? [],
    stage_codes: draft.stage_codes ?? [],
    skill_codes: draft.skill_codes ?? [],
    domain_codes: (draft as CompendiumRecordInput).domain_codes ?? [],
    classification_confidence: draft.classification_confidence,
  }
  return {
    resource_type_code: draft.resource_type_code,
    resource_subtype_code: draft.resource_subtype_code ?? null,
    methodology_codes: [...(draft.methodology_codes ?? [])],
    skill_codes: [...(draft.skill_codes ?? [])],
    stage_codes: [...(draft.stage_codes ?? [])],
    discipline_codes: [...(draft.discipline_codes ?? [])],
    domain_codes: [...(record.domain_codes ?? [])],
    tags: draftRecordToVocabularyTags(record),
  }
}

export interface BuildGoldCaseInput {
  draft: DraftRecord
  resourceCode: string
  origin?: GoldCaseOrigin
  failureMode?: string | null
  taxonomy?: Partial<DraftRecord>
  edited?: Partial<DraftRecord>
  pipelineState?: PipelineStateDoc | null
  draftDoc?: DraftDoc | null
}

export function buildGoldEvalCase(input: BuildGoldCaseInput): GoldEvalCase {
  const working = mergedDraft(input.draft, input.taxonomy, input.edited)
  const resourceCode = input.resourceCode || working.resource_code
  const evalId = resourceCode

  const promptVersions: Record<string, string> = { ...PROMPT_VERSIONS }
  if (input.draftDoc?.assessment_prompt_version) {
    promptVersions.appraisal = input.draftDoc.assessment_prompt_version
  }

  const source: GoldCaseSource = {
    resource_code: resourceCode,
    origin: input.origin ?? "hitl",
    prompt_versions: promptVersions,
  }
  if (input.failureMode) {
    source.failure_mode = input.failureMode
  }

  return {
    eval_id: evalId,
    source,
    expected_classification: buildExpectedClassification(working),
    conversation: [
      {
        invocation_id: "",
        user_content: { parts: [textPart(buildUserPrompt(working))], role: null },
        final_response: { parts: [textPart(buildFinalResponse(working))], role: null },
        intermediate_data: null,
        creation_timestamp: 0.0,
        rubrics: STANDARD_RUBRICS,
        app_details: null,
      },
    ],
    conversation_scenario: null,
    session_input: null,
    creation_timestamp: 0.0,
    rubrics: null,
    final_session_state: {
      resource_code: resourceCode,
      pipeline_run_id: input.pipelineState?.pipeline_run_id ?? null,
    },
  }
}

/** Minimal structural validation (full schema check in pytest). */
export function validateGoldCase(doc: GoldEvalCase): string[] {
  const errors: string[] = []
  if (!doc.eval_id?.trim()) errors.push("eval_id is required")
  if (!doc.source?.resource_code) errors.push("source.resource_code is required")
  if (!["seed", "hitl", "synthetic"].includes(doc.source?.origin)) {
    errors.push("source.origin must be seed, hitl, or synthetic")
  }
  if (!Array.isArray(doc.conversation) || doc.conversation.length < 1) {
    errors.push("conversation must have at least one turn")
  }
  if (!doc.expected_classification?.resource_type_code) {
    errors.push("expected_classification.resource_type_code is required")
  }
  return errors
}

export function serializeGoldCase(doc: GoldEvalCase): string {
  const errors = validateGoldCase(doc)
  if (errors.length > 0) {
    throw new Error(`Invalid gold case: ${errors.join("; ")}`)
  }
  return JSON.stringify(doc, null, 2) + "\n"
}
