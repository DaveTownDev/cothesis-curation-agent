"use client"

import { useState, useTransition } from "react"
import { approveProposal, rejectProposal } from "@/app/prompt-lab/actions"
import type { PromptProposalDoc } from "@/lib/firestore"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, XCircle } from "lucide-react"

interface Props {
  proposal: PromptProposalDoc
}

export function PromptProposalCard({ proposal }: Props) {
  const [notes, setNotes] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  function reviewerName(): string {
    if (typeof window === "undefined") return "console"
    return localStorage.getItem("cothesis_reviewer") ?? "console"
  }

  function run(action: "approve" | "reject") {
    setError(null)
    startTransition(async () => {
      try {
        if (action === "approve") {
          await approveProposal(proposal.id, reviewerName(), notes)
        } else {
          await rejectProposal(proposal.id, reviewerName(), notes)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Action failed")
      }
    })
  }

  const delta = proposal.eval_delta

  return (
    <Card className="border-[#d4cfc5]">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base text-[#0E3A27] font-serif">
              {proposal.target_prompt_file}
            </CardTitle>
            <p className="text-xs text-[#6b7280] mt-1">
              {proposal.status} · {proposal.created_at?.slice(0, 19) ?? "—"}
              {proposal.lab_run_id ? ` · run ${proposal.lab_run_id}` : ""}
            </p>
          </div>
          <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded bg-[#f5f3ee] text-[#4a6741]">
            {proposal.status}
          </span>
        </div>
        {proposal.rationale && (
          <p className="text-sm text-[#374151] mt-2">{proposal.rationale}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {delta && (
          <div className="rounded border border-[#d4cfc5] bg-[#faf9f6] p-3 text-xs space-y-1">
            <p className="font-semibold text-[#0E3A27]">Eval delta</p>
            <p>
              Subset {delta.subset_cases ?? 0} cases ·{" "}
              {delta.passed ? "passed" : "failed"} vs {delta.baseline_path ?? "baseline"}
            </p>
            {delta.response_match_score != null && (
              <p>response_match_score: {delta.response_match_score.toFixed(3)}</p>
            )}
            {delta.notes && <p className="text-[#6b7280]">{delta.notes}</p>}
          </div>
        )}

        <div>
          <p className="text-xs font-semibold text-[#4a6741] uppercase tracking-wide mb-2">
            Unified diff
          </p>
          <pre className="text-[11px] leading-relaxed overflow-x-auto rounded border border-[#d4cfc5] bg-[#1e1e1e] text-[#d4d4d4] p-3 max-h-80">
            {proposal.unified_diff}
          </pre>
        </div>

        {proposal.status === "pending" && (
          <div className="space-y-2">
            <textarea
              className="w-full text-xs rounded border border-[#d4cfc5] p-2 min-h-[60px]"
              placeholder="Optional review notes…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            {error && (
              <p className="text-xs text-red-600">{error}</p>
            )}
            <div className="flex gap-2">
              <Button
                size="sm"
                data-action="approve-proposal"
                disabled={isPending}
                onClick={() => run("approve")}
              >
                <CheckCircle size={14} />
                {isPending ? "Saving…" : "Approve (PR instructions)"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                data-action="reject-proposal"
                disabled={isPending}
                className="text-red-600 border-red-200"
                onClick={() => run("reject")}
              >
                <XCircle size={14} />
                Reject
              </Button>
            </div>
            <p className="text-[10px] text-[#6b7280]">
              Approve does not write agents/prompts/ — open a PR with the diff above.
            </p>
          </div>
        )}

        {proposal.review_notes && proposal.status !== "pending" && (
          <div className="text-xs text-[#374151] rounded bg-[#f5f3ee] p-2 whitespace-pre-wrap">
            {proposal.review_notes}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
