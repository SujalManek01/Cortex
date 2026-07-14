import { useState } from 'react'
import type { ExecuteRequest } from '../types/cortex'

interface Props {
  onPlanCommand: (command: string) => void
  onExecuteDirect: (request: ExecuteRequest) => void
  disabled: boolean
}

const JSON_PLACEHOLDER = `{
  "plan": {
    "steps": [
      { "capability": "application.open", "target": "vscode" },
      { "capability": "application.open", "target": "chrome" }
    ]
  }
}`

const NL_PLACEHOLDER = "E.g. Open Chrome and GitHub"

export function PlanInput({ onPlanCommand, onExecuteDirect, disabled }: Props) {
  const [mode, setMode] = useState<'nl' | 'json'>('nl')
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit() {
    setError(null)
    const raw = text.trim()
    if (!raw) {
      setError(mode === 'nl' ? 'Command cannot be empty.' : 'Plan JSON cannot be empty.')
      return
    }

    if (mode === 'nl') {
      onPlanCommand(raw)
      return
    }

    // JSON Mode
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
    onExecuteDirect(parsed as ExecuteRequest)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit()
    }
  }

  return (
    <div className="card plan-input-card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="card-icon">⚡</span>
          <h2 className="card-title">Command Input</h2>
        </div>
        <div className="mode-toggle">
          <button
            className={`toggle-btn ${mode === 'nl' ? 'active' : ''}`}
            onClick={() => { setMode('nl'); setError(null); }}
          >
            Natural Language
          </button>
          <button
            className={`toggle-btn ${mode === 'json' ? 'active' : ''}`}
            onClick={() => { setMode('json'); setError(null); }}
          >
            JSON
          </button>
        </div>
      </div>

      <div className="textarea-wrapper">
        <textarea
          id="plan-input"
          className={`plan-textarea${error ? ' textarea-error' : ''}`}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={mode === 'nl' ? NL_PLACEHOLDER : JSON_PLACEHOLDER}
          disabled={disabled}
          spellCheck={false}
          rows={mode === 'nl' ? 4 : 14}
          aria-label="Command Input"
          aria-describedby={error ? 'input-error' : undefined}
        />
        {error && (
          <p id="input-error" className="input-error" role="alert">
            {error}
          </p>
        )}
      </div>

      <div className="card-footer">
        <span className="hint">Ctrl+Enter to submit</span>
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
              Processing…
            </>
          ) : (
            <>{mode === 'nl' ? 'Generate Plan' : 'Execute Plan'}</>
          )}
        </button>
      </div>
    </div>
  )
}
