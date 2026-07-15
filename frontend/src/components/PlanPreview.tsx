import type { PlanResponse, ExecuteRequest } from '../types/cortex'

interface Props {
  plan: PlanResponse
  onExecute: (request: ExecuteRequest) => void
  onCancel: () => void
  disabled: boolean
}

export function PlanPreview({ plan, onExecute, onCancel, disabled }: Props) {
  function handleConfirm() {
    // Serialize to ExecuteRequest format
    const request: ExecuteRequest = {
      version: '1.0',
      plan: {
        steps: plan.steps.map(step => ({
          capability: step.capability,
          target: step.target
        }))
      }
    }
    onExecute(request)
  }

  return (
    <div className="card plan-preview-card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="card-icon">📋</span>
          <h2 className="card-title">Plan Preview</h2>
        </div>
        <span className="badge badge-success">Confidence: {(plan.confidence * 100).toFixed(0)}%</span>
      </div>

      <div className="preview-content">
        <div className="preview-meta">
          <p><strong>Input:</strong> {plan.normalized_input}</p>
          <p><strong>Planner:</strong> {plan.planner}</p>
        </div>

        {plan.warnings.length > 0 && (
          <div className="warnings" style={{ marginTop: '12px' }}>
            {plan.warnings.map((w, i) => (
              <p key={i} className="warning-text" style={{ margin: '4px 0', color: '#f38ba8' }}>
                ⚠️ <strong>[{w.code}]</strong> {w.message}
              </p>
            ))}
          </div>
        )}

        {plan.information && plan.information.length > 0 && (
          <div className="information-logs" style={{ marginTop: '12px' }}>
            {plan.information.map((info, i) => (
              <p key={i} className="info-text" style={{ margin: '4px 0', color: '#89b4fa', fontSize: '13px' }}>
                ℹ️ {info.message}
              </p>
            ))}
          </div>
        )}

        {plan.diagnostics && (
          <div className="diagnostics-summary" style={{ marginTop: '16px', padding: '10px', background: '#1e1e2e', borderRadius: '6px', fontSize: '13px', border: '1px solid #313244' }}>
            <h3 style={{ margin: '0 0 6px 0', color: '#cdd6f4', fontSize: '13px' }}>Diagnostics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', color: '#a6adc8' }}>
              <div>⏱️ Time: <strong>{plan.diagnostics.planning_time_ms} ms</strong></div>
              <div>🪙 Tokens: <strong>{plan.diagnostics.token_count}</strong></div>
              <div>📖 Clauses: <strong>{plan.diagnostics.clause_count}</strong></div>
              <div>🎯 Targets: <strong>{plan.diagnostics.resolved_target_count}</strong></div>
            </div>
          </div>
        )}

        <div className="steps-list" style={{ marginTop: '16px' }}>
          <h3>Generated Steps ({plan.step_count})</h3>
          {plan.steps.map((step, i) => (
            <div key={step.id} className="preview-step">
              <span className="step-number">{i + 1}</span>
              <div className="step-details">
                <span className="step-capability">{step.capability}</span>
                <span className="step-target">{step.target}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card-footer footer-actions">
        <button
          className="btn btn-secondary"
          onClick={onCancel}
          disabled={disabled}
        >
          Cancel
        </button>
        <button
          className="btn btn-primary"
          onClick={handleConfirm}
          disabled={disabled}
        >
          {disabled ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Executing…
            </>
          ) : (
            <>Confirm Execution</>
          )}
        </button>
      </div>
    </div>
  )
}
