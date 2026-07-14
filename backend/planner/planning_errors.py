"""PlanningError — exception hierarchy for the Natural Language Planning Engine.

Sprint 003: Deterministic Rule Planner.

All planner errors carry a structured error_code drawn from PlannerErrorCode.
No internal details are exposed to callers beyond the structured fields.
"""
from __future__ import annotations

from enum import StrEnum


class PlannerErrorCode(StrEnum):
    """Standardised error codes for every planning failure.

    These map directly to HTTP 400 responses from the /plan and /command endpoints.
    """

    EMPTY_COMMAND      = "EMPTY_COMMAND"       # No command supplied
    UNKNOWN_INTENT     = "UNKNOWN_INTENT"       # Verb not in supported set
    UNKNOWN_TARGET     = "UNKNOWN_TARGET"       # Resource not found in any registry
    AMBIGUOUS_TARGET   = "AMBIGUOUS_TARGET"     # Target found in multiple registries
    MIXED_INTENTS      = "MIXED_INTENTS"        # Multiple canonical intents in one command
    TOKENIZATION_ERROR = "TOKENIZATION_ERROR"   # Invalid lexical input
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR" # Failed normalization
    COMMAND_TOO_LONG   = "COMMAND_TOO_LONG"     # Input exceeds 500-character limit


class PlanningError(Exception):
    """Raised by any planning stage when it cannot produce a valid plan.

    Always carries a PlannerErrorCode for structured API responses.
    Never exposes internal stack traces.
    """

    def __init__(self, message: str, error_code: PlannerErrorCode) -> None:
        super().__init__(message)
        self.error_code = error_code

    def __repr__(self) -> str:
        return f"PlanningError({self.error_code}: {self})"
