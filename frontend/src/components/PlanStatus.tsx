import type { ExecuteResponse } from '../types/cortex'

type Phase = 'idle' | 'running' | 'completed' | 'failed' | 'error'

interface Props {
  phase: Phase
  state: ExecuteResponse | null
  errorMessage: string | null
}

const STATUS_CONFIG: Record<Phase, { label: string; emoji: string; className: string }> = {
  idle:      { label: 'Idle',      emoji: '○',  className: 'status-idle' },
  running:   { label: 'Running',   emoji: '◉',  className: 'status-running' },
  completed: { label: 'Completed', emoji: '✓',  className: 'status-completed' },
  failed:    { label: 'Failed',    emoji: '✗',  className: 'status-failed' },
  error:     { label: 'Error',     emoji: '⚠',  className: 'status-error' },
}

function formatMs(ms: number): string {
  if (!ms) return ''
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(2)}s`
}

export function PlanStatus({ phase, state, errorMessage }: Props) {
  const cfg = STATUS_CONFIG[phase]

  return (
    <div className={`card status-card ${cfg.className}`}>
      <div className="status-header">
        <span className={`status-dot ${phase === 'running' ? 'pulse' : ''}`} aria-hidden="true">
          {cfg.emoji}
        </span>
        <div className="status-text">
          <span className="status-label">{cfg.label}</span>
          {state && (
            <span className="status-plan-id" title={state.execution_id}>
              {state.execution_id.slice(0, 8)}…
            </span>
          )}
        </div>
        {state && (
          <span className="status-duration">
            {formatMs(state.duration_ms)}
          </span>
        )}
      </div>

      {errorMessage && (
        <div className="error-banner" role="alert">
          <span className="error-banner-icon">⚠</span>
          <span>{errorMessage}</span>
        </div>
      )}

      {state && phase === 'running' && (
        <div className="progress-bar-track" role="progressbar" aria-label="Executing plan">
          <div className="progress-bar-fill" />
        </div>
      )}
    </div>
  )
}
