"""API Schemas — definitions for HTTP request and response bodies.

Matches the Sprint 002 specification for /execute.
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
