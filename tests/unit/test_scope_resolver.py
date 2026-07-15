from __future__ import annotations

import pytest
from backend.models.intent_group import IntentGroup
from backend.planner.scope_resolver import ScopeResolver
from backend.planner.planning_errors import PlannerErrorCode, PlanningError


@pytest.fixture
def resolver() -> ScopeResolver:
    return ScopeResolver()


def test_scope_resolver_basic(resolver):
    groups = [
        IntentGroup(verb="open", targets=["chrome", "github"], sequence_index=0, source_clause="open chrome and github")
    ]
    expanded = resolver.resolve_scope(groups)
    assert len(expanded) == 2
    assert expanded[0].verb == "open"
    assert expanded[0].targets == ["chrome"]
    assert expanded[0].sequence_index == 0
    assert expanded[1].verb == "open"
    assert expanded[1].targets == ["github"]
    assert expanded[1].sequence_index == 0


def test_scope_resolver_missing_verb_raises(resolver):
    groups = [
        IntentGroup(verb="open", targets=["chrome"], sequence_index=0, source_clause="open chrome"),
        IntentGroup(verb=None, targets=["github"], sequence_index=1, source_clause="github")
    ]
    with pytest.raises(PlanningError) as exc:
        resolver.resolve_scope(groups)
    assert exc.value.error_code == PlannerErrorCode.INVALID_SEQUENCE
