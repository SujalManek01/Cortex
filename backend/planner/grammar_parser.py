from __future__ import annotations

import re
from typing import Any
from backend.config.config_loader import GrammarConfig
from backend.models.grammar_tree import Clause, GrammarTree


class GrammarParser:
    """GrammarParser — parses normalized tokens into a syntactic GrammarTree.

    This stage is only responsible for identifying clause boundaries and grouping
    targets. It does not resolve targets or determine intent execution.
    """

    def __init__(self, grammar_config: GrammarConfig | None = None) -> None:
        self._verbs = {"open", "close"}
        self._connectors = {"and"}
        self._sequences = {"then"}

    def parse(
        self,
        normalized_tokens: list[str],
        original_command: str
    ) -> GrammarTree:
        """Parse normalized token values into a GrammarTree.

        A new clause is started whenever:
          - A SEQUENCE token ("then") is encountered.
          - A VERB token ("open", "close") is encountered.

        Args:
            normalized_tokens: List of normalized token strings from Normalizer.
            original_command: Raw user input command.

        Returns:
            A populated GrammarTree object.
        """
        clauses: list[Clause] = []
        current_verb: str | None = None
        current_targets: list[str] = []
        clause_active = False

        def flush_current():
            nonlocal clause_active, current_verb, current_targets
            if clause_active:
                clauses.append(Clause(verb=current_verb, targets=list(current_targets)))
            current_verb = None
            current_targets = []
            clause_active = False

        for token in normalized_tokens:
            token_type = self._classify(token)

            if token_type == "SEQUENCE":
                flush_current()
                # A sequence token implies we split, but we also mark it active
                # so that any subsequent targets start a new clause with verb=None.
                clause_active = True
                continue

            if token_type == "VERB":
                # Start of a new action: flush previous clause if it had content
                if clause_active and (current_verb is not None or current_targets):
                    flush_current()
                current_verb = token
                clause_active = True
                continue

            if token_type == "CONNECTOR":
                # Grouping connector: we just skip it as it connects targets inside the same clause
                clause_active = True
                continue

            # TARGET or UNKNOWN
            clause_active = True
            current_targets.append(token)

        flush_current()

        # Remove any completely empty clauses (e.g. trailing connectors/sequences)
        clauses = [c for c in clauses if c.verb is not None or c.targets]

        # Build metadata
        metadata = {
            "parser_version": "1.0",
            "grammar_version": "1.0",
            "spec_version": "0.4",
            "token_count": len(normalized_tokens),
            "clause_count": len(clauses),
        }

        return GrammarTree(
            clauses=clauses,
            original_command=original_command,
            normalized_command=" ".join(normalized_tokens),
            metadata=metadata,
        )

    def _classify(self, token: str) -> str:
        """Classify a single normalized token into a grammatical category."""
        if token in self._verbs:
            return "VERB"
        if token in self._sequences:
            return "SEQUENCE"
        if token in self._connectors:
            return "CONNECTOR"
        # Check if it is a potential target (alphanumeric word matching pattern)
        if re.fullmatch(r"[a-z0-9][a-z0-9\-']*", token):
            return "TARGET"
        return "UNKNOWN"
