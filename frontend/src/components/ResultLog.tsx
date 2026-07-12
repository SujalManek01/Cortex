import type { ActionResult } from '../types/cortex'

interface Props {
  results: ActionResult[]
}

const ERROR_LABELS: Record<string, string> = {
  unknown_application: 'Unknown App',
  invalid_alias: 'Invalid Alias',
  invalid_plan: 'Invalid Plan',
  timeout: 'Timeout',
  launch_failure: 'Launch Failure',
  validation_error: 'Validation Error',
  safety_violation: 'Safety Violation',
  concurrent_execution: 'Concurrent Exec',
}

function formatMs(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(2)}s`
}

export function ResultLog({ results }: Props) {
  if (results.length === 0) return null

  return (
    <div className="card result-log-card">
      <div className="card-header">
        <span className="card-icon">📋</span>
        <h2 className="card-title">Step Results</h2>
        <span className="result-count">
          {results.filter(r => r.success).length}/{results.length} passed
        </span>
      </div>

      <ol className="result-list" aria-label="Step execution results">
        {results.map((result, idx) => (
          <li
            key={result.step_id || idx}
            className={`result-item ${result.success ? 'result-success' : 'result-failure'}`}
          >
            <div className="result-row">
              <span className="result-status-icon" aria-label={result.success ? 'success' : 'failed'}>
                {result.success ? '✓' : '✗'}
              </span>
              <div className="result-details">
                <div className="result-top">
                  <code className="result-step-id">{result.step_id}</code>
                  {result.error_code && (
                    <span className="result-error-code" title={result.error_code}>
                      {ERROR_LABELS[result.error_code] ?? result.error_code}
                    </span>
                  )}
                  <span className="result-duration">{formatMs(result.duration_ms)}</span>
                </div>
                <p className="result-message">{result.message}</p>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
