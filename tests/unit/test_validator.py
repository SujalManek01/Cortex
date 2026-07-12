"""Unit tests: PlanValidator.

Covers all four validation checks:
  1. Schema completeness
  2. Version whitelist (unknown versions rejected)
  3. Action format (domain.verb)
  4. Registry membership
"""
from __future__ import annotations

import uuid

import pytest

from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.error_codes import ErrorCode
from backend.validator.validator import PlanValidator, ValidationError


def make_plan(**overrides) -> ActionPlan:
    """Helper: build a minimal valid ActionPlan with optional overrides."""
    defaults = dict(
        plan_id=uuid.uuid4(),
        goal="Open Notepad",
        version="1.0",
        created_by="stub_planner",
        steps=[ActionStep(id="step-1", action="application.open", parameters={"app": "notepad"})],
    )
    defaults.update(overrides)
    return ActionPlan(**defaults)


class TestPlanValidatorSchemaChecks:
    def test_valid_plan_passes(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan()
        validator.validate(plan)  # Should not raise.

    def test_empty_goal_raises(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(goal="   ")
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert exc_info.value.error_code == ErrorCode.INVALID_PLAN

    def test_empty_steps_raises(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(steps=[])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert exc_info.value.error_code == ErrorCode.INVALID_PLAN

    def test_empty_created_by_raises(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(created_by="")
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert exc_info.value.error_code == ErrorCode.INVALID_PLAN


class TestPlanValidatorVersion:
    def test_version_1_0_accepted(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(version="1.0")
        validator.validate(plan)  # Should not raise.

    def test_unknown_version_rejected(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(version="2.0")
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert "2.0" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.INVALID_PLAN

    def test_empty_version_rejected(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(version="")
        with pytest.raises(ValidationError):
            validator.validate(plan)


class TestPlanValidatorActions:
    def test_registered_action_passes(self, real_registry):
        validator = PlanValidator(real_registry)
        for action in ["application.open", "application.close", "folder.open"]:
            params = {"app": "vscode"} if "application" in action else {"alias": "desktop"}
            plan = make_plan(steps=[ActionStep(id="s1", action=action, parameters=params)])
            validator.validate(plan)  # Should not raise.

    def test_unregistered_action_raises(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(steps=[
            ActionStep(id="s1", action="browser.open", parameters={"url": "https://example.com"})
        ])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert "browser.open" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    def test_invalid_action_format_no_dot(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(steps=[ActionStep(id="s1", action="open_vscode", parameters={})])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert exc_info.value.error_code == ErrorCode.INVALID_PLAN

    def test_invalid_action_format_too_many_dots(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(steps=[ActionStep(id="s1", action="a.b.c", parameters={})])
        with pytest.raises(ValidationError):
            validator.validate(plan)

    def test_duplicate_step_ids_raise(self, real_registry):
        validator = PlanValidator(real_registry)
        plan = make_plan(steps=[
            ActionStep(id="step-1", action="application.open", parameters={"app": "vscode"}),
            ActionStep(id="step-1", action="application.open", parameters={"app": "notepad"}),
        ])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(plan)
        assert "Duplicate" in str(exc_info.value)
