"""BasePlanner — abstract interface for all plan generators.

Engineering Rule 1: AI plans. Executors execute.

Sprint 1: StubPlanner (pass-through from frontend-supplied steps).
Future sprints: LLM-backed planners (GPT, Gemini, Claude) will subclass this.

From the spec (Future Compatibility):
  "LLM planners, voice, memory, plugins and browser automation must integrate
   without changing the execution engine."

The engine always receives a completed ActionPlan — it never knows or cares
how the plan was generated.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.action_plan import ActionPlan


class BasePlanner(ABC):
    """Abstract base class for all Cortex planners.

    Future LLM-backed planners accept only a natural language goal and
    autonomously produce an ActionPlan (selecting actions, parameters, etc.).
    """

    @abstractmethod
    async def plan(self, goal: str) -> ActionPlan:
        """Convert a natural language goal into an immutable ActionPlan.

        Args:
            goal: Human-readable description of what the user wants to accomplish.
                  Example: "Open VS Code and Chrome, then open the chatbot project folder."

        Returns:
            A fully-formed, immutable ActionPlan ready for validation and execution.

        Raises:
            PlanningError: If the goal cannot be converted into a valid plan.
        """
