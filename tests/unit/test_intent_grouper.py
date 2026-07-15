from __future__ import annotations

import pytest
from backend.models.grammar_tree import Clause, GrammarTree
from backend.planner.intent_grouper import IntentGrouper
from backend.planner.planning_errors import PlannerErrorCode, PlanningError


@pytest.fixture
def grouper() -> IntentGrouper:
    return IntentGrouper()


def test_grouper_basic(grouper):
    tree = GrammarTree(
        clauses=[Clause(verb="open", targets=["chrome", "github"])],
        original_command="Open Chrome and GitHub",
        normalized_command="open chrome and github"
    )
    groups = grouper.group(tree)
    assert len(groups) == 1
    assert groups[0].verb == "open"
    assert groups[0].targets == ["chrome", "github"]
    assert groups[0].sequence_index == 0


def test_grouper_multiple_clauses(grouper):
    tree = GrammarTree(
        clauses=[
            Clause(verb="open", targets=["chrome"]),
            Clause(verb="close", targets=["vscode"])
        ],
        original_command="Open Chrome then close VS Code",
        normalized_command="open chrome then close vscode"
    )
    groups = grouper.group(tree)
    assert len(groups) == 2
    assert groups[0].verb == "open"
    assert groups[0].targets == ["chrome"]
    assert groups[0].sequence_index == 0
    assert groups[1].verb == "close"
    assert groups[1].targets == ["vscode"]
    assert groups[1].sequence_index == 1


def test_grouper_empty_targets_raises(grouper):
    tree = GrammarTree(
        clauses=[Clause(verb="open", targets=[])],
        original_command="Open",
        normalized_command="open"
    )
    with pytest.raises(PlanningError) as exc:
        grouper.group(tree)
    assert exc.value.error_code == PlannerErrorCode.EMPTY_GROUP
