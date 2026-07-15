from __future__ import annotations

from backend.models.intent_group import IntentGroup
from backend.planner.planning_errors import PlannerErrorCode, PlanningError


class ScopeResolver:
    """ScopeResolver — resolves verb scope and propagates verbs across grouped targets.

    Ensures every target has a governing verb, and rejects cases where
    verbs are missing (e.g. across sequence boundaries).
    """

    def resolve_scope(self, groups: list[IntentGroup]) -> list[IntentGroup]:
        """Expand IntentGroups so that each group contains exactly one target.

        Verbs are propagated to all targets within the same group.

        Args:
            groups: List of IntentGroup objects from IntentGrouper.

        Returns:
            List of expanded single-target IntentGroup objects.

        Raises:
            PlanningError(INVALID_SEQUENCE): If any target lacks a governing verb.
        """
        expanded: list[IntentGroup] = []

        for group in groups:
            if group.verb is None:
                if group.sequence_index == 0:
                    raise PlanningError(
                        f"Unknown or missing intent for target(s): {', '.join(group.targets)}.",
                        PlannerErrorCode.UNKNOWN_INTENT,
                    )
                else:
                    targets_str = ", ".join(group.targets)
                    raise PlanningError(
                        f"No governing verb specified for target(s): {targets_str}.",
                        PlannerErrorCode.INVALID_SEQUENCE,
                    )

            for target in group.targets:
                expanded.append(
                    IntentGroup(
                        verb=group.verb,
                        targets=[target],
                        sequence_index=group.sequence_index,
                        source_clause=group.source_clause,
                    )
                )

        return expanded
