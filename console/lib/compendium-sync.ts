/**
 * Console-side Compendium import — mirrors agents/shared/compendium_bridge.py
 * and agents/shared/compendium_sync.py.
 */

export interface CompendiumConfig {
  baseUrl: string
  apiKey: string
}

export interface ItemSyncResult {
  resource_code: string
  ok: boolean
  compendium_id?: string | null
  compendium_url?: string | null
  error?: string | null
  skipped?: boolean
}

export interface BatchSyncResult {
  synced: number
  failed: number
  skipped: number
  results: ItemSyncResult[]
}

export interface ResourceSyncOutcome {
  compendium_id: string | null
  compendium_url: string | null
}

export interface ImportBatchResult {
  import_batch_id: string
  outcomes: ResourceSyncOutcome[]
}

export interface CompendiumRecordInput {
  resource_code?: string
  title?: string
  url?: string
  resource_type_code?: string
  resource_subtype_code?: string | null
  editorial_description?: string
  editorial_description_plain?: string | null
  methodology_codes?: string[]
  discipline_codes?: string[]
  access_type?: string
  doi?: string | null
  isbn?: string | null
  pmid?: string | null
  authors?: string[]
  publisher?: string
  journal_name?: string
  platform?: string
  year?: number
  language?: string
}

const ACCESS_TYPE_MAP: Record<string, string> = {
  open_access: "free",
  free: "free",
  freemium: "freemium",
  paid: "paid",
  subscription: "subscription",
  institutional: "institutional",
}

export function getCompendiumConfig(): CompendiumConfig | null {
  const baseUrl =
    process.env.COMPENDIUM_IMPORT_URL?.trim() ||
    process.env.COMPENDIUM_BASE_URL?.trim() ||
    ""
  const apiKey = process.env.IMPORT_API_KEY?.trim() || ""
  if (!baseUrl || !apiKey) return null
  return { baseUrl, apiKey }
}

function normalizeDisciplineSlug(slug: string): string {
  return slug.trim().toLowerCase()
}

export function toCompendiumRecord(resource: CompendiumRecordInput): Record<string, unknown> {
  const out: Record<string, unknown> = {
    title: resource.title,
    url: resource.url,
    resource_type: resource.resource_type_code,
    description: resource.editorial_description,
    source_tool: "claude",
    subtype: resource.resource_subtype_code ?? null,
    methodology_tags: resource.methodology_codes ?? [],
    specialty_tags: (resource.discipline_codes ?? []).map(normalizeDisciplineSlug),
    access_type: ACCESS_TYPE_MAP[resource.access_type ?? "free"] ?? "free",
    doi: resource.doi ?? null,
    isbn: resource.isbn ?? null,
    pmid: resource.pmid ?? null,
    discovery_context: resource.editorial_description_plain ?? null,
  }

  for (const field of ["authors", "publisher", "journal_name", "platform", "year", "language"] as const) {
    const val = resource[field]
    if (val !== undefined && val !== null && val !== "") {
      out[field] = val
    }
  }

  return out
}

function firstStr(data: Record<string, unknown>, ...keys: string[]): string | null {
  for (const key of keys) {
    const value = data[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value).trim()
    }
  }
  return null
}

export function extractResourceId(item: Record<string, unknown>): string | null {
  return firstStr(item, "resource_id", "compendium_id", "resourceId", "id")
}

function subtypePathSegment(subtype: string | null, resourceType: string | null): string {
  if (subtype) return subtype.replace(/_/g, "-")
  if (resourceType) return resourceType.replace(/_/g, "-")
  return "resources"
}

/** True when a published resource should POST to Compendium (or re-sync for id/url). */
export function needsCompendiumResync(record: {
  compendium_synced_at?: string | null
  compendium_sync_error?: string | null
  compendium_id?: string | null
  compendium_url?: string | null
}): boolean {
  if (record.compendium_sync_error) return true
  if (!record.compendium_synced_at) return true
  if (!record.compendium_id || !record.compendium_url) return true
  return false
}

export function buildCompendiumPublicUrl(
  baseUrl: string,
  opts: {
    resource_id?: string | null
    slug?: string | null
    subtype_slug?: string | null
    resource_type_code?: string | null
  },
): string | null {
  const root = baseUrl.replace(/\/$/, "")
  if (opts.resource_id) return `${root}/library/resource/${opts.resource_id}`
  if (opts.slug) {
    const segment = subtypePathSegment(opts.subtype_slug ?? null, opts.resource_type_code ?? null)
    return `${root}/library/${segment}/${opts.slug}`
  }
  return null
}

export function extractPublicUrl(
  item: Record<string, unknown>,
  baseUrl: string,
  record: CompendiumRecordInput,
): string | null {
  for (const key of ["compendium_url", "public_url", "page_url", "library_url", "url"]) {
    const value = item[key]
    if (typeof value !== "string" || !value.trim()) continue
    const trimmed = value.trim()
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) return trimmed
    if (trimmed.startsWith("/")) return `${baseUrl.replace(/\/$/, "")}${trimmed}`
  }

  const resourceId = extractResourceId(item)
  const slug = firstStr(item, "slug", "code")
  const subtype =
    firstStr(item, "subtype_slug", "subtype") ?? record.resource_subtype_code ?? null
  return buildCompendiumPublicUrl(baseUrl, {
    resource_id: resourceId,
    slug,
    subtype_slug: subtype,
    resource_type_code: record.resource_type_code ?? null,
  })
}

function resourceItems(response: Record<string, unknown>): Record<string, unknown>[] {
  for (const key of ["resources", "accepted", "accepted_resources", "results", "imported"]) {
    const raw = response[key]
    if (Array.isArray(raw)) {
      return raw.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    }
  }
  return []
}

export function parseImportResponse(
  response: Record<string, unknown>,
  records: CompendiumRecordInput[],
  baseUrl: string,
): ImportBatchResult {
  const batchId = String(response.import_batch_id ?? response.batch_id ?? "")
  const items = resourceItems(response)

  if (items.length > 0) {
    const outcomes = records.map((record, index) => {
      const item = items[index] ?? {}
      return {
        compendium_id: extractResourceId(item),
        compendium_url: extractPublicUrl(item, baseUrl, record),
      }
    })
    return { import_batch_id: batchId, outcomes }
  }

  return {
    import_batch_id: batchId,
    outcomes: records.map(() => ({ compendium_id: null, compendium_url: null })),
  }
}

export async function postToCompendium(
  records: CompendiumRecordInput[],
  config: CompendiumConfig,
): Promise<ImportBatchResult> {
  const url = `${config.baseUrl.replace(/\/$/, "")}/api/import/json`
  const sourceFile = `cothesis-console-sync-${new Date().toISOString().slice(0, 10)}`
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source_file: sourceFile,
      source_tool: "claude",
      resources: records.map(toCompendiumRecord),
    }),
    signal: AbortSignal.timeout(30_000),
  })

  if (!resp.ok) {
    const body = await resp.text().catch(() => "")
    throw new Error(`Compendium import HTTP ${resp.status}${body ? `: ${body.slice(0, 200)}` : ""}`)
  }

  const data = (await resp.json()) as Record<string, unknown>
  return parseImportResponse(data, records, config.baseUrl)
}

/** Hide/show a live Compendium resource (requires Compendium curation API). */
export async function setCompendiumVisibility(
  config: CompendiumConfig,
  resourceId: string,
  visible: boolean,
): Promise<{ ok: boolean; error?: string }> {
  const url = `${config.baseUrl.replace(/\/$/, "")}/api/curation/resource-visibility`
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ resource_id: resourceId, is_active: visible }),
      signal: AbortSignal.timeout(15_000),
    })
    if (resp.status === 404) {
      return { ok: false, error: "Compendium visibility API is not deployed yet" }
    }
    if (!resp.ok) {
      const body = await resp.text().catch(() => "")
      return { ok: false, error: `Compendium visibility HTTP ${resp.status}${body ? `: ${body.slice(0, 120)}` : ""}` }
    }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}
