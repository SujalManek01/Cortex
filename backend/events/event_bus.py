"""EventBus Protocol — interface definition only. Not implemented in Sprint 1.

Refinement 5: Introduced for future-proofing. LLM planners, voice, memory,
and plugins will integrate via events without changing the execution engine.

Per the spec (Future Compatibility):
  "LLM planners, voice, memory, plugins and browser automation must integrate
   without changing the execution engine."

DO NOT implement this protocol in Sprint 1.
An implementation (e.g. InMemoryEventBus) will be added in a future sprint
when consumers exist.
"""
from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class EventBus(Protocol):
    """
    Protocol for the Cortex event bus.

    Once implemented, the execution engine will publish lifecycle events
    (engine.plan.start, engine.step.complete, etc.) so that future
    components (voice, memory, plugins) can react without coupling to
    the engine internals.

    Naming convention for event_type: 'component.noun.verb'
    Examples:
        'engine.plan.started'
        'engine.step.completed'
        'engine.step.failed'
        'engine.plan.completed'
    """

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Emit an event to all registered subscribers.

        Args:
            event_type: Namespaced event identifier, e.g. 'engine.step.completed'.
            payload:    Structured event data. Must be JSON-serializable.
        """
        ...

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[str, dict[str, Any]], None],
    ) -> None:
        """Register a callable to handle events of a given type.

        Args:
            event_type: The event type to subscribe to. Supports exact match only.
            handler:    Callable receiving (event_type: str, payload: dict).
        """
        ...
