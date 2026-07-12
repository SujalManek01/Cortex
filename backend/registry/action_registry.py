"""ActionRegistry — self-registering executor lookup table.

From the spec: "Self-registering executors. Engine never contains
action-specific conditionals."

Executors call registry.register(self) at construction time (wired in main.py).
The engine calls registry.get(action_name) at step execution time.

Refinement 4: ActionRegistry is instantiated once and injected via constructor
into the engine, validator, and safety policy. No module-level global registry.
"""
from __future__ import annotations

from backend.executors.base_executor import BaseExecutor
from backend.models.error_codes import ErrorCode


class RegistrationError(Exception):
    """Raised when executor registration fails (e.g. duplicate action name)."""


class UnknownActionError(Exception):
    """Raised when the registry is queried for an unregistered action name."""

    def __init__(self, action_name: str) -> None:
        super().__init__(
            f"No executor registered for action '{action_name}'. "
            "Check the action name spelling and ensure the executor module is imported."
        )
        self.action_name = action_name
        self.error_code = ErrorCode.VALIDATION_ERROR


class ActionRegistry:
    """Maps 'domain.verb' action names to their BaseExecutor instances.

    The registry is intentionally simple — a dict with a strict no-duplicate rule.
    Adding a new action requires only: create an executor, register it in main.py.
    The engine never needs modification.

    Engineering Rule: Engine never contains action-specific conditionals.
    """

    def __init__(self) -> None:
        self._registry: dict[str, BaseExecutor] = {}

    def register(self, executor: BaseExecutor) -> None:
        """Register an executor for its declared action_name.

        Args:
            executor: A concrete BaseExecutor instance.

        Raises:
            RegistrationError: If an executor for this action_name is already registered.
        """
        name = executor.action_name
        if name in self._registry:
            raise RegistrationError(
                f"An executor for '{name}' is already registered. "
                "Each action may only have one executor. "
                f"Existing: {type(self._registry[name]).__name__}, "
                f"New: {type(executor).__name__}."
            )
        self._registry[name] = executor

    def get(self, action_name: str) -> BaseExecutor:
        """Return the executor for the given action name.

        Args:
            action_name: The 'domain.verb' action identifier.

        Returns:
            The registered BaseExecutor instance.

        Raises:
            UnknownActionError: If no executor is registered for action_name.
        """
        executor = self._registry.get(action_name)
        if executor is None:
            raise UnknownActionError(action_name)
        return executor

    def is_registered(self, action_name: str) -> bool:
        """Return True if an executor is registered for the given action name."""
        return action_name in self._registry

    @property
    def registered_actions(self) -> list[str]:
        """Sorted list of all currently registered action names."""
        return sorted(self._registry.keys())
