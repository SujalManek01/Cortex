"""Unit tests: TargetResolver — Sprint 003."""
from __future__ import annotations

from types import MappingProxyType

import pytest

from backend.config.config_loader import AppEntry, ReadOnlyConfig
from pydantic import ValidationError
from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.planner.target_resolver import TargetResolver
from backend.models.resolved_action import ResolvedAction
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry


# ── Test registries ────────────────────────────────────────────────────────────

def _make_resolver(
    apps: tuple[AppEntry, ...] | None = None,
    aliases: dict | None = None,
    websites: dict | None = None,
) -> TargetResolver:
    """Build a TargetResolver backed by test-only registries."""
    apps = apps or (
        AppEntry(name="Chrome", alias="chrome", executable="chrome.exe", path="C:\\fake\\chrome.exe"),
        AppEntry(name="VS Code", alias="vscode", executable="Code.exe", path="C:\\fake\\Code.exe"),
        AppEntry(name="Notepad", alias="notepad", executable="notepad.exe", path="C:\\Windows\\notepad.exe"),
        AppEntry(name="Spotify", alias="spotify", executable="Spotify.exe", path="C:\\fake\\Spotify.exe"),
    )
    aliases = aliases or {
        "downloads": "C:\\Users\\test\\Downloads",
        "desktop":   "C:\\Users\\test\\Desktop",
        "documents": "C:\\Users\\test\\Documents",
    }
    websites = websites or {
        "github":     "https://github.com",
        "chatgpt":    "https://chat.openai.com",
        "youtube":    "https://youtube.com",
    }
    config = ReadOnlyConfig(
        _apps=apps,
        _aliases=MappingProxyType(aliases),
        _websites=MappingProxyType(websites),
    )
    return TargetResolver(
        app_registry=ApplicationRegistry(config),
        folder_registry=FolderRegistry(config),
        website_registry=WebsiteRegistry(config),
    )


@pytest.fixture
def resolver() -> TargetResolver:
    return _make_resolver()


# ── Application resolution ─────────────────────────────────────────────────────

class TestApplicationResolution:
    def test_chrome_resolves_to_application_open(self, resolver):
        result = resolver.resolve("open", "chrome")
        assert result == ResolvedAction(
            target="chrome",
            capability="application.open",
            resource_type="application",
        )

    def test_vscode_resolves_to_application_open(self, resolver):
        result = resolver.resolve("open", "vscode")
        assert result.capability == "application.open"
        assert result.resource_type == "application"

    def test_close_intent_gives_application_close(self, resolver):
        result = resolver.resolve("close", "chrome")
        assert result.capability == "application.close"
        assert result.resource_type == "application"

    def test_multiple_app_aliases(self, resolver):
        for alias in ["chrome", "vscode", "notepad", "spotify"]:
            result = resolver.resolve("open", alias)
            assert result.resource_type == "application"


# ── Folder resolution ─────────────────────────────────────────────────────────

class TestFolderResolution:
    def test_downloads_resolves_to_folder_open(self, resolver):
        result = resolver.resolve("open", "downloads")
        assert result == ResolvedAction(
            target="downloads",
            capability="folder.open",
            resource_type="folder",
        )

    def test_desktop_resolves_to_folder_open(self, resolver):
        result = resolver.resolve("open", "desktop")
        assert result.capability == "folder.open"
        assert result.resource_type == "folder"

    def test_folder_always_uses_open_capability_regardless_of_intent(self, resolver):
        """Folder.close is not supported; folder.open is always used."""
        result = resolver.resolve("close", "downloads")
        assert result.capability == "folder.open"


# ── Website resolution ─────────────────────────────────────────────────────────

class TestWebsiteResolution:
    def test_github_resolves_to_website_open(self, resolver):
        result = resolver.resolve("open", "github")
        assert result == ResolvedAction(
            target="github",
            capability="website.open",
            resource_type="website",
        )

    def test_chatgpt_resolves_to_website_open(self, resolver):
        result = resolver.resolve("open", "chatgpt")
        assert result.capability == "website.open"
        assert result.resource_type == "website"

    def test_youtube_resolves_to_website_open(self, resolver):
        result = resolver.resolve("open", "youtube")
        assert result.resource_type == "website"


# ── Resolution order ──────────────────────────────────────────────────────────

class TestResolutionOrder:
    def test_app_wins_over_folder(self):
        """If an alias is registered in both app and folder registries,
        app takes priority (checked first)."""
        apps = (AppEntry(name="Clash", alias="downloads", executable="x.exe", path="C:\\x.exe"),)
        aliases = {"downloads": "C:\\Users\\test\\Downloads"}
        resolver = _make_resolver(apps=apps, aliases=aliases, websites={})
        # Both match — should raise AMBIGUOUS_TARGET, not silently pick one
        with pytest.raises(PlanningError) as exc:
            resolver.resolve("open", "downloads")
        assert exc.value.error_code == PlannerErrorCode.AMBIGUOUS_TARGET


# ── Unknown target ─────────────────────────────────────────────────────────────

class TestUnknownTarget:
    def test_unregistered_target_raises(self, resolver):
        with pytest.raises(PlanningError) as exc:
            resolver.resolve("open", "abcxyz123")
        assert exc.value.error_code == PlannerErrorCode.UNKNOWN_TARGET

    def test_error_message_contains_target(self, resolver):
        with pytest.raises(PlanningError) as exc:
            resolver.resolve("open", "notaresource")
        assert "notaresource" in str(exc.value)


# ── Ambiguous target ──────────────────────────────────────────────────────────

class TestAmbiguousTarget:
    def test_target_in_multiple_registries_raises(self):
        apps = (AppEntry(name="GitHub App", alias="github", executable="github.exe", path="C:\\github.exe"),)
        websites = {"github": "https://github.com"}
        resolver = _make_resolver(apps=apps, aliases={}, websites=websites)
        with pytest.raises(PlanningError) as exc:
            resolver.resolve("open", "github")
        assert exc.value.error_code == PlannerErrorCode.AMBIGUOUS_TARGET


# ── resolve_all ───────────────────────────────────────────────────────────────

class TestResolveAll:
    def test_resolves_all_targets(self, resolver):
        results = resolver.resolve_all("open", ["chrome", "github", "downloads"])
        assert len(results) == 3
        assert results[0].resource_type == "application"
        assert results[1].resource_type == "website"
        assert results[2].resource_type == "folder"

    def test_preserves_order(self, resolver):
        results = resolver.resolve_all("open", ["downloads", "chrome", "github"])
        assert [r.target for r in results] == ["downloads", "chrome", "github"]

    def test_fails_fast_on_unknown(self, resolver):
        with pytest.raises(PlanningError) as exc:
            resolver.resolve_all("open", ["chrome", "unknownthing", "github"])
        assert exc.value.error_code == PlannerErrorCode.UNKNOWN_TARGET


# ── ResolvedAction model ───────────────────────────────────────────────────

class TestResolvedActionModel:
    def test_equality(self):
        a = ResolvedAction(target="chrome", capability="application.open", resource_type="application")
        b = ResolvedAction(target="chrome", capability="application.open", resource_type="application")
        assert a == b

    def test_frozen(self):
        rt = ResolvedAction(target="chrome", capability="application.open", resource_type="application")
        with pytest.raises((AttributeError, TypeError, ValidationError)):
            rt.target = "vscode"  # type: ignore[misc]
