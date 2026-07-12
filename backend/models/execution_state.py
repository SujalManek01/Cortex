"""Execution state — maintained separately from ActionPlan.

Engineering Rule 4: Execution state is separate from ActionPlan.
ActionPlan is frozen and immutable. PlanExecutionState is the mutable
runtime record that tracks what actually happened.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from backend.models.action_result import ActionResult


class ExecutionState(str, Enum):
    """Lifecycle states for step and plan execution.

    Using str as base ensures JSON-serializable values.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanExecutionState(BaseModel):
    """Mutable runtime state of a plan execution.

    This is the response payload returned to the frontend after execution.
    Never mixed into or derived from the ActionPlan itself.
    """

    plan_id: uuid.UUID
    status: ExecutionState
    current_step_id: str | None = None
    step_results: list[ActionResult] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
