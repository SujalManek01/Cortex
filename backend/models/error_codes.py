"""Canonical error codes for structured error handling in Cortex.

Every failure produced by the engine, validator, safety policy, or
executors is identified by one of these codes. Using str as the enum
base ensures JSON-serializable values without extra conversion.
"""
from enum import Enum


class ErrorCode(str, Enum):
    """All structured error codes produced by the Cortex execution engine.

    These codes appear in ActionResult.error_code and HTTP error responses.
    """

    UNKNOWN_APPLICATION = "unknown_application"
    INVALID_ALIAS = "invalid_alias"
    INVALID_PLAN = "invalid_plan"
    TIMEOUT = "timeout"
    LAUNCH_FAILURE = "launch_failure"
    VALIDATION_ERROR = "validation_error"
    SAFETY_VIOLATION = "safety_violation"
    CONCURRENT_EXECUTION = "concurrent_execution"
