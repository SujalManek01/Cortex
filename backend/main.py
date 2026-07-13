"""Cortex backend — FastAPI application entry point.

This module is responsible for:
1. Wiring all services together (Refinement 4: constructor dependency injection).
2. Registering all executors with the ActionRegistry.
3. Configuring CORS for the Vite dev server.
4. Attaching all services to app.state for route access.
5. Exposing the ASGI app for uvicorn.

To add a new executor in future sprints:
  1. Create the executor class in backend/executors/.
  2. Import it here.
  3. Register it: registry.register(MyNewExecutor()).
  No other files need to change.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config.config_loader import ConfigLoader
from backend.engine.execution_engine import ExecutionEngine
from backend.executors.application_close import ApplicationCloseExecutor
from backend.executors.application_open import ApplicationOpenExecutor
from backend.executors.folder_open import FolderOpenExecutor
from backend.executors.website_open import WebsiteOpenExecutor
from backend.logging.logger import StructuredLogger
from backend.planner.stub_planner import StubPlanner
from backend.registry.action_registry import ActionRegistry
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry
from backend.safety.safety_policy import SafetyPolicy
from backend.validator.validator import PlanValidator

# ── Paths ──────────────────────────────────────────────────────────────────────
# Resolve paths relative to this file so the app works from any CWD.
_BACKEND_DIR = Path(__file__).parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"
_LOG_PATH = _PROJECT_ROOT / "logs" / "cortex.log"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build and wire all services at startup. Tear down (future) at shutdown."""

    # ── 1. Infrastructure ──────────────────────────────────────────────────────
    logger = StructuredLogger(log_path=_LOG_PATH, echo_stdout=True)
    logger.info("Cortex starting up", config_dir=str(_CONFIG_DIR))

    config_loader = ConfigLoader(config_dir=_CONFIG_DIR)
    config = config_loader.load()

    logger.info(
        "Config loaded",
        apps_registered=len(config.all_apps),
        aliases_registered=len(config.all_aliases),
        discovered_apps=[a.alias for a in config.all_apps if a.path],
    )

    # ── 2. Sprint 002 Specialized Registries (created before executors for DI) ────
    app_registry = ApplicationRegistry(config)
    folder_registry = FolderRegistry(config)
    website_registry = WebsiteRegistry(config)

    # ── 3. Action Registry + Executors ───────────────────────────────────────
    # Engineering Rule: Engine never contains action-specific conditionals.
    # Adding a new executor = create class + register here.
    registry = ActionRegistry()
    registry.register(ApplicationOpenExecutor())
    registry.register(ApplicationCloseExecutor())
    registry.register(FolderOpenExecutor())
    registry.register(WebsiteOpenExecutor(registry=website_registry))

    logger.info("Executors registered", actions=registry.registered_actions)

    # ── 3. Validation + Safety ────────────────────────────────────────────────
    validator = PlanValidator(registry=registry)
    safety_policy = SafetyPolicy(config=config)

    # ── 4. Planner ────────────────────────────────────────────────────────────
    planner = StubPlanner()

    # ── 5. Engine ─────────────────────────────────────────────────────────────
    engine = ExecutionEngine(
        registry=registry,
        logger=logger,
        config=config,
        step_timeout_seconds=30.0,
    )

    # ── 6. Attach to app.state for route access ────────────────────────────────
    app.state.logger = logger
    app.state.config = config
    app.state.registry = registry
    app.state.app_registry = app_registry
    app.state.folder_registry = folder_registry
    app.state.website_registry = website_registry
    app.state.planner = planner
    app.state.validator = validator
    app.state.safety_policy = safety_policy
    app.state.engine = engine

    logger.info("Cortex ready", registered_actions=registry.registered_actions)

    yield  # Application runs here.

    logger.info("Cortex shutting down")


# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Cortex",
    description=(
        "An AI operating layer that converts natural language into "
        "safe, deterministic computer actions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow the Vite dev server and any localhost origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)
