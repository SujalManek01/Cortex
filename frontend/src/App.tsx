import { useState } from 'react'
import type { PlanExecutionState } from './types/cortex'
import { executePlan } from './api/cortexApi'
import type { ExecuteRequest } from './types/cortex'
import { PlanInput } from './components/PlanInput'
import { PlanStatus } from './components/PlanStatus'
import { ResultLog } from './components/ResultLog'

type Phase = 'idle' | 'running' | 'completed' | 'failed' | 'error'

export default function App() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [planState, setPlanState] = useState<PlanExecutionState | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(request: ExecuteRequest) {
    setPhase('running')
    setPlanState(null)
    setErrorMessage(null)

    try {
      const state = await executePlan(request)
      setPlanState(state)
      setPhase(state.status === 'completed' ? 'completed' : 'failed')
    } catch (err: unknown) {
      const e = err as { message?: string; status?: number; detail?: { message?: string } }
      const msg = e.detail?.message ?? e.message ?? 'Unknown error.'
      setErrorMessage(msg)
      setPhase('error')
    }
  }

  return (
    <div className="app">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-mark" aria-hidden="true">◈</span>
            <span className="logo-name">Cortex</span>
          </div>
          <p className="tagline">AI Operating Layer — Sprint 001</p>
        </div>
      </header>

      {/* ── Main layout ─────────────────────────────────────────────────────── */}
      <main className="main-layout">
        <div className="left-column">
          <PlanInput onSubmit={handleSubmit} disabled={phase === 'running'} />
        </div>

        <div className="right-column">
          <PlanStatus
            phase={phase}
            state={planState}
            errorMessage={errorMessage}
          />
          {planState && <ResultLog results={planState.step_results} />}
        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="app-footer">
        <span>Cortex · SPR-001 · Core Execution Engine</span>
      </footer>
    </div>
  )
}
