import { requireAuth } from "@/lib/auth"
import { getPromptProposals, type PromptProposalDoc } from "@/lib/firestore"
import { PromptProposalCard } from "@/components/PromptProposalCard"

export const metadata = { title: "Prompt lab — CoThesis" }

export const revalidate = 30

export default async function PromptLabPage() {
  await requireAuth()

  let proposals: PromptProposalDoc[] = []
  let firestoreError: string | null = null
  try {
    proposals = await getPromptProposals()
  } catch (err) {
    firestoreError = err instanceof Error ? err.message : "Firestore unavailable"
  }

  const pending = proposals.filter((p) => p.status === "pending")
  const reviewed = proposals.filter((p) => p.status !== "pending")

  return (
    <div className="space-y-5 max-w-4xl">
      <h1 className="hitl-page-title">Prompt lab</h1>
      <p className="text-sm text-[#6b7280] max-w-2xl">
        Review offline prompt proposals from the prompt-lab-run Job. Approve adds merge
        instructions only — never auto-writes <code className="text-xs">agents/prompts/</code>.
      </p>

      {firestoreError && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <strong>Firestore unavailable:</strong> {firestoreError}
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-[#0E3A27]">
          Pending ({pending.length})
        </h2>
        {pending.length === 0 ? (
          <p className="text-sm text-[#6b7280]">
            No pending proposals. Flag taxonomy errors or send items from review to seed the
            failure bucket; the prompt-lab Job writes proposals here.
          </p>
        ) : (
          pending.map((p) => <PromptProposalCard key={p.id} proposal={p} />)
        )}
      </section>

      {reviewed.length > 0 && (
        <section className="space-y-3 pt-4 border-t border-[#d4cfc5]">
          <h2 className="text-sm font-semibold text-[#0E3A27]">
            Reviewed ({reviewed.length})
          </h2>
          {reviewed.map((p) => (
            <PromptProposalCard key={p.id} proposal={p} />
          ))}
        </section>
      )}
    </div>
  )
}
