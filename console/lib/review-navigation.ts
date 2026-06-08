export function reviewNextPath(nextId: string | null, queueQuery: string): string {
  if (nextId) return `/review/${nextId}${queueQuery ? `?${queueQuery}` : ""}`
  return queueQuery ? `/review?${queueQuery}` : "/review"
}
