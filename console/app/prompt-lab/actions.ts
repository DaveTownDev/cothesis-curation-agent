"use server"

import { revalidatePath } from "next/cache"
import { getFirestoreDb, getPromptProposal } from "@/lib/firestore"

const MERGE_INSTRUCTIONS =
  "Approved in console — merge via human PR only: apply unified_diff to the target prompt file, " +
  "bump <!-- prompt-version: … --> and agents/shared/prompt_versions.py, then run " +
  "python -m scripts.run_benchmark --check-regression before deploy."

export async function approveProposal(
  proposalId: string,
  reviewerName: string,
  notes?: string,
): Promise<void> {
  const proposal = await getPromptProposal(proposalId)
  if (!proposal) throw new Error("Proposal not found")
  if (proposal.status !== "pending") {
    throw new Error(`Proposal is already ${proposal.status}`)
  }

  const reviewedBy = reviewerName.trim() || "console"
  const reviewNotes = [MERGE_INSTRUCTIONS, notes?.trim()].filter(Boolean).join("\n\n")

  const db = getFirestoreDb()
  await db.collection("prompt_proposals").doc(proposalId).update({
    status: "approved",
    reviewed_at: new Date().toISOString(),
    reviewed_by: reviewedBy,
    review_notes: reviewNotes,
  })
  revalidatePath("/prompt-lab")
}

export async function rejectProposal(
  proposalId: string,
  reviewerName: string,
  notes?: string,
): Promise<void> {
  const proposal = await getPromptProposal(proposalId)
  if (!proposal) throw new Error("Proposal not found")
  if (proposal.status !== "pending") {
    throw new Error(`Proposal is already ${proposal.status}`)
  }

  const db = getFirestoreDb()
  await db.collection("prompt_proposals").doc(proposalId).update({
    status: "rejected",
    reviewed_at: new Date().toISOString(),
    reviewed_by: reviewerName.trim() || "console",
    review_notes: notes?.trim() || "Rejected in prompt lab console",
  })
  revalidatePath("/prompt-lab")
}
