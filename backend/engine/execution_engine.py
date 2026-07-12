"""ExecutionEngine — sequential, deterministic plan executor.

From the spec:
  - Sequential execution
  - Stop on failure
  - One plan at a time
  - 30 second timeout per step
  - Structured events

Engineering Rules enforced here:
  3. ActionPlans are immutable (engine never modifies the plan).
  4. Execution state is separate (PlanExecutionState tracks runtime).
  8. Engine never contains action-specific conditionals (all routing via registry).

Refinement 4: ActionRegistry, StructuredLogger, and ReadOnlyConfig are
injected via constructor. The asyncio.Lock is an internal implementation
detail and is NOT injected — it belongs to the engine exclusively.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from backend.config.config_loader import ReadOnlyConfig
from backend.logging.logger import StructuredLogger
from backend.models.action_context import ActionContext, WorkspaceMetadata
from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode
from backend.models.execution_state import ExecutionState, PlanExecutionState
from backend.registry.action_registry import ActionRegistry, UnknownActionError


class ConcurrentExecutionError(Exception):
    """Raised when a plan is submitted while another is already running.

    Maps to HTTP 409 Conflict.
    """

    def __init__(self) -> None:
        super().__init__(
            "A plan is already executing. Concurrent execution is not supported. "
            "Wait for the current plan to finish before submitting another."
        )
        self.error_code = ErrorCode.CONCURRENT_EXECUTION


class ExecutionEngine:
    """Executes ActionPlans sequentially and deterministically.

    One plan at a time is enforced by an asyncio.Lock acquired at the start
    of execute(). If the lock is already held, ConcurrentExecutionError is
    raised immediately (no queuing).

    Per-step timeouts are enforced via asyncio.wait_for(). A timed-out step
    produces an ActionResult with ErrorCode.TIMEOUT and halts the plan.

    Refinement 4: All dependencies are injected via constructor.
    """

    def __init__(
        self,
        registry: ActionRegistry,
        logger: StructuredLogger,
        config: ReadOnlyConfig,
        step_timeout_seconds: float = 30.0,
    ) -> None:
        """
        Args:
            registry:              ActionRegistry for executor lookup.
            logger:                StructuredLogger for JSON Lines output.
            config:                ReadOnlyConfig passed into ActionContext for executors.
            step_timeout_seconds:  Per-step timeout. Default 30s per spec.
                                   Can be overridden in tests for faster timeout testing.
        """
        self._registry = registry
        self._logger = logger
        self._config = config
        self._step_timeout = step_timeout_seconds
        self._lock = asyncio.Lock()

    # ── Public API ─────────────────────────────────────────────────────────────

    async def execute(self, plan: ActionPlan) -> PlanExecutionState:
        """Execute an ActionPlan. Returns PlanExecutionState on completion.

        Args:
            plan: A validated, safety-checked, immutable ActionPlan.

        Returns:
            PlanExecutionState with status COMPLETED or FAILED, and all
            step results populated.

        Raises:
            ConcurrentExecutionError: If another plan is currently running.
        """
        if self._lock.locked():
            raise ConcurrentExecutionError()

        async with self._lock:
            return await self._run(plan)

    @property
    def is_busy(self) -> bool:
        """True if a plan is currently executing."""
        return self._lock.locked()

    # ── Internal execution loop ────────────────────────────────────────────────

    async def _run(self, plan: ActionPlan) -> PlanExecutionState:
        """Internal execution loop. Called with the lock already acquired."""
        plan_id_str = str(plan.plan_id)
        plan_start = time.monotonic()

        state = PlanExecutionState(
            plan_id=plan.plan_id,
            status=ExecutionState.RUNNING,
            started_at=datetime.now(tz=timezone.utc),
        )

        self._logger.plan_start(plan_id_str, plan.goal, len(plan.steps))

        plan_succeeded = True

        for step in plan.steps:
            state.current_step_id = step.id
            self._logger.step_start(
                plan_id_str, step.id, step.action, dict(step.parameters)
            )

            step_start = time.monotonic()

            # Build a per-step ActionContext with the correct step_id.
            context = ActionContext(
                logger=self._logger,
                config=self._config,
                workspace=WorkspaceMetadata(
                    plan_id=plan.plan_id,
                    goal=plan.goal,
                    version=plan.version,
                    step_id=step.id,
                ),
            )

            result = await self._execute_step(context, step, plan_id_str, step_start)
            state.step_results.append(result)

            self._logger.step_complete(
                plan_id=plan_id_str,
                step_id=step.id,
                action=step.action,
                status="completed" if result.success else "failed",
                duration_ms=result.duration_ms,
                error_code=result.error_code.value if result.error_code else None,
            )

            if not result.success:
                plan_succeeded = False
                break  # Engineering Rule: Stop on failure.

        plan_duration_ms = (time.monotonic() - plan_start) * 1000
        state.status = (
            ExecutionState.COMPLETED if plan_succeeded else ExecutionState.FAILED
        )
        state.current_step_id = None
        state.finished_at = datetime.now(tz=timezone.utc)

        self._logger.plan_complete(
            plan_id_str,
            status=state.status.value,
            duration_ms=plan_duration_ms,
        )

        return state

    async def _execute_step(
        self,
        context: ActionContext,
        step: ActionStep,
        plan_id_str: str,
        step_start: float,
    ) -> ActionResult:
        """Execute a single step with timeout and error isolation.

        Never raises. Returns an ActionResult for every outcome.
        """
        # Resolve executor (should always succeed — validator checked this already).
        try:
            executor = self._registry.get(step.action)
        except UnknownActionError as exc:
            return ActionResult(
                step_id=step.id,
                success=False,
                message=str(exc),
                error_code=ErrorCode.VALIDATION_ERROR,
                duration_ms=(time.monotonic() - step_start) * 1000,
            )

        # Execute with per-step timeout.
        try:
            result = await asyncio.wait_for(
                executor.execute(context, step.parameters),
                timeout=self._step_timeout,
            )
            # Guarantee step_id is always set correctly (defensive — executor should set it).
            if result.step_id != step.id:
                result = result.model_copy(update={"step_id": step.id})
            return result

        except asyncio.TimeoutError:
            duration_ms = self._step_timeout * 1000
            self._logger.warning(
                "Step timeout",
                plan_id=plan_id_str,
                step_id=step.id,
                action=step.action,
                timeout_seconds=self._step_timeout,
            )
            return ActionResult(
                step_id=step.id,
                success=False,
                message=f"Step timed out after {self._step_timeout:.0f}s.",
                error_code=ErrorCode.TIMEOUT,
                duration_ms=duration_ms,
            )

        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - step_start) * 1000
            self._logger.error(
                "Unexpected executor error",
                plan_id=plan_id_str,
                step_id=step.id,
                action=step.action,
                error=str(exc),
                exc_type=type(exc).__name__,
            )
            return ActionResult(
                step_id=step.id,
                success=False,
                message=f"Unexpected error in executor: {exc}",
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=duration_ms,
            )
