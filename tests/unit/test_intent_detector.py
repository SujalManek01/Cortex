"""Unit tests: IntentDetector — Sprint 003."""
from __future__ import annotations

import pytest

from backend.planner.intent_detector import IntentDetector, SubCommand
from backend.planner.planning_errors import PlannerErrorCode, PlanningError


@pytest.fixture
def detector() -> IntentDetector:
    return IntentDetector()


# ── Single sub-command ─────────────────────────────────────────────────────────

class TestSingleSubCommand:
    def test_open_chrome(self, detector):
        result = detector.detect(["open", "chrome"])
        assert result == [SubCommand(intent="open", targets=["chrome"])]

    def test_close_chrome(self, detector):
        result = detector.detect(["close", "chrome"])
        assert result == [SubCommand(intent="close", targets=["chrome"])]

    def test_open_single_target(self, detector):
        result = detector.detect(["open", "vscode"])
        assert len(result) == 1
        assert result[0].intent == "open"
        assert result[0].targets == ["vscode"]


# ── Verb synonyms (already normalised by Normalizer) ─────────────────────────

class TestVerbSynonyms:
    """Verbs are already canonicalised by the Normalizer; detector sees only 'open'/'close'."""

    def test_open_is_open(self, detector):
        result = detector.detect(["open", "chrome"])
        assert result[0].intent == "open"

    def test_close_is_close(self, detector):
        result = detector.detect(["close", "chrome"])
        assert result[0].intent == "close"


# ── Multiple targets in one sub-command ───────────────────────────────────────

class TestMultipleTargetsViaSingleVerb:
    def test_two_targets_via_connector(self, detector):
        """open chrome then github → 2 sub-commands each with open intent."""
        result = detector.detect(["open", "chrome", "then", "github"])
        assert len(result) == 2
        assert result[0] == SubCommand(intent="open", targets=["chrome"])
        assert result[1] == SubCommand(intent="open", targets=["github"])

    def test_three_targets_via_connectors(self, detector):
        result = detector.detect(["open", "chrome", "then", "github", "then", "downloads"])
        assert len(result) == 3
        assert all(sc.intent == "open" for sc in result)
        assert [sc.targets[0] for sc in result] == ["chrome", "github", "downloads"]

    def test_order_preserved(self, detector):
        result = detector.detect(["open", "vscode", "then", "chrome", "then", "downloads"])
        assert [sc.targets[0] for sc in result] == ["vscode", "chrome", "downloads"]


# ── Verb repeated explicitly ──────────────────────────────────────────────────

class TestRepeatedVerb:
    def test_open_verb_repeated_with_same_intent(self, detector):
        """open chrome then open github — both open, no MIXED_INTENTS."""
        result = detector.detect(["open", "chrome", "then", "open", "github"])
        assert len(result) == 2
        assert all(sc.intent == "open" for sc in result)
        assert result[0].targets == ["chrome"]
        assert result[1].targets == ["github"]


# ── Mixed intents rejected ────────────────────────────────────────────────────

class TestMixedIntents:
    def test_open_and_close_raises(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect(["open", "chrome", "then", "close", "vscode"])
        assert exc.value.error_code == PlannerErrorCode.MIXED_INTENTS

    def test_close_then_open_raises(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect(["close", "chrome", "then", "open", "vscode"])
        assert exc.value.error_code == PlannerErrorCode.MIXED_INTENTS


# ── Error cases ────────────────────────────────────────────────────────────────

class TestErrors:
    def test_empty_token_list(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect([])
        assert exc.value.error_code == PlannerErrorCode.EMPTY_COMMAND

    def test_no_verb_at_start(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect(["chrome"])
        assert exc.value.error_code == PlannerErrorCode.UNKNOWN_INTENT

    def test_connector_only(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect(["then"])
        assert exc.value.error_code == PlannerErrorCode.UNKNOWN_INTENT

    def test_verb_with_no_targets(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect(["open"])
        assert exc.value.error_code == PlannerErrorCode.UNKNOWN_INTENT

    def test_unknown_verb_raises(self, detector):
        with pytest.raises(PlanningError) as exc:
            detector.detect(["destroy", "chrome"])
        assert exc.value.error_code == PlannerErrorCode.UNKNOWN_INTENT


# ── SubCommand dataclass ───────────────────────────────────────────────────────

class TestSubCommandDataclass:
    def test_equality(self):
        a = SubCommand(intent="open", targets=["chrome"])
        b = SubCommand(intent="open", targets=["chrome"])
        assert a == b

    def test_frozen(self):
        sc = SubCommand(intent="open", targets=["chrome"])
        with pytest.raises((AttributeError, TypeError)):
            sc.intent = "close"  # type: ignore[misc]
