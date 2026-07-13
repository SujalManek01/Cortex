import type { ExecutionResultSchema } from '../types/cortex'

interface Props {
  results: ExecutionResultSchema[]
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
          {results.filter(r => r.status === 'success').length}/{results.length} passed
        </span>
      </div>

      <ol className="result-list" aria-label="Step execution results">
        {results.map((result, idx) => {
          const isSuccess = result.status === 'success'
          return (
            <li
              key={result.step || idx}
              className={`result-item ${isSuccess ? 'result-success' : 'result-failure'}`}
            >
              <div className="result-row">
                <span className="result-status-icon" aria-label={isSuccess ? 'success' : 'failed'}>
                  {isSuccess ? '✓' : '✗'}
                </span>
                <div className="result-details">
                  <div className="result-top">
                    <code className="result-step-id">Step {result.step}</code>
                    <span className="result-duration">{formatMs(result.duration)}</span>
                  </div>
                  <p className="result-message">
                    <strong>{result.capability}</strong> {result.target}
                  </p>
                  {result.error && (
                    <div className="result-error-code">
                      {ERROR_LABELS[result.error.code] ?? result.error.code}: {result.error.message}
                    </div>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
