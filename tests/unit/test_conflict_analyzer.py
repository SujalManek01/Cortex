from __future__ import annotations

import pytest
from backend.config.config_loader import PlannerRulesConfig
from backend.models.resolved_action import ResolvedAction
from backend.planner.conflict_analyzer import ConflictAnalyzer


@pytest.fixture
def default_analyzer() -> ConflictAnalyzer:
    return ConflictAnalyzer()


def test_conflict_analyzer_no_conflicts(default_analyzer):
    actions = [
        ResolvedAction(capability="application.open", target="chrome", resource_type="application"),
        ResolvedAction(capability="application.open", target="vscode", resource_type="application")
    ]
    warnings, infos = default_analyzer.analyze(actions)
    assert not warnings
    assert not infos


def test_conflict_analyzer_duplicate_application(default_analyzer):
    actions = [
        ResolvedAction(capability="application.open", target="chrome", resource_type="application"),
        ResolvedAction(capability="application.open", target="chrome", resource_type="application")
    ]
    warnings, infos = default_analyzer.analyze(actions)
    assert len(warnings) == 1
    assert warnings[0].code == "DUPLICATE_ACTION"
    assert "chrome" in warnings[0].message
    assert not infos


def test_conflict_analyzer_redundant_folder(default_analyzer):
    actions = [
        ResolvedAction(capability="folder.open", target="downloads", resource_type="folder"),
        ResolvedAction(capability="folder.open", target="downloads", resource_type="folder")
    ]
    warnings, infos = default_analyzer.analyze(actions)
    assert not warnings
    assert len(infos) == 1
    assert "downloads" in infos[0].message


def test_conflict_analyzer_contradictory_application(default_analyzer):
    actions = [
        ResolvedAction(capability="application.open", target="chrome", resource_type="application"),
        ResolvedAction(capability="application.close", target="chrome", resource_type="application")
    ]
    warnings, infos = default_analyzer.analyze(actions)
    assert len(warnings) == 1
    assert warnings[0].code == "CONTRADICTORY_ACTION"
    assert "chrome" in warnings[0].message
    assert not infos


def test_conflict_analyzer_custom_rules():
    config = PlannerRulesConfig(
        version="1.0",
        duplicate_action="information",      # duplicate as info
        contradictory_action="information",  # contradiction as info
        redundant_action="warning"           # redundant as warning
    )
    analyzer = ConflictAnalyzer(rules_config=config)

    # 1. Test duplicate chrome is now info, redundant downloads is warning
    actions = [
        ResolvedAction(capability="application.open", target="chrome", resource_type="application"),
        ResolvedAction(capability="application.open", target="chrome", resource_type="application"),
        ResolvedAction(capability="folder.open", target="downloads", resource_type="folder"),
        ResolvedAction(capability="folder.open", target="downloads", resource_type="folder")
    ]
    warnings, infos = analyzer.analyze(actions)
    assert len(warnings) == 1
    assert warnings[0].code == "REDUNDANT_ACTION"  # redundant is warning
    assert len(infos) == 1
    assert "chrome" in infos[0].message            # duplicate is info

    # 2. Test contradiction is now info
    actions_contra = [
        ResolvedAction(capability="application.open", target="chrome", resource_type="application"),
        ResolvedAction(capability="application.close", target="chrome", resource_type="application")
    ]
    warnings_contra, infos_contra = analyzer.analyze(actions_contra)
    assert not warnings_contra
    assert len(infos_contra) == 1
    assert "chrome" in infos_contra[0].message
