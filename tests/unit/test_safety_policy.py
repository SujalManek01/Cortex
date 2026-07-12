"""Unit tests: SafetyPolicy.

Covers:
  - Raw path detection in any parameter (Rule 11)
  - Application allow-list enforcement (Rule 10)
  - Folder alias validation (Rule 11)
  - Plans with no safety concerns pass cleanly
"""
from __future__ import annotations

import uuid

import pytest

from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.error_codes import ErrorCode
from backend.safety.safety_policy import SafetyPolicy, SafetyViolation


def make_plan(steps: list[ActionStep]) -> ActionPlan:
    return ActionPlan(
        plan_id=uuid.uuid4(),
        goal="Test",
        version="1.0",
        created_by="stub_planner",
        steps=steps,
    )


class TestSafetyPolicyRawPaths:
    def test_windows_drive_path_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.open",
                       parameters={"app": r"C:\Windows\notepad.exe"}),
        ])
        with pytest.raises(SafetyViolation) as exc_info:
            policy.enforce(plan)
        assert exc_info.value.error_code == ErrorCode.SAFETY_VIOLATION
        assert "raw path" in str(exc_info.value).lower()

    def test_unc_path_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="folder.open",
                       parameters={"alias": r"\\server\share"}),
        ])
        with pytest.raises(SafetyViolation):
            policy.enforce(plan)

    def test_alias_string_without_path_passes_raw_check(self, test_config):
        """'vscode' alone is not a path — should not trip the raw path check."""
        policy = SafetyPolicy(test_config)
        # This will pass raw path check but may fail allow-list check (expected)
        plan = make_plan([
            ActionStep(id="s1", action="application.open", parameters={"app": "vscode"}),
        ])
        # Should not raise SafetyViolation for raw path reason
        try:
            policy.enforce(plan)
        except SafetyViolation as exc:
            assert "raw path" not in str(exc).lower()


class TestSafetyPolicyAllowList:
    def test_registered_app_passes(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.open", parameters={"app": "vscode"}),
        ])
        policy.enforce(plan)  # Should not raise.

    def test_unregistered_app_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.open", parameters={"app": "unknown_app"}),
        ])
        with pytest.raises(SafetyViolation) as exc_info:
            policy.enforce(plan)
        assert exc_info.value.error_code == ErrorCode.SAFETY_VIOLATION
        assert "unknown_app" in str(exc_info.value)

    def test_missing_app_parameter_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.open", parameters={}),
        ])
        with pytest.raises(SafetyViolation):
            policy.enforce(plan)

    def test_application_close_uses_allow_list(self, test_config):
        policy = SafetyPolicy(test_config)
        # Registered app: should pass.
        plan = make_plan([
            ActionStep(id="s1", action="application.close", parameters={"app": "vscode"}),
        ])
        policy.enforce(plan)  # Should not raise.

    def test_application_close_unregistered_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.close", parameters={"app": "malware"}),
        ])
        with pytest.raises(SafetyViolation):
            policy.enforce(plan)


class TestSafetyPolicyAliases:
    def test_registered_alias_passes(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="folder.open", parameters={"alias": "desktop"}),
        ])
        policy.enforce(plan)  # Should not raise.

    def test_unregistered_alias_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="folder.open", parameters={"alias": "secret_folder"}),
        ])
        with pytest.raises(SafetyViolation) as exc_info:
            policy.enforce(plan)
        assert "secret_folder" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.SAFETY_VIOLATION

    def test_missing_alias_parameter_rejected(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="folder.open", parameters={}),
        ])
        with pytest.raises(SafetyViolation):
            policy.enforce(plan)


class TestSafetyPolicyMultiStep:
    def test_first_violation_stops_enforcement(self, test_config):
        """SafetyPolicy raises on the first violation — it does not collect all violations."""
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.open", parameters={"app": "bad_app"}),
            ActionStep(id="s2", action="application.open", parameters={"app": "another_bad"}),
        ])
        with pytest.raises(SafetyViolation) as exc_info:
            policy.enforce(plan)
        # Only the first step's violation should be reported.
        assert "bad_app" in str(exc_info.value)

    def test_clean_multi_step_plan_passes(self, test_config):
        policy = SafetyPolicy(test_config)
        plan = make_plan([
            ActionStep(id="s1", action="application.open", parameters={"app": "vscode"}),
            ActionStep(id="s2", action="folder.open", parameters={"alias": "desktop"}),
            ActionStep(id="s3", action="application.close", parameters={"app": "vscode"}),
        ])
        policy.enforce(plan)  # Should not raise.
