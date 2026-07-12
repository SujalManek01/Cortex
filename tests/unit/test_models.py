"""Unit tests: domain models.

Tests ActionPlan immutability, ActionStep, ActionResult, ErrorCode,
ExecutionState, and StubPlanner request model construction.
"""
from __future__ import annotations

import uuid

import pytest

from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode
from backend.models.execution_state import ExecutionState, PlanExecutionState
from backend.planner.stub_planner import StubPlanner
from backend.schemas.api import ExecuteRequest, ExecuteStepRequest, ExecutePlanRequest


class TestActionStep:
    def test_creates_with_required_fields(self):
        step = ActionStep(id="s1", action="application.open", parameters={"app": "vscode"})
        assert step.id == "s1"
        assert step.action == "application.open"
        assert step.parameters == {"app": "vscode"}

    def test_parameters_defaults_to_empty_dict(self):
        step = ActionStep(id="s1", action="application.open")
        assert step.parameters == {}

    def test_is_immutable(self):
        step = ActionStep(id="s1", action="application.open")
        with pytest.raises(Exception):  # Pydantic raises ValidationError or TypeError
            step.id = "changed"  # type: ignore[misc]


class TestActionPlan:
    def test_creates_with_all_fields(self):
        plan_id = uuid.uuid4()
        plan = ActionPlan(
            plan_id=plan_id,
            goal="Test goal",
            version="1.0",
            created_by="stub_planner",
            steps=[ActionStep(id="s1", action="application.open", parameters={"app": "vscode"})],
        )
        assert plan.plan_id == plan_id
        assert plan.goal == "Test goal"
        assert plan.version == "1.0"
        assert plan.created_by == "stub_planner"
        assert len(plan.steps) == 1

    def test_default_version_is_1_0(self):
        plan = ActionPlan(
            plan_id=uuid.uuid4(),
            goal="g",
            created_by="stub_planner",
            steps=[ActionStep(id="s1", action="folder.open", parameters={"alias": "desktop"})],
        )
        assert plan.version == "1.0"

    def test_is_immutable(self):
        plan = ActionPlan(
            plan_id=uuid.uuid4(),
            goal="g",
            created_by="stub_planner",
            steps=[],
        )
        with pytest.raises(Exception):
            plan.goal = "mutated"  # type: ignore[misc]

    def test_plan_id_is_uuid(self):
        plan = ActionPlan(
            plan_id=uuid.uuid4(),
            goal="g",
            created_by="stub_planner",
            steps=[],
        )
        assert isinstance(plan.plan_id, uuid.UUID)


class TestActionResult:
    def test_success_result(self):
        result = ActionResult(
            step_id="s1",
            success=True,
            message="OK",
            duration_ms=42.5,
        )
        assert result.success is True
        assert result.error_code is None
        assert result.metadata == {}

    def test_failure_result_with_error_code(self):
        result = ActionResult(
            step_id="s1",
            success=False,
            message="App not found",
            error_code=ErrorCode.UNKNOWN_APPLICATION,
            duration_ms=1.0,
        )
        assert result.success is False
        assert result.error_code == ErrorCode.UNKNOWN_APPLICATION

    def test_model_copy_update(self):
        result = ActionResult(step_id="", success=True, message="ok", duration_ms=0)
        updated = result.model_copy(update={"step_id": "step-99"})
        assert updated.step_id == "step-99"
        assert result.step_id == ""  # original unchanged


class TestErrorCode:
    def test_all_codes_are_strings(self):
        for code in ErrorCode:
            assert isinstance(code.value, str)

    def test_json_serializable(self):
        import json
        codes = [c.value for c in ErrorCode]
        dumped = json.dumps(codes)
        assert isinstance(dumped, str)

    def test_specific_values(self):
        assert ErrorCode.UNKNOWN_APPLICATION == "unknown_application"
        assert ErrorCode.SAFETY_VIOLATION == "safety_violation"
        assert ErrorCode.CONCURRENT_EXECUTION == "concurrent_execution"


class TestExecutionState:
    def test_all_states_present(self):
        states = {s.value for s in ExecutionState}
        assert states == {"pending", "running", "completed", "failed", "skipped"}

    def test_plan_execution_state_defaults(self):
        state = PlanExecutionState(plan_id=uuid.uuid4(), status=ExecutionState.PENDING)
        assert state.step_results == []
        assert state.current_step_id is None
        assert state.started_at is None


class TestStubPlanner:
    def test_generates_plan_id(self):
        planner = StubPlanner()
        req = ExecuteRequest(
            plan=ExecutePlanRequest(
                steps=[ExecuteStepRequest(capability="application.open", target="notepad")]
            )
        )
        plan = planner.plan_from_request(req)
        assert isinstance(plan.plan_id, uuid.UUID)

    def test_sets_created_by(self):
        planner = StubPlanner()
        req = ExecuteRequest(
            plan=ExecutePlanRequest(
                steps=[ExecuteStepRequest(capability="application.open", target="notepad")]
            )
        )
        plan = planner.plan_from_request(req)
        assert plan.created_by == "stub_planner"

    def test_generates_unique_plan_ids(self):
        planner = StubPlanner()
        req = ExecuteRequest(
            plan=ExecutePlanRequest(
                steps=[ExecuteStepRequest(capability="application.open", target="notepad")]
            )
        )
        ids = {planner.plan_from_request(req).plan_id for _ in range(10)}
        assert len(ids) == 10  # All unique

    def test_auto_assigns_step_ids(self):
        planner = StubPlanner()
        req = ExecuteRequest(
            plan=ExecutePlanRequest(
                steps=[
                    ExecuteStepRequest(capability="application.open", target="vscode"),
                    ExecuteStepRequest(capability="application.open", target="notepad"),
                ]
            )
        )
        plan = planner.plan_from_request(req)
        assert plan.steps[0].id == "step-1"
        assert plan.steps[1].id == "step-2"

    def test_sets_version_1_0(self):
        planner = StubPlanner()
        req = ExecuteRequest(
            plan=ExecutePlanRequest(
                steps=[ExecuteStepRequest(capability="folder.open", target="desktop")]
            )
        )
        plan = planner.plan_from_request(req)
        assert plan.version == "1.0"
