"""Shared pytest fixtures for all Cortex tests.

Fixtures are scoped as narrowly as possible to avoid test interdependence.
All fixtures use in-memory or temporary resources — no disk I/O to real config files.

Test configuration:
  - apps.json equivalent: two apps registered (vscode, notepad).
  - aliases.json equivalent: two aliases registered (desktop, chatbot_project).
  - A real ActionRegistry with three executors registered.
  - Tests that need mocked executors override the registry fixture locally.
"""
from __future__ import annotations

import asyncio
import uuid
from types import MappingProxyType
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from backend.config.config_loader import AppEntry, ReadOnlyConfig
from backend.engine.execution_engine import ExecutionEngine
from backend.executors.application_close import ApplicationCloseExecutor
from backend.executors.application_open import ApplicationOpenExecutor
from backend.executors.folder_open import FolderOpenExecutor
from backend.logging.logger import StructuredLogger
from backend.models.action_context import ActionContext, WorkspaceMetadata
from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode
from backend.schemas.api import ExecuteRequest, ExecuteStepRequest  # noqa: F401 – exported for test modules
from backend.registry.action_registry import ActionRegistry


# ── Config fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def test_apps() -> tuple[AppEntry, ...]:
    """A minimal set of registered apps for testing."""
    return (
        AppEntry(name="VS Code", alias="vscode", executable="Code.exe", path="C:\\fake\\Code.exe"),
        AppEntry(name="Notepad", alias="notepad", executable="notepad.exe", path="C:\\Windows\\System32\\notepad.exe"),
        AppEntry(name="Google Chrome", alias="chrome", executable="chrome.exe", path="C:\\fake\\chrome.exe"),
    )


@pytest.fixture
def test_aliases() -> MappingProxyType:
    """A minimal set of folder aliases for testing."""
    return MappingProxyType({
        "desktop": "C:\\Users\\testuser\\Desktop",
        "chatbot_project": "C:\\Users\\testuser\\Projects\\chatbot",
        "downloads": "C:\\Users\\testuser\\Downloads",
    })


@pytest.fixture
def test_config(test_apps, test_aliases) -> ReadOnlyConfig:
    """ReadOnlyConfig pre-populated with test apps and aliases."""
    return ReadOnlyConfig(_apps=test_apps, _aliases=test_aliases, _websites=MappingProxyType({}))


# ── Logger fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_logger(tmp_path) -> StructuredLogger:
    """StructuredLogger writing to a temp file, no stdout echo."""
    return StructuredLogger(log_path=tmp_path / "test.log", echo_stdout=False)


# ── Registry fixture ───────────────────────────────────────────────────────────

@pytest.fixture
def real_registry() -> ActionRegistry:
    """ActionRegistry with all three Sprint 1 executors registered."""
    registry = ActionRegistry()
    registry.register(ApplicationOpenExecutor())
    registry.register(ApplicationCloseExecutor())
    registry.register(FolderOpenExecutor())
    return registry


@pytest.fixture
def empty_registry() -> ActionRegistry:
    """An ActionRegistry with no executors registered."""
    return ActionRegistry()


# ── Engine fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_engine(real_registry, test_logger, test_config) -> ExecutionEngine:
    """ExecutionEngine wired with real registry, test config, and short timeout for tests."""
    return ExecutionEngine(
        registry=real_registry,
        logger=test_logger,
        config=test_config,
        step_timeout_seconds=30.0,
    )


@pytest.fixture
def fast_timeout_engine(real_registry, test_logger, test_config) -> ExecutionEngine:
    """ExecutionEngine with a very short timeout for testing timeout behaviour."""
    return ExecutionEngine(
        registry=real_registry,
        logger=test_logger,
        config=test_config,
        step_timeout_seconds=0.1,
    )


# ── Plan fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_plan_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def valid_open_plan(sample_plan_id) -> ActionPlan:
    """A valid ActionPlan that opens notepad (always available on Windows)."""
    return ActionPlan(
        plan_id=sample_plan_id,
        goal="Open Notepad",
        version="1.0",
        created_by="stub_planner",
        steps=[
            ActionStep(id="step-1", action="application.open", parameters={"app": "notepad"}),
        ],
    )


@pytest.fixture
def multi_step_plan(sample_plan_id) -> ActionPlan:
    """A two-step plan: open vscode then notepad."""
    return ActionPlan(
        plan_id=sample_plan_id,
        goal="Open VS Code and Notepad",
        version="1.0",
        created_by="stub_planner",
        steps=[
            ActionStep(id="step-1", action="application.open", parameters={"app": "vscode"}),
            ActionStep(id="step-2", action="application.open", parameters={"app": "notepad"}),
        ],
    )


# ── ActionContext fixture ──────────────────────────────────────────────────────

@pytest.fixture
def test_context(test_logger, test_config, sample_plan_id) -> ActionContext:
    """ActionContext suitable for unit-testing individual executors."""
    return ActionContext(
        logger=test_logger,
        config=test_config,
        workspace=WorkspaceMetadata(
            plan_id=sample_plan_id,
            goal="Test goal",
            version="1.0",
            step_id="step-1",
        ),
    )


# ── HTTP test client ───────────────────────────────────────────────────────────

@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client backed by the FastAPI ASGI app (no real network).

    Manually invokes the FastAPI lifespan context so app.state is fully
    populated (planner, engine, registry, etc.) before any request is made.
    """
    from backend.main import app

    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client


# ── Mock executor helpers ──────────────────────────────────────────────────────

def make_mock_executor(action: str, success: bool = True, delay: float = 0.0) -> MagicMock:
    """Create a mock BaseExecutor for a given action name."""
    executor = MagicMock()
    executor.action_name = action

    async def _execute(context, parameters):
        if delay:
            await asyncio.sleep(delay)
        return ActionResult(
            step_id=context.workspace.step_id,
            success=success,
            message="Mock success" if success else "Mock failure",
            error_code=None if success else ErrorCode.LAUNCH_FAILURE,
            duration_ms=delay * 1000,
        )

    executor.execute = _execute
    return executor
