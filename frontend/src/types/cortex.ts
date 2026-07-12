/**
 * Cortex TypeScript types — mirror of the backend Pydantic models.
 * These types are the frontend-owned contract. The backend drives changes.
 */

// ── Request types (what the frontend sends) ───────────────────────────────────

export interface ExecuteStepRequest {
  action: string
  parameters: Record<string, unknown>
}

export interface ExecuteRequest {
  goal: string
  steps: ExecuteStepRequest[]
}

// ── Response types (what the backend returns) ─────────────────────────────────

export type ErrorCode =
  | 'unknown_application'
  | 'invalid_alias'
  | 'invalid_plan'
  | 'timeout'
  | 'launch_failure'
  | 'validation_error'
  | 'safety_violation'
  | 'concurrent_execution'

export type ExecutionState = 'pending' | 'running' | 'completed' | 'failed' | 'skipped'

export interface ActionResult {
  step_id: string
  success: boolean
  message: string
  error_code: ErrorCode | null
  duration_ms: number
  metadata: Record<string, unknown>
}

export interface PlanExecutionState {
  plan_id: string
  status: ExecutionState
  current_step_id: string | null
  step_results: ActionResult[]
  started_at: string | null
  finished_at: string | null
}

// ── API error shape ────────────────────────────────────────────────────────────

export interface ApiError {
  error: string
  error_code: ErrorCode
  message: string
  plan_id?: string
}

export interface StatusResponse {
  busy: boolean
  status: 'idle' | 'running'
}
