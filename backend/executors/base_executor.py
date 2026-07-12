"""BaseExecutor — the interface every executor must implement.

Engineering Rules:
  5. Every executor implements one interface.
  6. Every executor receives ActionContext.
  7. Every executor returns ActionResult.

Executors are the only layer that interacts with the operating system.
The engine, registry, validator, and safety policy are all OS-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.action_context import ActionContext
from backend.models.action_result import ActionResult


class BaseExecutor(ABC):
    """Abstract base class for all Cortex action executors.

    Contract:
    - The action_name property must return a stable 'domain.verb' string.
    - execute() must be async and must NEVER raise an unhandled exception.
    - execute() must ALWAYS return an ActionResult (success or failure).
    - Executors must NOT hold mutable state between calls.
    - Executors must NOT import or call OS APIs outside the execute() method.
    """

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Action identifier in 'domain.verb' format, e.g. 'application.open'.

        Must be unique across all registered executors.
        Must be stable — changing it is a breaking change.
        """

    @abstractmethod
    async def execute(
        self,
        context: ActionContext,
        parameters: dict[str, object],
    ) -> ActionResult:
        """Execute the action and return a structured result.

        Args:
            context:    Read-only dependency container (logger, config, workspace).
                        context.workspace.step_id contains the current step ID.
            parameters: Action-specific parameters from the ActionStep.
                        May be empty dict if the action requires no parameters.

        Returns:
            ActionResult. step_id must be set to context.workspace.step_id.
            On failure, error_code must be set to an appropriate ErrorCode.

        Raises:
            Nothing. All errors must be captured and returned as ActionResult.
        """
