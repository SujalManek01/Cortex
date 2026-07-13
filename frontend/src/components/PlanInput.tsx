import { useState } from 'react'
import type { ExecuteRequest } from '../types/cortex'

interface Props {
  onSubmit: (request: ExecuteRequest) => void
  disabled: boolean
}

const PLACEHOLDER = `{
  "plan": {
    "steps": [
      { "capability": "application.open", "target": "vscode" },
      { "capability": "application.open", "target": "chrome" }
    ]
  }
}`

export function PlanInput({ onSubmit, disabled }: Props) {
  const [json, setJson] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit() {
    setError(null)
    const raw = json.trim()
    if (!raw) {
      setError('Plan JSON cannot be empty.')
      return
    }
    let parsed: unknown
    try {
      parsed = JSON.parse(raw)
    } catch {
      setError('Invalid JSON. Check your syntax and try again.')
      return
    }
    if (
      typeof parsed !== 'object' ||
      parsed === null ||
      !('plan' in parsed) ||
      typeof (parsed as any).plan !== 'object' ||
      !('steps' in (parsed as any).plan)
    ) {
      setError('JSON must have a "plan" object with a "steps" array field.')
      return
    }
    onSubmit(parsed as ExecuteRequest)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit()
    }
  }

  return (
    <div className="card plan-input-card">
      <div className="card-header">
        <span className="card-icon">⚡</span>
        <h2 className="card-title">Action Plan</h2>
        <span className="hint">Ctrl+Enter to submit</span>
      </div>

      <div className="textarea-wrapper">
        <textarea
          id="plan-json-input"
          className={`plan-textarea${error ? ' textarea-error' : ''}`}
          value={json}
          onChange={e => setJson(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDER}
          disabled={disabled}
          spellCheck={false}
          rows={14}
          aria-label="ActionPlan JSON"
          aria-describedby={error ? 'input-error' : undefined}
        />
        {error && (
          <p id="input-error" className="input-error" role="alert">
            {error}
          </p>
        )}
      </div>

      <div className="card-footer">
        <button
          id="submit-plan-btn"
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={disabled}
          aria-busy={disabled}
        >
          {disabled ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Executing…
            </>
          ) : (
            <>Execute Plan</>
          )}
        </button>
      </div>
    </div>
  )
}
