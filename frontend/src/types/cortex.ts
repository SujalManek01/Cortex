/**
 * Cortex TypeScript types — mirror of the backend Pydantic models.
 * These types are the frontend-owned contract. The backend drives changes.
 */

// ── Request types (what the frontend sends) ───────────────────────────────────

export interface ExecuteStepRequest {
  capability: string
  target: string
}

export interface ExecutePlanRequest {
  steps: ExecuteStepRequest[]
}

export interface ExecuteRequest {
  version?: string
  plan: ExecutePlanRequest
}

// ── Response types (what the backend returns) ─────────────────────────────────

export interface ExecutionSummary {
  successful: number
  failed: number
  total: number
  duration: number
}

export interface ExecutionResultSchema {
  step: number
  capability: string
  target: string
  status: string
  duration: number
  error?: Record<string, any>
}

export interface ExecuteResponse {
  execution_id: string
  status: string
  duration_ms: number
  summary: ExecutionSummary
  results: ExecutionResultSchema[]
}

export interface ApplicationItem {
  alias: string
  name: string
  executable: string | null
  path: string | null
}

export interface ApplicationsResponse {
  applications: ApplicationItem[]
}

export interface FolderItem {
  alias: string
  path: string
}

export interface FoldersResponse {
  folders: FolderItem[]
}

export interface WebsiteItem {
  alias: string
  url: string
}

export interface WebsitesResponse {
  websites: WebsiteItem[]
}

export interface CapabilitiesResponse {
  capabilities: string[]
}

export interface StatusResponse {
  busy: boolean
  status: 'idle' | 'running'
}

export interface ApiError {
  error: string
  error_code: string
  message: string
  plan_id?: string
}
