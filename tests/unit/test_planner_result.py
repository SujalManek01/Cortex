"""Unit tests: PlannerResult model — Sprint 003."""
from __future__ import annotations

import uuid

import pytest

from backend.models.planner_result import PlannerResult
from backend.models.action_plan import ActionPlan, ActionStep


def _make_plan() -> ActionPlan:
    return ActionPlan(
        plan_id=uuid.uuid4(),
        goal="open chrome",
        version="1.0",
        created_by="rule_planner",
        steps=[ActionStep(id="step-1", action="application.open", parameters={"app": "chrome"})],
    )


class TestPlannerResultSuccess:
    def test_success_defaults(self):
        result = PlannerResult(success=True, plan=_make_plan(), planner_name="rule_planner")
        assert result.success is True
        assert result.confidence == 0.0   # caller must set explicitly
        assert result.warnings == []
        assert result.error_code is None
        assert result.error_message is None
        assert result.token_count == 0
        assert result.step_count == 0

    def test_success_full(self):
        plan = _make_plan()
        result = PlannerResult(
            success=True,
            plan=plan,
            normalized_input="open chrome",
            confidence=1.0,
            warnings=[],
            planning_time_ms=3.7,
            token_count=2,
            step_count=1,
            planner_name="rule_planner",
        )
        assert result.plan is plan
        assert result.confidence == 1.0
        assert result.planning_time_ms == 3.7
        assert result.token_count == 2
        assert result.step_count == 1
        assert result.planner_name == "rule_planner"

    def test_warnings_preserved(self):
        result = PlannerResult(
            success=True, plan=_make_plan(),
            warnings=["Duplicate target detected."],
            planner_name="rule_planner",
        )
        assert len(result.warnings) == 1
        assert "Duplicate" in result.warnings[0]


class TestPlannerResultFailure:
    def test_failure_defaults(self):
        result = PlannerResult(
            success=False,
            error_code="UNKNOWN_TARGET",
            error_message="Target 'xyz' is not registered.",
            planner_name="rule_planner",
        )
        assert result.success is False
        assert result.plan is None
        assert result.confidence == 0.0
        assert result.error_code == "UNKNOWN_TARGET"
        assert result.error_message == "Target 'xyz' is not registered."

    def test_all_error_codes_are_strings(self):
        from backend.planner.planning_errors import PlannerErrorCode
        for code in PlannerErrorCode:
            assert isinstance(code.value, str)
            result = PlannerResult(success=False, error_code=code, planner_name="rule_planner")
            assert result.error_code == code


class TestPlannerResultSerialization:
    def test_serializes_to_dict(self):
        result = PlannerResult(
            success=False,
            error_code="EMPTY_COMMAND",
            error_message="No command supplied.",
            planner_name="rule_planner",
        )
        d = result.model_dump()
        assert d["success"] is False
        assert d["error_code"] == "EMPTY_COMMAND"
        assert d["plan"] is None
