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

/** Sprint 003: Natural language command request. */
export interface CommandRequest {
  command: string
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

// ── Sprint 003 & 004: Planning response types ───────────────────────────────────

export interface PlanStepSchema {
  id: string
  capability: string
  target: string
}

export interface PlanningErrorResponse {
  error_code: string
  message: string
}

export interface PlannerWarning {
  code: string
  message: string
}

export interface PlannerInfo {
  message: string
}

export interface PlannerDiagnostics {
  planning_time_ms: number
  token_count: number
  clause_count: number
  intent_group_count: number
  resolved_target_count: number
  warning_count: number
}

export interface PlanResponse {
  success: boolean
  planner: string
  confidence: number
  normalized_input: string
  warnings: PlannerWarning[]
  information: PlannerInfo[]
  diagnostics: PlannerDiagnostics | null
  planning_time_ms: number
  token_count: number
  step_count: number
  steps: PlanStepSchema[]
  error: PlanningErrorResponse | null
}

// ── Registry response types ───────────────────────────────────────────────────

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
