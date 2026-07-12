"""PlanValidator — validates ActionPlan schema, version, and supported actions.

From the spec, the Validator checks:
  - Schema completeness
  - Version (unknown versions rejected)
  - Supported actions (must exist in registry)
  - Parameter types

Refinement 4: ActionRegistry is injected via constructor.
"""
from __future__ import annotations

from backend.models.action_plan import ActionPlan
from backend.models.error_codes import ErrorCode
from backend.registry.action_registry import ActionRegistry

# The only ActionPlan version supported in Sprint 1.
SUPPORTED_VERSIONS: frozenset[str] = frozenset({"1.0"})


class ValidationError(Exception):
    """Raised when an ActionPlan fails validation.

    Always carries a structured error_code for API response mapping.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code


class PlanValidator:
    """Validates ActionPlans before they reach the safety policy or engine.

    Validation is ordered: schema → version → steps.
    First failure raises immediately (fail-fast).

    Refinement 4: ActionRegistry injected via constructor.
    """

    def __init__(self, registry: ActionRegistry) -> None:
        self._registry = registry

    def validate(self, plan: ActionPlan) -> None:
        """Validate the ActionPlan. Raises ValidationError on any failure.

        Args:
            plan: The ActionPlan produced by the planner.

        Raises:
            ValidationError: With a descriptive message and structured error_code.
        """
        self._check_schema(plan)
        self._check_version(plan)
        self._check_steps(plan)

    # ── Private checks ─────────────────────────────────────────────────────────

    def _check_schema(self, plan: ActionPlan) -> None:
        """Verify required top-level fields are present and non-empty."""
        if not plan.steps:
            raise ValidationError(
                "ActionPlan must contain at least one step.",
                error_code=ErrorCode.INVALID_PLAN,
            )
        if not plan.created_by or not plan.created_by.strip():
            raise ValidationError(
                "ActionPlan 'created_by' must not be empty.",
                error_code=ErrorCode.INVALID_PLAN,
            )

    def _check_version(self, plan: ActionPlan) -> None:
        """Reject unknown schema versions. Per spec: 'Unknown versions rejected.'"""
        if plan.version not in SUPPORTED_VERSIONS:
            raise ValidationError(
                f"Unsupported ActionPlan version '{plan.version}'. "
                f"Supported: {sorted(SUPPORTED_VERSIONS)}. "
                "Upgrade your client or use a supported version.",
                error_code=ErrorCode.INVALID_PLAN,
            )

    def _check_steps(self, plan: ActionPlan) -> None:
        """Validate each step: unique IDs, action format, registry membership, params."""
        seen_ids: set[str] = set()

        for step in plan.steps:
            # Step IDs must be unique within the plan.
            if step.id in seen_ids:
                raise ValidationError(
                    f"Duplicate step id '{step.id}' in ActionPlan. "
                    "All step IDs must be unique.",
                    error_code=ErrorCode.INVALID_PLAN,
                )
            seen_ids.add(step.id)

            # Action must be in 'domain.verb' format with exactly one dot.
            parts = step.action.split(".")
            if len(parts) != 2 or not all(parts):
                raise ValidationError(
                    f"Step '{step.id}': action '{step.action}' is not in valid "
                    "'domain.verb' format (e.g. 'application.open').",
                    error_code=ErrorCode.INVALID_PLAN,
                )

            # Action must be registered in the registry.
            if not self._registry.is_registered(step.action):
                raise ValidationError(
                    f"Step '{step.id}': action '{step.action}' is not supported. "
                    f"Registered actions: {self._registry.registered_actions}.",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Parameters must be a dict (Pydantic guarantees this, but belt-and-suspenders).
            if not isinstance(step.parameters, dict):
                raise ValidationError(
                    f"Step '{step.id}': 'parameters' must be a dict, "
                    f"got {type(step.parameters).__name__}.",
                    error_code=ErrorCode.INVALID_PLAN,
                )
