"""Unit tests: Specialized registries (ApplicationRegistry, FolderRegistry, WebsiteRegistry).

Tests verify that each specialized registry correctly delegates to ReadOnlyConfig
and exposes a consistent interface for lookup, registration checks, and listing.
"""
from __future__ import annotations

from types import MappingProxyType

import pytest

from backend.config.config_loader import AppEntry, ReadOnlyConfig
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def config_with_data() -> ReadOnlyConfig:
    apps = (
        AppEntry(name="VS Code", alias="vscode", executable="Code.exe", path="C:\\fake\\Code.exe"),
        AppEntry(name="Notepad", alias="notepad", executable="notepad.exe", path="C:\\Windows\\notepad.exe"),
    )
    aliases = MappingProxyType({
        "desktop": "C:\\Users\\test\\Desktop",
        "downloads": "C:\\Users\\test\\Downloads",
    })
    websites = MappingProxyType({
        "google": "https://google.com",
        "github": "https://github.com",
    })
    return ReadOnlyConfig(_apps=apps, _aliases=aliases, _websites=websites)


@pytest.fixture
def empty_config() -> ReadOnlyConfig:
    return ReadOnlyConfig(_apps=(), _aliases=MappingProxyType({}), _websites=MappingProxyType({}))


# ── ApplicationRegistry ──────────────────────────────────────────────────────

class TestApplicationRegistry:
    def test_get_known_app(self, config_with_data):
        reg = ApplicationRegistry(config_with_data)
        app = reg.get("vscode")
        assert app is not None
        assert app.alias == "vscode"
        assert app.name == "VS Code"

    def test_get_unknown_app_returns_none(self, config_with_data):
        reg = ApplicationRegistry(config_with_data)
        assert reg.get("firefox") is None

    def test_is_registered_true(self, config_with_data):
        reg = ApplicationRegistry(config_with_data)
        assert reg.is_registered("notepad") is True

    def test_is_registered_false(self, config_with_data):
        reg = ApplicationRegistry(config_with_data)
        assert reg.is_registered("unknown") is False

    def test_registered_aliases(self, config_with_data):
        reg = ApplicationRegistry(config_with_data)
        aliases = reg.registered_aliases
        assert "vscode" in aliases
        assert "notepad" in aliases

    def test_all_apps_returns_tuple(self, config_with_data):
        reg = ApplicationRegistry(config_with_data)
        all_apps = reg.all_apps
        assert isinstance(all_apps, tuple)
        assert len(all_apps) == 2

    def test_empty_registry(self, empty_config):
        reg = ApplicationRegistry(empty_config)
        assert reg.registered_aliases == []
        assert reg.all_apps == ()


# ── FolderRegistry ────────────────────────────────────────────────────────────

class TestFolderRegistry:
    def test_get_known_folder(self, config_with_data):
        reg = FolderRegistry(config_with_data)
        path = reg.get("desktop")
        assert path == "C:\\Users\\test\\Desktop"

    def test_get_unknown_folder_returns_none(self, config_with_data):
        reg = FolderRegistry(config_with_data)
        assert reg.get("secret") is None

    def test_is_registered_true(self, config_with_data):
        reg = FolderRegistry(config_with_data)
        assert reg.is_registered("downloads") is True

    def test_is_registered_false(self, config_with_data):
        reg = FolderRegistry(config_with_data)
        assert reg.is_registered("nonexistent") is False

    def test_registered_aliases(self, config_with_data):
        reg = FolderRegistry(config_with_data)
        aliases = reg.registered_aliases
        assert "desktop" in aliases
        assert "downloads" in aliases

    def test_all_aliases_returns_dict(self, config_with_data):
        reg = FolderRegistry(config_with_data)
        all_aliases = reg.all_aliases
        assert isinstance(all_aliases, dict)
        assert len(all_aliases) == 2
        assert all_aliases["desktop"] == "C:\\Users\\test\\Desktop"

    def test_empty_registry(self, empty_config):
        reg = FolderRegistry(empty_config)
        assert reg.registered_aliases == []
        assert reg.all_aliases == {}


# ── WebsiteRegistry ──────────────────────────────────────────────────────────

class TestWebsiteRegistry:
    def test_get_known_website(self, config_with_data):
        reg = WebsiteRegistry(config_with_data)
        url = reg.get("google")
        assert url == "https://google.com"

    def test_get_unknown_website_returns_none(self, config_with_data):
        reg = WebsiteRegistry(config_with_data)
        assert reg.get("stackoverflow") is None

    def test_is_registered_true(self, config_with_data):
        reg = WebsiteRegistry(config_with_data)
        assert reg.is_registered("github") is True

    def test_is_registered_false(self, config_with_data):
        reg = WebsiteRegistry(config_with_data)
        assert reg.is_registered("nonexistent") is False

    def test_registered_aliases(self, config_with_data):
        reg = WebsiteRegistry(config_with_data)
        aliases = reg.registered_aliases
        assert "google" in aliases
        assert "github" in aliases

    def test_all_websites_returns_dict(self, config_with_data):
        reg = WebsiteRegistry(config_with_data)
        all_websites = reg.all_websites
        assert isinstance(all_websites, dict)
        assert len(all_websites) == 2
        assert all_websites["github"] == "https://github.com"

    def test_empty_registry(self, empty_config):
        reg = WebsiteRegistry(empty_config)
        assert reg.registered_aliases == []
        assert reg.all_websites == {}
