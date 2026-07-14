import { useState } from 'react'
import type { ExecuteResponse, PlanResponse, ExecuteRequest } from './types/cortex'
import { executePlan, generatePlan } from './api/cortexApi'
import { PlanInput } from './components/PlanInput'
import { PlanPreview } from './components/PlanPreview'
import { PlanStatus } from './components/PlanStatus'
import { ResultLog } from './components/ResultLog'
import { RegistryPanels } from './components/RegistryPanels'

type Phase = 'idle' | 'planning' | 'review' | 'running' | 'completed' | 'failed' | 'error'

export default function App() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [planState, setPlanState] = useState<ExecuteResponse | null>(null)
  const [previewPlan, setPreviewPlan] = useState<PlanResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handlePlanCommand(command: string) {
    setPhase('planning')
    setPlanState(null)
    setPreviewPlan(null)
    setErrorMessage(null)

    try {
      const result = await generatePlan(command)
      if (result.success) {
        setPreviewPlan(result)
        setPhase('review')
      } else {
        setErrorMessage(result.error?.message ?? 'Planning failed')
        setPhase('error')
      }
    } catch (err: unknown) {
      const e = err as { message?: string; status?: number; detail?: { message?: string } }
      const msg = e.detail?.message ?? e.message ?? 'Unknown error during planning.'
      setErrorMessage(msg)
      setPhase('error')
    }
  }

  async function handleExecuteDirect(request: ExecuteRequest) {
    setPhase('running')
    setPlanState(null)
    setPreviewPlan(null)
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

  function handleCancelPlan() {
    setPhase('idle')
    setPreviewPlan(null)
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
          <p className="tagline">AI Operating Layer — Sprint 003</p>
        </div>
      </header>

      {/* ── Main layout ─────────────────────────────────────────────────────── */}
      <main className="main-layout">
        <div className="left-column">
          <PlanInput 
            onPlanCommand={handlePlanCommand} 
            onExecuteDirect={handleExecuteDirect} 
            disabled={phase === 'planning' || phase === 'running'} 
          />
          <RegistryPanels />
        </div>

        <div className="right-column">
          {phase === 'review' && previewPlan ? (
            <PlanPreview 
              plan={previewPlan} 
              onExecute={handleExecuteDirect} 
              onCancel={handleCancelPlan} 
              disabled={false} 
            />
          ) : (
            <>
              <PlanStatus
                phase={phase}
                state={planState}
                errorMessage={errorMessage}
              />
              {planState && <ResultLog results={planState.results} />}
            </>
          )}
        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="app-footer">
        <span>Cortex · SPR-003 · Natural Language Planning</span>
      </footer>
    </div>
  )
}
