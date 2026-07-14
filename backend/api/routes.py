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
from backend.planner.planning_errors import PlanningError
from backend.planner.rule_planner import RulePlanner
from backend.planner.stub_planner import StubPlanner
from backend.registry.action_registry import ActionRegistry
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry
from backend.safety.safety_policy import SafetyPolicy, SafetyViolation
from backend.schemas.api import (
    CommandRequest,
    ExecuteRequest,
    ExecuteResponse,
    ExecutionResultSchema,
    ExecutionSummary,
    PlanningErrorResponse,
    PlanResponse,
    PlanStepSchema,
)
from backend.validator.validator import PlanValidator, ValidationError

router = APIRouter()


# ── Dependency helpers ─────────────────────────────────────────────────────────

def _planner(request: Request) -> StubPlanner:
    return request.app.state.planner


def _rule_planner(request: Request) -> RulePlanner:
    return request.app.state.rule_planner


def _validator(request: Request) -> PlanValidator:
    return request.app.state.validator


def _safety(request: Request) -> SafetyPolicy:
    return request.app.state.safety_policy


def _engine(request: Request) -> ExecutionEngine:
    return request.app.state.engine


def _app_registry(request: Request) -> ApplicationRegistry:
    return request.app.state.app_registry


def _folder_registry(request: Request) -> FolderRegistry:
    return request.app.state.folder_registry


def _website_registry(request: Request) -> WebsiteRegistry:
    return request.app.state.website_registry


def _action_registry(request: Request) -> ActionRegistry:
    return request.app.state.registry


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/execute",
    response_model=ExecuteResponse,
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
async def execute_plan(request: Request, body: ExecuteRequest) -> ExecuteResponse:
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

    # Step 5: Map to Sprint 002 ExecuteResponse API contract.
    successful = sum(1 for r in state.step_results if r.success)
    failed = sum(1 for r in state.step_results if not r.success)
    duration = 0
    if state.started_at and state.finished_at:
        duration = int((state.finished_at - state.started_at).total_seconds() * 1000)

    results = []
    for i, res in enumerate(state.step_results):
        step_def = next((s for s in plan.steps if s.id == res.step_id), None)
        capability = step_def.action if step_def else ""
        target = ""
        if step_def:
            target = step_def.parameters.get("target") or step_def.parameters.get("app") or step_def.parameters.get("alias") or step_def.parameters.get("url") or ""
            
        error_dict = None
        if not res.success:
            error_dict = {
                "code": res.error_code.value if res.error_code else "INTERNAL_ERROR",
                "message": res.message
            }
            
        results.append(ExecutionResultSchema(
            step=i + 1,
            capability=capability,
            target=str(target),
            status="success" if res.success else "failed",
            duration=int(res.duration_ms),
            error=error_dict
        ))

    return ExecuteResponse(
        execution_id=state.plan_id,
        status=state.status.value,
        duration=duration,
        summary=ExecutionSummary(
            successful=successful,
            failed=failed,
            total=len(state.step_results),
            duration=duration,
        ),
        results=results
    )


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


# ── Sprint 003: Natural Language Planning Routes ─────────────────────────────────

@router.post(
    "/plan",
    response_model=PlanResponse,
    summary="Generate an ActionPlan from a natural language command",
    description=(
        "Runs the deterministic planning pipeline "
        "(Tokenizer → Normalizer → IntentDetector → TargetResolver → ActionPlan). "
        "Does NOT execute the plan. Returns the generated plan for user review."
    ),
    responses={
        200: {"description": "Plan generated (success or planning failure both return 200)."},
        422: {"description": "Invalid request body."},
    },
)
async def generate_plan(request: Request, body: CommandRequest) -> PlanResponse:
    """Generate an ActionPlan from a natural language command without executing it."""
    rule_planner = _rule_planner(request)
    result = await rule_planner.plan(body.command)

    if not result.success:
        return PlanResponse(
            success=False,
            planner=result.planner_name,
            confidence=result.confidence,
            normalized_input=result.normalized_input,
            warnings=result.warnings,
            planning_time_ms=result.planning_time_ms,
            token_count=result.token_count,
            step_count=result.step_count,
            steps=[],
            error=PlanningErrorResponse(
                error_code=result.error_code or "UNKNOWN_ERROR",
                message=result.error_message or "Planning failed.",
            ),
        )

    # Serialize steps for the frontend.
    # The frontend uses capability+target to reconstruct ExecuteRequest.
    plan_steps = [
        PlanStepSchema(
            id=step.id,
            capability=step.action,
            target=(
                step.parameters.get("app")
                or step.parameters.get("alias")
                or ""
            ),
        )
        for step in (result.plan.steps if result.plan else [])
    ]

    return PlanResponse(
        success=True,
        planner=result.planner_name,
        confidence=result.confidence,
        normalized_input=result.normalized_input,
        warnings=result.warnings,
        planning_time_ms=result.planning_time_ms,
        token_count=result.token_count,
        step_count=result.step_count,
        steps=plan_steps,
        error=None,
    )


@router.post(
    "/command",
    response_model=ExecuteResponse,
    summary="Plan and execute a natural language command in one request",
    description=(
        "Convenience endpoint for API consumers. "
        "Runs the full pipeline: planning → validation → safety → execution. "
        "The Cortex UI uses POST /plan followed by POST /execute instead."
    ),
    responses={
        200: {"description": "Execution completed."},
        400: {"description": "Planning failed."},
        403: {"description": "Safety violation."},
        422: {"description": "Invalid request body."},
        500: {"description": "Unexpected internal error."},
    },
)
async def execute_command(request: Request, body: CommandRequest) -> ExecuteResponse:
    """Plan then execute a natural language command."""
    rule_planner = _rule_planner(request)
    validator = _validator(request)
    safety = _safety(request)
    engine = _engine(request)

    # Step 1: Plan
    result = await rule_planner.plan(body.command)
    if not result.success or result.plan is None:
        raise HTTPException(status_code=400, detail={
            "error": "planning_failed",
            "error_code": result.error_code or "UNKNOWN_ERROR",
            "message": result.error_message or "Planning failed.",
            "normalized_input": result.normalized_input,
        })

    plan = result.plan

    # Step 2: Validate
    try:
        validator.validate(plan)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={
            "error": "validation_failed",
            "error_code": exc.error_code.value,
            "message": str(exc),
        }) from exc

    # Step 3: Safety
    try:
        safety.enforce(plan)
    except SafetyViolation as exc:
        raise HTTPException(status_code=403, detail={
            "error": "safety_violation",
            "error_code": exc.error_code.value,
            "message": str(exc),
        }) from exc

    # Step 4: Execute
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

    # Step 5: Map to ExecuteResponse
    successful = sum(1 for r in state.step_results if r.success)
    failed = sum(1 for r in state.step_results if not r.success)
    duration = 0
    if state.started_at and state.finished_at:
        duration = int((state.finished_at - state.started_at).total_seconds() * 1000)

    results = []
    for i, res in enumerate(state.step_results):
        step_def = next((s for s in plan.steps if s.id == res.step_id), None)
        capability = step_def.action if step_def else ""
        target = ""
        if step_def:
            target = (
                step_def.parameters.get("app")
                or step_def.parameters.get("alias")
                or ""
            )
        error_dict = None
        if not res.success:
            error_dict = {
                "code": res.error_code.value if res.error_code else "INTERNAL_ERROR",
                "message": res.message,
            }
        results.append(ExecutionResultSchema(
            step=i + 1,
            capability=capability,
            target=str(target),
            status="success" if res.success else "failed",
            duration=int(res.duration_ms),
            error=error_dict,
        ))

    return ExecuteResponse(
        execution_id=state.plan_id,
        status=state.status.value,
        duration=duration,
        summary=ExecutionSummary(
            successful=successful,
            failed=failed,
            total=len(state.step_results),
            duration=duration,
        ),
        results=results,
    )


# ── Sprint 002 Metadata Routes ───────────────────────────────────────────────

@router.get(
    "/applications",
    summary="List registered applications",
    description="Returns all applications known to the Capability Registry.",
)
async def list_applications(request: Request) -> JSONResponse:
    """Return all registered application entries."""
    reg = _app_registry(request)
    return JSONResponse({
        "applications": [
            {"alias": app.alias, "name": app.name, "executable": app.executable or ""}
            for app in reg.all_apps
        ]
    })


@router.get(
    "/folders",
    summary="List registered folder aliases",
    description="Returns all folder aliases known to the Capability Registry.",
)
async def list_folders(request: Request) -> JSONResponse:
    """Return all registered folder alias → path mappings."""
    reg = _folder_registry(request)
    return JSONResponse({
        "folders": [
            {"alias": alias, "path": path}
            for alias, path in reg.all_aliases.items()
        ]
    })


@router.get(
    "/websites",
    summary="List registered website aliases",
    description="Returns all website aliases known to the Capability Registry.",
)
async def list_websites(request: Request) -> JSONResponse:
    """Return all registered website alias → URL mappings."""
    reg = _website_registry(request)
    return JSONResponse({
        "websites": [
            {"alias": alias, "url": url}
            for alias, url in reg.all_websites.items()
        ]
    })


@router.get(
    "/capabilities",
    summary="List registered capabilities",
    description="Returns all capability names currently registered with the engine.",
)
async def list_capabilities(request: Request) -> JSONResponse:
    """Return all registered capability (action) names."""
    reg = _action_registry(request)
    return JSONResponse({"capabilities": reg.registered_actions})
