"""BasePlanner — abstract interface for all plan generators.

Engineering Rule 1: AI plans. Executors execute.

Sprint 001: StubPlanner (pass-through from frontend-supplied steps).
Sprint 003: RulePlanner (deterministic natural language → ActionPlan).
Future sprints: LLM-backed planners (GPT, Gemini, Claude) will subclass this.

From the spec (Future Compatibility):
  "LLM planners, voice, memory, plugins and browser automation must integrate
   without changing the execution engine."

The engine always receives a completed ActionPlan — it never knows or cares
how the plan was generated.

Sprint 003 change: return type updated from ActionPlan to PlannerResult.
This is the universal contract. Every planner returns structured metadata
alongside the ActionPlan so that callers can inspect confidence, warnings,
and error information regardless of the planner implementation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.planner_result import PlannerResult


class BasePlanner(ABC):
    """Abstract base class for all Cortex planners.

    Every planner accepts a natural language command string and returns
    a PlannerResult containing the generated ActionPlan plus metadata.

    Future LLM-backed planners are drop-in replacements — the execution
    pipeline never changes when a new planner is introduced.
    """

    @abstractmethod
    async def plan(self, command: str) -> PlannerResult:
        """Convert a natural language command into a PlannerResult.

        Args:
            command: Plain-text command from the user.
                     Example: "Open Chrome and GitHub"

        Returns:
            PlannerResult with success=True and a populated ActionPlan,
            or success=False with error_code and error_message set.

        Raises:
            PlanningError: Implementations may raise instead of returning
                           a failure PlannerResult. Callers must handle both.
        """
