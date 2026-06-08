/** GCP Console deep links (project from server env). */

export function cloudTraceListUrl(projectId: string): string {
  return `https://console.cloud.google.com/traces/list?project=${encodeURIComponent(projectId)}`
}

/** Logs Explorer query scoped to a pipeline run id (best-effort trace correlation). */
export function cloudLogsForRunUrl(projectId: string, pipelineRunId: string): string {
  const query = encodeURIComponent(
    `jsonPayload.pipeline_run_id="${pipelineRunId}" OR textPayload:"${pipelineRunId}"`,
  )
  return `https://console.cloud.google.com/logs/query;query=${query}?project=${encodeURIComponent(projectId)}`
}
