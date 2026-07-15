from __future__ import annotations

from backend.config.config_loader import PlannerRulesConfig
from backend.models.planner_result import PlannerWarning, PlannerInfo
from backend.models.resolved_action import ResolvedAction


class ConflictAnalyzer:
    """ConflictAnalyzer — detects duplicates, contradictions, and redundancies in planned actions.

    The severity of warnings and info logs is dynamically configurable via
    PlannerRulesConfig (loaded from planner_rules.json).
    """

    def __init__(self, rules_config: PlannerRulesConfig | None = None) -> None:
        if rules_config is not None:
            self._duplicate_severity = rules_config.duplicate_action
            self._contradictory_severity = rules_config.contradictory_action
            self._redundant_severity = rules_config.redundant_action
        else:
            self._duplicate_severity = "warning"
            self._contradictory_severity = "warning"
            self._redundant_severity = "information"

    def analyze(
        self,
        actions: list[ResolvedAction]
    ) -> tuple[list[PlannerWarning], list[PlannerInfo]]:
        """Scan actions to identify duplicates, contradictions, and redundancies.

        Args:
            actions: List of ResolvedAction objects from TargetResolver.

        Returns:
            A tuple of (warnings, information) lists.
        """
        warnings: list[PlannerWarning] = []
        infos: list[PlannerInfo] = []

        seen_actions: set[tuple[str, str]] = set()
        target_caps: dict[str, set[str]] = {}

        # First collect capabilities per application target to identify contradictions
        for action in actions:
            if action.resource_type == "application":
                if action.target not in target_caps:
                    target_caps[action.target] = set()
                target_caps[action.target].add(action.capability)

        # 1. Process duplicate and redundant actions sequentially
        for action in actions:
            action_key = (action.capability, action.target)
            if action_key in seen_actions:
                if action.resource_type == "application":
                    msg = f"Duplicate action detected for target '{action.target}'."
                    self._add_conflict(msg, self._duplicate_severity, "DUPLICATE_ACTION", warnings, infos)
                else:
                    msg = f"Redundant action detected for target '{action.target}'."
                    self._add_conflict(msg, self._redundant_severity, "REDUNDANT_ACTION", warnings, infos)
            seen_actions.add(action_key)

        # 2. Process contradictory actions
        for target, caps in target_caps.items():
            if "application.open" in caps and "application.close" in caps:
                msg = f"Contradictory actions detected for target '{target}'."
                self._add_conflict(msg, self._contradictory_severity, "CONTRADICTORY_ACTION", warnings, infos)

        return warnings, infos

    @staticmethod
    def _add_conflict(
        message: str,
        severity: str,
        code: str,
        warnings: list[PlannerWarning],
        infos: list[PlannerInfo]
    ) -> None:
        """Helper to append log to the correct list based on severity setting."""
        if severity == "warning":
            warnings.append(PlannerWarning(code=code, message=message))
        elif severity == "information":
            infos.append(PlannerInfo(message=message))
