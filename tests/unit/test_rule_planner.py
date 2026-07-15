"""Unit tests: RulePlanner — Sprint 003.

Uses real registries backed by real config files for full end-to-end planning.
No execution occurs — only ActionPlan construction is tested.
"""
from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from backend.config.config_loader import AppEntry, ReadOnlyConfig
from backend.models.action_plan import ActionPlan
from backend.models.planner_result import PlannerResult
from backend.planner.planning_errors import PlannerErrorCode
from backend.planner.rule_planner import RulePlanner
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry

_CONFIG_DIR = Path(__file__).parents[2] / "config"


# ── Test registry factory ─────────────────────────────────────────────────────

def _make_planner(
    apps: tuple[AppEntry, ...] | None = None,
    aliases: dict | None = None,
    websites: dict | None = None,
) -> RulePlanner:
    apps = apps or (
        AppEntry(name="Chrome", alias="chrome", executable="chrome.exe", path="C:\\fake\\chrome.exe"),
        AppEntry(name="VS Code", alias="vscode", executable="Code.exe", path="C:\\fake\\vscode.exe"),
        AppEntry(name="Notepad", alias="notepad", executable="notepad.exe", path="C:\\notepad.exe"),
        AppEntry(name="Spotify", alias="spotify", executable="Spotify.exe", path="C:\\Spotify.exe"),
    )
    aliases = aliases or {
        "downloads": "C:\\Users\\test\\Downloads",
        "desktop":   "C:\\Users\\test\\Desktop",
        "documents": "C:\\Users\\test\\Documents",
    }
    websites = websites or {
        "github":  "https://github.com",
        "chatgpt": "https://chat.openai.com",
        "youtube": "https://youtube.com",
    }
    config = ReadOnlyConfig(
        _apps=apps,
        _aliases=MappingProxyType(aliases),
        _websites=MappingProxyType(websites),
    )
    return RulePlanner(
        app_registry=ApplicationRegistry(config),
        folder_registry=FolderRegistry(config),
        website_registry=WebsiteRegistry(config),
        config_dir=_CONFIG_DIR,
        logger=None,
    )


@pytest.fixture
def planner() -> RulePlanner:
    return _make_planner()


# ── Single action plans ───────────────────────────────────────────────────────

class TestSingleActionPlan:
    @pytest.mark.asyncio
    async def test_open_chrome(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.success is True
        assert result.plan is not None
        assert len(result.plan.steps) == 1
        step = result.plan.steps[0]
        assert step.action == "application.open"
        assert step.parameters["app"] == "chrome"

    @pytest.mark.asyncio
    async def test_open_downloads(self, planner):
        result = await planner.plan("Open Downloads")
        assert result.success is True
        step = result.plan.steps[0]
        assert step.action == "folder.open"
        assert step.parameters["alias"] == "downloads"

    @pytest.mark.asyncio
    async def test_open_github(self, planner):
        result = await planner.plan("Open GitHub")
        assert result.success is True
        step = result.plan.steps[0]
        assert step.action == "website.open"
        assert step.parameters["alias"] == "github"

    @pytest.mark.asyncio
    async def test_close_chrome(self, planner):
        result = await planner.plan("Close Chrome")
        assert result.success is True
        step = result.plan.steps[0]
        assert step.action == "application.close"
        assert step.parameters["app"] == "chrome"


# ── Multi-action plans ────────────────────────────────────────────────────────

class TestMultiActionPlan:
    @pytest.mark.asyncio
    async def test_open_chrome_and_github(self, planner):
        result = await planner.plan("Open Chrome and GitHub")
        assert result.success is True
        assert len(result.plan.steps) == 2
        assert result.plan.steps[0].action == "application.open"
        assert result.plan.steps[1].action == "website.open"

    @pytest.mark.asyncio
    async def test_three_step_plan(self, planner):
        result = await planner.plan("Open Chrome then open VS Code and Downloads")
        assert result.success is True
        assert len(result.plan.steps) == 3

    @pytest.mark.asyncio
    async def test_step_order_preserved(self, planner):
        result = await planner.plan("Open Downloads then open Chrome then open GitHub")
        assert result.success is True
        steps = result.plan.steps
        assert steps[0].parameters["alias"] == "downloads"
        assert steps[1].parameters["app"] == "chrome"
        assert steps[2].parameters["alias"] == "github"


# ── Verb alias expansion ──────────────────────────────────────────────────────

class TestVerbAliases:
    @pytest.mark.asyncio
    async def test_launch_chrome(self, planner):
        result = await planner.plan("Launch Chrome")
        assert result.success is True
        assert result.plan.steps[0].action == "application.open"

    @pytest.mark.asyncio
    async def test_run_chrome(self, planner):
        result = await planner.plan("Run Chrome")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_start_chrome(self, planner):
        result = await planner.plan("Start Chrome")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_quit_chrome(self, planner):
        result = await planner.plan("Quit Chrome")
        assert result.success is True
        assert result.plan.steps[0].action == "application.close"


# ── Target alias expansion ────────────────────────────────────────────────────

class TestTargetAliases:
    @pytest.mark.asyncio
    async def test_vs_code_expanded(self, planner):
        result = await planner.plan("Open VS Code")
        assert result.success is True
        assert result.plan.steps[0].parameters["app"] == "vscode"

    @pytest.mark.asyncio
    async def test_google_chrome_expanded(self, planner):
        result = await planner.plan("Open Google Chrome")
        assert result.success is True
        assert result.plan.steps[0].parameters["app"] == "chrome"

    @pytest.mark.asyncio
    async def test_chat_gpt_expanded(self, planner):
        result = await planner.plan("Open Chat GPT")
        assert result.success is True
        assert result.plan.steps[0].parameters["alias"] == "chatgpt"


# ── PlannerResult metadata ────────────────────────────────────────────────────

class TestPlannerResultMetadata:
    @pytest.mark.asyncio
    async def test_planner_name(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.planner_name == "rule_planner"

    @pytest.mark.asyncio
    async def test_confidence_is_1_on_success(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_token_count_set(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.token_count >= 1

    @pytest.mark.asyncio
    async def test_step_count_matches_steps(self, planner):
        result = await planner.plan("Open Chrome and GitHub")
        assert result.step_count == len(result.plan.steps)

    @pytest.mark.asyncio
    async def test_planning_time_recorded(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.planning_time_ms >= 0.0

    @pytest.mark.asyncio
    async def test_normalized_input_set(self, planner):
        result = await planner.plan("OPEN  CHROME")
        assert result.normalized_input == "open chrome"

    @pytest.mark.asyncio
    async def test_plan_goal_is_normalized_input(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.plan.goal == result.normalized_input

    @pytest.mark.asyncio
    async def test_plan_created_by(self, planner):
        result = await planner.plan("Open Chrome")
        assert result.plan.created_by == "rule_planner"

    @pytest.mark.asyncio
    async def test_step_ids_unique(self, planner):
        result = await planner.plan("Open Chrome and GitHub and Downloads")
        ids = [s.id for s in result.plan.steps]
        assert len(ids) == len(set(ids))


# ── Duplicate target warning ──────────────────────────────────────────────────

class TestDuplicateTargetWarning:
    @pytest.mark.asyncio
    async def test_duplicate_target_warns(self, planner):
        result = await planner.plan("Open Chrome then open Chrome")
        assert result.success is True
        assert len(result.plan.steps) == 2
        assert any("Duplicate" in w.message for w in result.warnings)

    @pytest.mark.asyncio
    async def test_no_warning_without_duplicate(self, planner):
        result = await planner.plan("Open Chrome and GitHub")
        assert not result.warnings


# ── Failure paths ─────────────────────────────────────────────────────────────

class TestFailurePaths:
    @pytest.mark.asyncio
    async def test_empty_command_fails(self, planner):
        result = await planner.plan("")
        assert result.success is False
        assert result.plan is None
        assert result.confidence == 0.0
        assert result.error_code == PlannerErrorCode.EMPTY_COMMAND

    @pytest.mark.asyncio
    async def test_unknown_target_fails(self, planner):
        result = await planner.plan("Open ABCXYZ123")
        assert result.success is False
        assert result.error_code == PlannerErrorCode.UNKNOWN_TARGET

    @pytest.mark.asyncio
    async def test_mixed_intents_succeeds(self, planner):
        result = await planner.plan("Open Chrome then close Spotify")
        assert result.success is True
        assert len(result.plan.steps) == 2
        assert result.plan.steps[0].action == "application.open"
        assert result.plan.steps[1].action == "application.close"

    @pytest.mark.asyncio
    async def test_unknown_intent_fails(self, planner):
        result = await planner.plan("Destroy Chrome")
        assert result.success is False
        assert result.error_code == PlannerErrorCode.UNKNOWN_INTENT

    @pytest.mark.asyncio
    async def test_failure_has_no_plan(self, planner):
        result = await planner.plan("Open UNKNOWN")
        assert result.plan is None

    @pytest.mark.asyncio
    async def test_shell_metachar_fails(self, planner):
        result = await planner.plan("Open Chrome && del C:\\")
        assert result.success is False
        assert result.error_code == PlannerErrorCode.TOKENIZATION_ERROR
