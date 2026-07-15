"""API Schemas — definitions for HTTP request and response bodies.

Matches the Sprint 002 specification for /execute.
Sprint 003 additions: CommandRequest, PlanResponse, PlanningErrorResponse.
"""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ── Requests ───────────────────────────────────────────────────────────────────

class ExecuteStepRequest(BaseModel):
    capability: str
    target: str

class ExecutePlanRequest(BaseModel):
    steps: list[ExecuteStepRequest] = Field(min_length=1)

class ExecuteRequest(BaseModel):
    version: str = Field(default="1.0")
    plan: ExecutePlanRequest

# ── Sprint 003: Natural Language request ───────────────────────────────────────

class CommandRequest(BaseModel):
    """Request body for POST /plan and POST /command endpoints."""
    command: str = Field(
        min_length=1,
        max_length=500,
        description="Natural language command. Example: 'Open Chrome and GitHub'.",
    )

# ── Sprint 003: Planning response schemas ──────────────────────────────────────

from backend.models.planner_result import PlannerWarning, PlannerInfo, PlannerDiagnostics


class PlanStepSchema(BaseModel):
    """A single planned step — serializable form sent to the frontend."""
    id: str
    capability: str
    target: str

class PlanningErrorResponse(BaseModel):
    """Structured error returned by /plan when planning fails."""
    error_code: str
    message: str

class PlanResponse(BaseModel):
    """Response body for POST /plan."""
    success: bool
    planner: str
    confidence: float
    normalized_input: str
    warnings: list[PlannerWarning] = Field(default_factory=list)
    information: list[PlannerInfo] = Field(default_factory=list)
    diagnostics: PlannerDiagnostics | None = None
    planning_time_ms: float
    token_count: int
    step_count: int
    steps: list[PlanStepSchema] = Field(default_factory=list)
    error: PlanningErrorResponse | None = None

# ── Responses ──────────────────────────────────────────────────────────────────

class ExecutionSummary(BaseModel):
    successful: int
    failed: int
    total: int
    duration_ms: int = Field(default=0, alias="duration") # Support mapping internally

    model_config = ConfigDict(populate_by_name=True)

class ExecutionResultSchema(BaseModel):
    step: int
    capability: str
    target: str
    status: str
    duration_ms: int = Field(default=0, alias="duration")
    error: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)

class ExecuteResponse(BaseModel):
    execution_id: uuid.UUID
    status: str
    duration_ms: int = Field(default=0)
    summary: ExecutionSummary
    results: list[ExecutionResultSchema]
