from __future__ import annotations

import pytest
from pydantic import ValidationError
from backend.models.resolved_action import ResolvedAction
from backend.models.grammar_tree import Clause, GrammarTree
from backend.models.intent_group import IntentGroup
from backend.models.planner_result import PlannerWarning, PlannerInfo, PlannerDiagnostics


def test_resolved_action_model():
    action = ResolvedAction(capability="application.open", target="chrome", resource_type="application")
    assert action.capability == "application.open"
    assert action.target == "chrome"
    assert action.resource_type == "application"

    with pytest.raises(ValidationError):
        # target must be a string, and frozen
        action.target = "vscode"


def test_grammar_tree_and_clause_models():
    clause = Clause(verb="open", targets=["chrome", "github"])
    assert clause.verb == "open"
    assert clause.targets == ["chrome", "github"]

    tree = GrammarTree(
        clauses=[clause],
        original_command="open chrome and github",
        normalized_command="open chrome and github",
        metadata={"parser_version": "1.0"}
    )
    assert len(tree.clauses) == 1
    assert tree.original_command == "open chrome and github"
    assert tree.metadata["parser_version"] == "1.0"


def test_intent_group_model():
    group = IntentGroup(verb="open", targets=["chrome"], sequence_index=0, source_clause="open chrome")
    assert group.verb == "open"
    assert group.targets == ["chrome"]
    assert group.sequence_index == 0
    assert group.source_clause == "open chrome"


def test_planner_result_models():
    warning = PlannerWarning(code="DUPLICATE_ACTION", message="Duplicate chrome")
    info = PlannerInfo(message="Redundant downloads")
    diag = PlannerDiagnostics(
        planning_time_ms=1.5,
        token_count=4,
        clause_count=1,
        intent_group_count=1,
        resolved_target_count=1,
        warning_count=1
    )

    assert warning.code == "DUPLICATE_ACTION"
    assert info.message == "Redundant downloads"
    assert diag.planning_time_ms == 1.5
    assert diag.token_count == 4
