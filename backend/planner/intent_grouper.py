from __future__ import annotations

from backend.models.grammar_tree import GrammarTree
from backend.models.intent_group import IntentGroup
from backend.planner.planning_errors import PlannerErrorCode, PlanningError


class IntentGrouper:
    """IntentGrouper — groups targets under their governing verbs into IntentGroups.

    Validates that no verb is left targetless.
    """

    def group(self, tree: GrammarTree) -> list[IntentGroup]:
        """Convert a GrammarTree into a list of IntentGroup objects.

        Args:
            tree: Syntactic GrammarTree from GrammarParser.

        Returns:
            List of IntentGroup objects.

        Raises:
            PlanningError(EMPTY_GROUP): If any clause has a verb but no targets.
        """
        intent_groups: list[IntentGroup] = []

        for i, clause in enumerate(tree.clauses):
            if clause.verb is not None and not clause.targets:
                raise PlanningError(
                    f"Verb '{clause.verb}' has no targets specified.",
                    PlannerErrorCode.EMPTY_GROUP,
                )

            if clause.targets:
                # Format a clean representation of the source clause
                verb_part = f"{clause.verb} " if clause.verb else ""
                source_clause = f"{verb_part}{' and '.join(clause.targets)}"
                
                intent_groups.append(
                    IntentGroup(
                        verb=clause.verb,
                        targets=list(clause.targets),
                        sequence_index=i,
                        source_clause=source_clause,
                    )
                )

        return intent_groups
