"""Unit tests: PlanningError and PlannerErrorCode — Sprint 003."""
from __future__ import annotations

import pytest

from backend.planner.planning_errors import PlannerErrorCode, PlanningError


class TestPlannerErrorCode:
    def test_all_codes_are_strings(self):
        for code in PlannerErrorCode:
            assert isinstance(code.value, str)
            assert code == code.value  # StrEnum equality

    def test_expected_codes_exist(self):
        codes = {c.value for c in PlannerErrorCode}
        expected = {
            "EMPTY_COMMAND",
            "UNKNOWN_INTENT",
            "UNKNOWN_TARGET",
            "AMBIGUOUS_TARGET",
            "MIXED_INTENTS",
            "TOKENIZATION_ERROR",
            "NORMALIZATION_ERROR",
            "COMMAND_TOO_LONG",
        }
        assert expected.issubset(codes)


class TestPlanningError:
    def test_carries_error_code(self):
        err = PlanningError("test error", PlannerErrorCode.UNKNOWN_TARGET)
        assert err.error_code == PlannerErrorCode.UNKNOWN_TARGET
        assert "test error" in str(err)

    def test_is_exception(self):
        err = PlanningError("msg", PlannerErrorCode.EMPTY_COMMAND)
        assert isinstance(err, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(PlanningError) as exc_info:
            raise PlanningError("no input", PlannerErrorCode.EMPTY_COMMAND)
        assert exc_info.value.error_code == PlannerErrorCode.EMPTY_COMMAND

    def test_repr(self):
        err = PlanningError("oops", PlannerErrorCode.MIXED_INTENTS)
        assert "MIXED_INTENTS" in repr(err)
        assert "oops" in repr(err)
