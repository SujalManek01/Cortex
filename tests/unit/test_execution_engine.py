"""Unit tests: ExecutionEngine.

Uses mock executors to test engine behaviour without OS side-effects:
  - Sequential execution (step order maintained)
  - Stop on failure (remaining steps skipped)
  - ConcurrentExecutionError when lock is held
  - Timeout handling (step exceeds step_timeout_seconds)
  - PlanExecutionState fields populated correctly
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from backend.engine.execution_engine import ConcurrentExecutionError, ExecutionEngine
from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.error_codes import ErrorCode
from backend.models.execution_state import ExecutionState
from backend.registry.action_registry import ActionRegistry
from tests.conftest import make_mock_executor


def build_plan(*actions: str) -> ActionPlan:
    """Build a plan with one step per given action name."""
    return ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Test plan",
        version="1.0",
        created_by="stub_planner",
        steps=[
            ActionStep(id=f"step-{i + 1}", action=action, parameters={})
            for i, action in enumerate(actions)
        ],
    )


def make_engine(
    *actions: str,
    success_map: dict[str, bool] | None = None,
    delay_map: dict[str, float] | None = None,
    timeout: float = 30.0,
    logger=None,
    config=None,
) -> ExecutionEngine:
    """Build an ExecutionEngine with mock executors for each action."""
    success_map = success_map or {}
    delay_map = delay_map or {}
    registry = ActionRegistry()
    for action in actions:
        executor = make_mock_executor(
            action=action,
            success=success_map.get(action, True),
            delay=delay_map.get(action, 0.0),
        )
        registry.register(executor)

    from pathlib import Path
    from types import MappingProxyType
    from backend.config.config_loader import ReadOnlyConfig
    from backend.logging.logger import StructuredLogger
    import tempfile

    if logger is None:
        tmp = tempfile.mkdtemp()
        logger = StructuredLogger(log_path=Path(tmp) / "test.log", echo_stdout=False)
    if config is None:
        from backend.config.config_loader import ReadOnlyConfig
        from types import MappingProxyType
        config = ReadOnlyConfig(_apps=(), _aliases=MappingProxyType({}), _websites=MappingProxyType({}))

    return ExecutionEngine(
        registry=registry,
        logger=logger,
        config=config,
        step_timeout_seconds=timeout,
    )


class TestExecutionEngineSequential:
    async def test_single_step_success(self):
        engine = make_engine("mock.action")
        plan = build_plan("mock.action")
        state = await engine.execute(plan)
        assert state.status == ExecutionState.COMPLETED
        assert len(state.step_results) == 1
        assert state.step_results[0].success is True

    async def test_multi_step_all_success(self):
        engine = make_engine("mock.a", "mock.b", "mock.c")
        plan = build_plan("mock.a", "mock.b", "mock.c")
        state = await engine.execute(plan)
        assert state.status == ExecutionState.COMPLETED
        assert len(state.step_results) == 3
        assert all(r.success for r in state.step_results)

    async def test_step_ids_populated(self):
        engine = make_engine("mock.a", "mock.b")
        plan = build_plan("mock.a", "mock.b")
        state = await engine.execute(plan)
        result_ids = [r.step_id for r in state.step_results]
        assert result_ids == ["step-1", "step-2"]

    async def test_started_at_and_finished_at_set(self):
        engine = make_engine("mock.a")
        plan = build_plan("mock.a")
        state = await engine.execute(plan)
        assert state.started_at is not None
        assert state.finished_at is not None
        assert state.finished_at >= state.started_at

    async def test_plan_id_preserved_in_state(self):
        engine = make_engine("mock.a")
        plan = build_plan("mock.a")
        state = await engine.execute(plan)
        assert state.plan_id == plan.plan_id


class TestExecutionEngineStopOnFailure:
    async def test_stop_on_first_failure(self):
        """If step-2 fails, step-3 must NOT be executed."""
        engine = make_engine(
            "mock.a", "mock.b", "mock.c",
            success_map={"mock.a": True, "mock.b": False, "mock.c": True},
        )
        plan = build_plan("mock.a", "mock.b", "mock.c")
        state = await engine.execute(plan)

        assert state.status == ExecutionState.FAILED
        # Only 2 results — step 3 was skipped.
        assert len(state.step_results) == 2
        assert state.step_results[0].success is True
        assert state.step_results[1].success is False

    async def test_first_step_failure_stops_immediately(self):
        engine = make_engine(
            "mock.a", "mock.b",
            success_map={"mock.a": False, "mock.b": True},
        )
        plan = build_plan("mock.a", "mock.b")
        state = await engine.execute(plan)

        assert state.status == ExecutionState.FAILED
        assert len(state.step_results) == 1


class TestExecutionEngineConcurrency:
    async def test_concurrent_execution_rejected(self, test_logger, test_config):
        """Submitting a second plan while one is running must raise ConcurrentExecutionError."""
        # Create a slow executor that takes 0.5s.
        slow_engine = make_engine("mock.slow", delay_map={"mock.slow": 0.5})
        plan = build_plan("mock.slow")

        # Start first execution in background.
        task = asyncio.create_task(slow_engine.execute(plan))
        await asyncio.sleep(0.05)  # Let the first plan start and acquire the lock.

        # Attempt concurrent execution.
        with pytest.raises(ConcurrentExecutionError) as exc_info:
            await slow_engine.execute(plan)
        assert exc_info.value.error_code == ErrorCode.CONCURRENT_EXECUTION

        # Clean up.
        await task

    async def test_engine_available_after_completion(self):
        """Engine must accept a new plan after the previous one completes."""
        engine = make_engine("mock.a")
        plan = build_plan("mock.a")

        state1 = await engine.execute(plan)
        assert state1.status == ExecutionState.COMPLETED

        # Should not raise.
        state2 = await engine.execute(plan)
        assert state2.status == ExecutionState.COMPLETED

    async def test_is_busy_during_execution(self):
        slow_engine = make_engine("mock.slow", delay_map={"mock.slow": 0.5})
        plan = build_plan("mock.slow")

        task = asyncio.create_task(slow_engine.execute(plan))
        await asyncio.sleep(0.05)

        assert slow_engine.is_busy is True

        await task
        assert slow_engine.is_busy is False


class TestExecutionEngineTimeout:
    async def test_step_timeout_produces_timeout_result(self):
        """A step that takes longer than the timeout must produce a TIMEOUT error result."""
        # Engine with 0.1s timeout; executor sleeps for 0.5s.
        engine = make_engine("mock.slow", delay_map={"mock.slow": 0.5}, timeout=0.1)
        plan = build_plan("mock.slow")
        state = await engine.execute(plan)

        assert state.status == ExecutionState.FAILED
        assert state.step_results[0].error_code == ErrorCode.TIMEOUT
        assert state.step_results[0].success is False

    async def test_timeout_stops_plan(self):
        """A timed-out step must halt the plan — subsequent steps must not run."""
        engine = make_engine("mock.slow", "mock.fast",
                             delay_map={"mock.slow": 0.5, "mock.fast": 0.0},
                             timeout=0.1)
        plan = build_plan("mock.slow", "mock.fast")
        state = await engine.execute(plan)

        assert state.status == ExecutionState.FAILED
        assert len(state.step_results) == 1  # Only the timed-out step.
        assert state.step_results[0].error_code == ErrorCode.TIMEOUT
