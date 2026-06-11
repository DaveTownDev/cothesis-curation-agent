/**
 * Write structured eval failures to Firestore eval_failure_bucket.
 * Mirrors agents/shared/firestore_schemas.py EvalFailureBucketDoc.
 */
import { getFirestoreDb, type EvalFailureBucketDoc, type FailureOrigin } from "@/lib/firestore"
import { PROMPT_VERSIONS } from "@/lib/eval-export"

const AGENT_FOR_FIELD: Record<string, string> = {
  resource_type_code: "classification",
  resource_subtype_code: "classification",
  methodology_codes: "classification",
  discipline_codes: "classification",
  stage_codes: "classification",
  skill_codes: "classification",
  domain_codes: "classification",
  editorial_description: "editorial",
  summary: "editorial",
  quality_score: "appraisal",
}

export function promptVersionForAgent(agent: string): string {
  const key = agent.trim().toLowerCase().replace(/_agent$/, "")
  return PROMPT_VERSIONS[key] ?? `${key}@1.0.0`
}

export function agentForField(field: string): string {
  return AGENT_FOR_FIELD[field] ?? "classification"
}

export interface RecordFailureInput {
  resource_code: string
  field: string
  human_label: string
  agent?: string
  origin?: FailureOrigin
  prompt_version?: string
  pipeline_run_id?: string | null
  review_queue_id?: string | null
}

export async function recordEvalFailure(input: RecordFailureInput): Promise<string> {
  const agent = input.agent ?? agentForField(input.field)
  const doc: EvalFailureBucketDoc = {
    resource_code: input.resource_code,
    agent,
    field: input.field,
    human_label: input.human_label.trim(),
    prompt_version: input.prompt_version ?? promptVersionForAgent(agent),
    created_at: new Date().toISOString(),
    origin: input.origin ?? "hitl_flag",
    pipeline_run_id: input.pipeline_run_id ?? null,
    review_queue_id: input.review_queue_id ?? null,
    consumed_by_lab_run_id: null,
  }

  if (!doc.human_label) {
    throw new Error("human_label is required")
  }

  const db = getFirestoreDb()
  const ref = await db.collection("eval_failure_bucket").add(doc)
  return ref.id
}
