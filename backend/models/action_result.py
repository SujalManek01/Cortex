"""ActionResult — the structured result returned by every executor.

Engineering Rule 7: Every executor returns ActionResult.
All failures are structured — no unhandled exceptions propagate from executors.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.error_codes import ErrorCode


class ActionResult(BaseModel):
    """Structured result of a single action step execution.

    Executors must always return an ActionResult — never raise.
    The engine appends step_id from the ActionStep after executor returns.
    """

    step_id: str = Field(description="The step ID this result corresponds to.")
    success: bool = Field(description="True if the step completed successfully.")
    message: str = Field(description="Human-readable outcome description.")
    error_code: ErrorCode | None = Field(
        default=None,
        description="Structured error code. Present only on failure.",
    )
    duration_ms: float = Field(
        description="Wall-clock time taken to execute this step, in milliseconds."
    )
    metadata: dict[str, object] = Field(
        default_factory=dict,
        description="Executor-specific supplemental data (e.g. launched process path).",
    )
