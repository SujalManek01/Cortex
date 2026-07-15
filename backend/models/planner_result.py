"""PlannerResult — universal contract between every planner and the execution pipeline.

Sprint 003: Every planner (RulePlanner, future AI planners) returns PlannerResult.
The Execution Engine only ever sees the ActionPlan inside; it never knows which
planner produced it.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.action_plan import ActionPlan



class PlannerWarning(BaseModel):
    """Structured warning returned by the planner."""
    code: str
    message: str


class PlannerInfo(BaseModel):
    """Structured informational log returned by the planner."""
    message: str


class PlannerDiagnostics(BaseModel):
    """Detailed performance and structure diagnostics for the planning run."""
    planning_time_ms: float = Field(default=0.0, ge=0.0)
    token_count: int = Field(default=0, ge=0)
    clause_count: int = Field(default=0, ge=0)
    intent_group_count: int = Field(default=0, ge=0)
    resolved_target_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)


class PlannerResult(BaseModel):
    """Structured output from any BasePlanner implementation.

    Fields
    ------
    success
        True if planning succeeded and plan is non-None.
    plan
        The generated ActionPlan, or None on failure.
    normalized_input
        The command string after tokenization and normalization.
    confidence
        1.0 for deterministic rule-based planning; intermediate values
        reserved for future AI planners.
    warnings
        Structured warnings (e.g. duplicate targets).
    information
        Structured informational messages (e.g. verb scope expansion details).
    diagnostics
        Detailed metrics and performance timings for the planning run.
    planning_time_ms
        Wall-clock time consumed by the full planning pipeline (for compatibility).
    token_count
        Number of lexical tokens in the normalized command (for compatibility).
    step_count
        Number of ActionSteps in the generated plan (0 on failure) (for compatibility).
    planner_name
        Identifier of the planner that produced this result.
    error_code
        PlannerErrorCode string on failure; None on success.
    error_message
        Human-readable description of the failure; None on success.
    """

    success: bool

    plan: ActionPlan | None = None

    normalized_input: str = Field(default="")

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    warnings: list[PlannerWarning] = Field(default_factory=list)

    information: list[PlannerInfo] = Field(default_factory=list)

    diagnostics: PlannerDiagnostics | None = None

    planning_time_ms: float = Field(default=0.0, ge=0.0)

    token_count: int = Field(default=0, ge=0)

    step_count: int = Field(default=0, ge=0)

    planner_name: str = Field(default="")

    error_code: str | None = None

    error_message: str | None = None

