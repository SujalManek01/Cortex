"""FastAPI route handlers for the Cortex execution API.

Endpoints:
  POST /execute  — Submit an ExecuteRequest; returns PlanExecutionState.
  GET  /status   — Return current engine state (idle or running).
  GET  /health   — Liveness check.

All services are retrieved from app.state (set in main.py at startup).
No module-level singletons. Refinement 4: DI via FastAPI app.state.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.engine.execution_engine import ConcurrentExecutionError, ExecutionEngine
from backend.models.execution_state import ExecutionState, PlanExecutionState
from backend.planner.stub_planner import ExecuteRequest, StubPlanner
from backend.safety.safety_policy import SafetyPolicy, SafetyViolation
from backend.validator.validator import PlanValidator, ValidationError

router = APIRouter()


# ── Dependency helpers ─────────────────────────────────────────────────────────

def _planner(request: Request) -> StubPlanner:
    return request.app.state.planner


def _validator(request: Request) -> PlanValidator:
    return request.app.state.validator


def _safety(request: Request) -> SafetyPolicy:
    return request.app.state.safety_policy


def _engine(request: Request) -> ExecutionEngine:
    return request.app.state.engine


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/execute",
    response_model=PlanExecutionState,
    summary="Execute an ActionPlan",
    description=(
        "Accepts a goal and pre-formed steps. "
        "The backend generates plan_id and created_by. "
        "Runs validation → safety check → sequential execution."
    ),
    responses={
        200: {"description": "Plan completed (may include failed steps)."},
        400: {"description": "Validation failed — invalid plan schema or unsupported action."},
        403: {"description": "Safety violation — allow-list or alias policy breached."},
        409: {"description": "Concurrent execution rejected — a plan is already running."},
        500: {"description": "Unexpected internal error."},
    },
)
async def execute_plan(request: Request, body: ExecuteRequest) -> PlanExecutionState:
    """Submit an execution request. Validate, enforce safety, then execute."""
    planner = _planner(request)
    validator = _validator(request)
    safety = _safety(request)
    engine = _engine(request)

    # Step 1: Build ActionPlan (assigns plan_id and created_by).
    plan = planner.plan_from_request(body)

    # Step 2: Validate schema, version, and action registry membership.
    try:
        validator.validate(plan)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={
            "error": "validation_failed",
            "error_code": exc.error_code.value,
            "message": str(exc),
            "plan_id": str(plan.plan_id),
        }) from exc

    # Step 3: Enforce safety policy.
    try:
        safety.enforce(plan)
    except SafetyViolation as exc:
        raise HTTPException(status_code=403, detail={
            "error": "safety_violation",
            "error_code": exc.error_code.value,
            "message": str(exc),
            "plan_id": str(plan.plan_id),
        }) from exc

    # Step 4: Execute.
    try:
        state = await engine.execute(plan)
    except ConcurrentExecutionError as exc:
        raise HTTPException(status_code=409, detail={
            "error": "concurrent_execution",
            "error_code": exc.error_code.value,
            "message": str(exc),
        }) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "message": f"Unexpected engine error: {exc}",
        }) from exc

    return state


@router.get(
    "/status",
    summary="Engine status",
    description="Returns the current engine busy state.",
)
async def get_status(request: Request) -> JSONResponse:
    """Return whether the engine is currently executing a plan."""
    engine = _engine(request)
    return JSONResponse({
        "busy": engine.is_busy,
        "status": "running" if engine.is_busy else "idle",
    })


@router.get(
    "/health",
    summary="Health check",
    description="Liveness probe. Returns 200 if the server is up.",
)
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})
