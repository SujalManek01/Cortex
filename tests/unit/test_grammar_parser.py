from __future__ import annotations

import pytest
from backend.planner.grammar_parser import GrammarParser


@pytest.fixture
def parser() -> GrammarParser:
    return GrammarParser()


def test_parse_single_action(parser):
    tree = parser.parse(["open", "chrome"], "Open Chrome")
    assert len(tree.clauses) == 1
    assert tree.clauses[0].verb == "open"
    assert tree.clauses[0].targets == ["chrome"]
    assert tree.metadata["parser_version"] == "1.0"
    assert tree.metadata["spec_version"] == "0.4"
    assert tree.metadata["clause_count"] == 1


def test_parse_grouped_targets(parser):
    tree = parser.parse(["open", "chrome", "and", "github", "and", "downloads"], "Open Chrome, GitHub and Downloads")
    assert len(tree.clauses) == 1
    assert tree.clauses[0].verb == "open"
    assert tree.clauses[0].targets == ["chrome", "github", "downloads"]


def test_parse_multiple_clauses(parser):
    tree = parser.parse(
        ["open", "chrome", "and", "github", "then", "close", "vscode"],
        "Open Chrome and GitHub then Close VS Code"
    )
    assert len(tree.clauses) == 2
    assert tree.clauses[0].verb == "open"
    assert tree.clauses[0].targets == ["chrome", "github"]
    assert tree.clauses[1].verb == "close"
    assert tree.clauses[1].targets == ["vscode"]


def test_parse_clause_without_verb(parser):
    tree = parser.parse(["chrome", "and", "github"], "Chrome and GitHub")
    assert len(tree.clauses) == 1
    assert tree.clauses[0].verb is None
    assert tree.clauses[0].targets == ["chrome", "github"]


def test_parse_mixed_verb_and_sequence(parser):
    tree = parser.parse(
        ["open", "chrome", "then", "github"],
        "Open Chrome then GitHub"
    )
    assert len(tree.clauses) == 2
    assert tree.clauses[0].verb == "open"
    assert tree.clauses[0].targets == ["chrome"]
    assert tree.clauses[1].verb is None
    assert tree.clauses[1].targets == ["github"]


def test_parse_unknown_tokens_preserved(parser):
    tree = parser.parse(["open", "chrome", "@invalid", "github"], "open chrome @invalid github")
    assert len(tree.clauses) == 1
    assert tree.clauses[0].targets == ["chrome", "@invalid", "github"]


def test_parse_empty_connector_clauses_filtered(parser):
    tree = parser.parse(["open", "chrome", "then"], "Open Chrome then")
    assert len(tree.clauses) == 1
    assert tree.clauses[0].verb == "open"
    assert tree.clauses[0].targets == ["chrome"]
