"""Acceptance tests — SPR-001 Definition of Done.

These 8 tests map directly to the acceptance criteria in
docs/specifications/SPR-001-Core-Execution-Engine.md:

  1. Open VS Code
  2. Open Chrome
  3. Open chatbot project folder
  4. Invalid application rejected
  5. Invalid ActionPlan rejected
  6. Partial failure stops execution
  7. Concurrent execution rejected
  8. Timeout handled

Tests 1–3 are marked @pytest.mark.acceptance because they launch real OS
applications on Windows. They are SKIPPED by default (see pyproject.toml
addopts: -m 'not acceptance').

To run acceptance tests:
  cd backend
  pytest ../tests/integration/test_acceptance.py -m acceptance -v

Tests 4–8 test rejection/failure behaviour. They do not launch real
applications and run in the standard test suite.
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.config.config_loader import AppEntry, ReadOnlyConfig
from backend.engine.execution_engine import ConcurrentExecutionError, ExecutionEngine
from backend.executors.application_close import ApplicationCloseExecutor
from backend.executors.application_open import ApplicationOpenExecutor
from backend.executors.folder_open import FolderOpenExecutor
from backend.logging.logger import StructuredLogger
from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode
from backend.models.execution_state import ExecutionState
from backend.planner.stub_planner import ExecuteRequest, ExecuteStepRequest, StubPlanner
from backend.registry.action_registry import ActionRegistry
from backend.safety.safety_policy import SafetyPolicy, SafetyViolation
from backend.validator.validator import PlanValidator, ValidationError
from tests.conftest import make_mock_executor


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _make_real_config(tmp_path: Path) -> ReadOnlyConfig:
    """Config with real-ish app paths for acceptance tests."""
    import os
    username = os.environ.get("USERNAME", "user")
    return ReadOnlyConfig(
        _apps=(
            AppEntry("VS Code", "vscode", "Code.exe",
                     rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe"),
            AppEntry("Google Chrome", "chrome", "chrome.exe",
                     r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            AppEntry("Notepad", "notepad", "notepad.exe",
                     r"C:\Windows\System32\notepad.exe"),
        ),
        _aliases=MappingProxyType({
            "chatbot_project": rf"C:\Users\{username}\Projects\chatbot",
            "desktop": rf"C:\Users\{username}\Desktop",
        }),
    )


def _make_full_engine(config: ReadOnlyConfig, logger: StructuredLogger) -> tuple[
    ExecutionEngine, PlanValidator, SafetyPolicy
]:
    """Wire up a complete engine with real executors."""
    registry = ActionRegistry()
    registry.register(ApplicationOpenExecutor())
    registry.register(ApplicationCloseExecutor())
    registry.register(FolderOpenExecutor())
    engine = ExecutionEngine(registry=registry, logger=logger, config=config, step_timeout_seconds=30.0)
    validator = PlanValidator(registry=registry)
    safety = SafetyPolicy(config=config)
    return engine, validator, safety


# ────────────────────────────────────────────────────────────────────────────────
# Acceptance Tests 1–3: Real OS execution (marked @acceptance, skipped by default)
# ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.acceptance
async def test_ac1_open_vscode(tmp_path: Path):
    """AC-1: Cortex successfully opens VS Code."""
    config = _make_real_config(tmp_path)
    logger = StructuredLogger(tmp_path / "test.log", echo_stdout=False)
    engine, validator, safety = _make_full_engine(config, logger)

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Open VS Code",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="application.open", parameters={"app": "vscode"})],
    )

    validator.validate(plan)
    safety.enforce(plan)
    state = await engine.execute(plan)

    assert state.status == ExecutionState.COMPLETED
    assert state.step_results[0].success is True


@pytest.mark.acceptance
async def test_ac2_open_chrome(tmp_path: Path):
    """AC-2: Cortex successfully opens Chrome."""
    config = _make_real_config(tmp_path)
    logger = StructuredLogger(tmp_path / "test.log", echo_stdout=False)
    engine, validator, safety = _make_full_engine(config, logger)

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Open Chrome",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="application.open", parameters={"app": "chrome"})],
    )

    validator.validate(plan)
    safety.enforce(plan)
    state = await engine.execute(plan)

    assert state.status == ExecutionState.COMPLETED
    assert state.step_results[0].success is True


@pytest.mark.acceptance
async def test_ac3_open_chatbot_project(tmp_path: Path):
    """AC-3: Cortex successfully opens the chatbot project folder."""
    import os
    username = os.environ.get("USERNAME", "user")
    project_path = Path(rf"C:\Users\{username}\Projects\chatbot")
    project_path.mkdir(parents=True, exist_ok=True)  # Ensure it exists for test.

    config = _make_real_config(tmp_path)
    logger = StructuredLogger(tmp_path / "test.log", echo_stdout=False)
    engine, validator, safety = _make_full_engine(config, logger)

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Open chatbot project folder",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="folder.open", parameters={"alias": "chatbot_project"})],
    )

    validator.validate(plan)
    safety.enforce(plan)
    state = await engine.execute(plan)

    assert state.status == ExecutionState.COMPLETED
    assert state.step_results[0].success is True


# ────────────────────────────────────────────────────────────────────────────────
# Acceptance Test 4: Invalid application rejected (runs in standard suite)
# ────────────────────────────────────────────────────────────────────────────────

async def test_ac4_invalid_application_rejected(tmp_path: Path, real_registry, test_config):
    """AC-4: An unregistered application is rejected before reaching the engine."""
    safety = SafetyPolicy(config=test_config)

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Open a dangerous app",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="application.open", parameters={"app": "virus.exe"})],
    )

    with pytest.raises(SafetyViolation) as exc_info:
        safety.enforce(plan)

    assert exc_info.value.error_code == ErrorCode.SAFETY_VIOLATION
    assert "virus.exe" in str(exc_info.value)


# ────────────────────────────────────────────────────────────────────────────────
# Acceptance Test 5: Invalid ActionPlan rejected (runs in standard suite)
# ────────────────────────────────────────────────────────────────────────────────

async def test_ac5_invalid_plan_rejected(real_registry):
    """AC-5: A malformed ActionPlan (unknown version) is rejected by the Validator."""
    validator = PlanValidator(registry=real_registry)

    bad_plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Something",
        version="99.0",  # Unknown version
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="application.open", parameters={"app": "notepad"})],
    )

    with pytest.raises(ValidationError) as exc_info:
        validator.validate(bad_plan)

    assert exc_info.value.error_code == ErrorCode.INVALID_PLAN
    assert "99.0" in str(exc_info.value)


async def test_ac5b_plan_with_unknown_action_rejected(real_registry):
    """AC-5 variant: Plan referencing an unregistered action is rejected."""
    validator = PlanValidator(registry=real_registry)

    bad_plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Browse the web",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="browser.open", parameters={"url": "https://x.com"})],
    )

    with pytest.raises(ValidationError) as exc_info:
        validator.validate(bad_plan)

    assert "browser.open" in str(exc_info.value)


# ────────────────────────────────────────────────────────────────────────────────
# Acceptance Test 6: Partial failure stops execution (runs in standard suite)
# ────────────────────────────────────────────────────────────────────────────────

async def test_ac6_partial_failure_stops_execution(test_logger, test_config):
    """AC-6: If step 2 fails, step 3 must NOT execute."""
    registry = ActionRegistry()
    registry.register(make_mock_executor("mock.a", success=True))
    registry.register(make_mock_executor("mock.b", success=False))
    registry.register(make_mock_executor("mock.c", success=True))

    engine = ExecutionEngine(
        registry=registry,
        logger=test_logger,
        config=test_config,
        step_timeout_seconds=5.0,
    )

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Three steps, second fails",
        version="1.0",
        created_by="stub_planner",
        steps=[
            ActionStep(id="step-1", action="mock.a", parameters={}),
            ActionStep(id="step-2", action="mock.b", parameters={}),
            ActionStep(id="step-3", action="mock.c", parameters={}),
        ],
    )

    state = await engine.execute(plan)

    assert state.status == ExecutionState.FAILED
    assert len(state.step_results) == 2          # step-3 was never executed
    assert state.step_results[0].success is True
    assert state.step_results[1].success is False


# ────────────────────────────────────────────────────────────────────────────────
# Acceptance Test 7: Concurrent execution rejected (runs in standard suite)
# ────────────────────────────────────────────────────────────────────────────────

async def test_ac7_concurrent_execution_rejected(test_logger, test_config):
    """AC-7: A second plan submitted while the first is running raises ConcurrentExecutionError."""
    registry = ActionRegistry()
    registry.register(make_mock_executor("mock.slow", success=True, delay=0.3))

    engine = ExecutionEngine(
        registry=registry,
        logger=test_logger,
        config=test_config,
        step_timeout_seconds=5.0,
    )

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Slow plan",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="mock.slow", parameters={})],
    )

    # Start first plan in background.
    first_task = asyncio.create_task(engine.execute(plan))
    await asyncio.sleep(0.05)  # Allow first plan to acquire the lock.

    # Second plan must be rejected.
    with pytest.raises(ConcurrentExecutionError) as exc_info:
        await engine.execute(plan)

    assert exc_info.value.error_code == ErrorCode.CONCURRENT_EXECUTION

    await first_task  # Wait for first plan to finish.


# ────────────────────────────────────────────────────────────────────────────────
# Acceptance Test 8: Timeout handled (runs in standard suite)
# ────────────────────────────────────────────────────────────────────────────────

async def test_ac8_timeout_handled(test_logger, test_config):
    """AC-8: A step exceeding the timeout produces a TIMEOUT error result and halts the plan."""
    registry = ActionRegistry()
    registry.register(make_mock_executor("mock.slow", success=True, delay=1.0))

    engine = ExecutionEngine(
        registry=registry,
        logger=test_logger,
        config=test_config,
        step_timeout_seconds=0.1,  # Very short timeout for test.
    )

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Timeout test",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="mock.slow", parameters={})],
    )

    state = await engine.execute(plan)

    assert state.status == ExecutionState.FAILED
    assert len(state.step_results) == 1
    assert state.step_results[0].success is False
    assert state.step_results[0].error_code == ErrorCode.TIMEOUT
    assert state.step_results[0].step_id == "step-1"
