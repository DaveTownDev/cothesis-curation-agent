"use client"

import type { DraftRecord, FieldProvenanceEntry } from "@/lib/firestore"

const SOURCE_LABELS: Record<string, string> = {
  crossref: "CrossRef", openalex: "OpenAlex", pubmed: "PubMed", unpaywall: "Unpaywall",
  icite: "iCite", openlibrary: "OpenLibrary", google_books: "Google Books",
  github: "GitHub", bio_tools: "bio.tools", datacite: "DataCite",
}

interface Props {
  draft: DraftRecord
}

function provenanceFor(
  field: string,
  fp?: Record<string, FieldProvenanceEntry>
): FieldProvenanceEntry | undefined {
  if (!fp) return undefined
  return fp[field] ?? fp[field.replace(/_/g, "")]
}

export function EnrichmentPanel({ draft }: Props) {
  const sources = draft.enrichment_sources ?? []
  const pending = draft.enrichment_pending_keys ?? []
  const fp = draft.field_provenance
  const tf = draft.type_fields ?? {}

  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-2">
          APIs consulted
        </p>
        {sources.length === 0 ? (
          <p className="text-xs text-[#6b7280] italic">No enrichment sources recorded.</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {sources.map((s) => (
              <span
                key={s}
                className="text-xs bg-[#e8f5ec] text-[#289642] border border-[#289642]/30 rounded px-2 py-0.5"
              >
                {SOURCE_LABELS[s] ?? s}
              </span>
            ))}
          </div>
        )}
      </div>

      {pending.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          <span className="font-semibold">Missing API keys: </span>
          {pending.join(", ")} — fields may be empty.
        </div>
      )}

      {(draft.time_to_consume || draft.content_format) && (
        <div className="flex flex-wrap gap-3 text-xs text-[#6b7280]">
          {draft.time_to_consume && (
            <span>Time to consume: <strong className="text-[#0E3A27]">{draft.time_to_consume}</strong></span>
          )}
          {draft.content_format && (
            <span>Format: <strong className="text-[#0E3A27]">{draft.content_format}</strong></span>
          )}
        </div>
      )}

      {Object.keys(tf).length > 0 && (
        <div>
          <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-2">
            Enriched fields
          </p>
          <div className="rounded border border-[#e8e4dc] overflow-hidden">
            <table className="w-full text-xs">
              <thead className="bg-[#F8F5EE]">
                <tr>
                  <th className="text-left px-2 py-1.5 font-medium text-[#6b7280]">Field</th>
                  <th className="text-left px-2 py-1.5 font-medium text-[#6b7280]">Value</th>
                  <th className="text-left px-2 py-1.5 font-medium text-[#6b7280]">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e8e4dc]">
                {Object.entries(tf).map(([k, v]) => {
                  const prov = provenanceFor(k, fp)
                  return (
                    <tr key={k}>
                      <td className="px-2 py-1.5 font-medium text-[#4a6741] align-top">{k}</td>
                      <td className="px-2 py-1.5 text-[#0E3A27] align-top max-w-[140px] break-words">
                        {v === null || v === undefined ? "—" : String(v)}
                      </td>
                      <td className="px-2 py-1.5 text-[#9ca3af] align-top font-mono text-[10px]">
                        {prov?.source ?? "—"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {fp && Object.keys(fp).length > 0 && Object.keys(tf).length === 0 && (
        <div>
          <p className="text-xs font-medium text-[#4a6741] uppercase tracking-wide mb-2">
            Field provenance
          </p>
          <ul className="space-y-1 text-xs text-[#6b7280]">
            {Object.entries(fp).slice(0, 20).map(([k, v]) => (
              <li key={k}>
                <span className="font-medium text-[#4a6741]">{k}</span>
                {v.source ? ` ← ${v.source}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
