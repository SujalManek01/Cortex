"""Configuration loader — loads, discovers, and merges application and alias config.

Engineering Rule 8: Configuration lives outside code.
Refinement 3: Auto-discovery is attempted first; apps.json supplements/overrides.
Refinement 4: ConfigLoader is instantiated once and injected via constructor.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from backend.config.app_discovery import discover_installed_apps

_USERNAME: str = os.environ.get("USERNAME", os.environ.get("COMPUTERNAME", "user"))


@dataclass(frozen=True)
class AppEntry:
    """A registered, launchable application entry."""

    name: str
    alias: str
    executable: str
    path: str  # Absolute path to the executable. May be empty if not found on disk.


@dataclass
class ReadOnlyConfig:
    """Read-only configuration container injected into ActionContext.

    MappingProxyType is used for aliases to enforce immutability at runtime.
    The _apps tuple is also immutable.
    """

    _apps: tuple[AppEntry, ...]
    _aliases: MappingProxyType  # str -> str (alias name -> resolved path)

    def get_app(self, alias: str) -> AppEntry | None:
        """Return the AppEntry for the given alias, or None if not registered."""
        return next((a for a in self._apps if a.alias == alias), None)

    def get_alias(self, alias: str) -> str | None:
        """Return the resolved folder path for the given alias, or None."""
        return self._aliases.get(alias)

    @property
    def all_apps(self) -> tuple[AppEntry, ...]:
        """All registered applications."""
        return self._apps

    @property
    def all_aliases(self) -> MappingProxyType:
        """All registered folder aliases (read-only mapping)."""
        return self._aliases


class ConfigLoader:
    """Loads configuration from disk and produces a ReadOnlyConfig.

    Merge strategy for apps:
    1. Auto-discovery runs first (Refinement 3).
    2. apps.json entries with a non-empty path override discovered entries.
    3. apps.json entries with an empty path register the alias only if
       auto-discovery did not already find it.

    The config_dir should point to the project's config/ directory.
    """

    def __init__(self, config_dir: Path) -> None:
        self._config_dir = config_dir

    def load(self) -> ReadOnlyConfig:
        """Load, discover, merge, and return an immutable ReadOnlyConfig."""
        apps = self._load_apps()
        aliases = self._load_aliases()
        return ReadOnlyConfig(
            _apps=tuple(apps),
            _aliases=MappingProxyType(aliases),
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _load_apps(self) -> list[AppEntry]:
        """Merge auto-discovered apps with apps.json entries."""
        # Step 1: Auto-discovery populates the base registry (keyed by alias).
        merged: dict[str, AppEntry] = {
            app.alias: AppEntry(
                name=app.name,
                alias=app.alias,
                executable=app.executable,
                path=app.path,
            )
            for app in discover_installed_apps()
        }

        # Step 2: Apply apps.json overrides/additions.
        apps_file = self._config_dir / "apps.json"
        if not apps_file.exists():
            return list(merged.values())

        raw: list[dict] = json.loads(apps_file.read_text(encoding="utf-8"))
        for entry in raw:
            alias = str(entry.get("alias", "")).strip()
            if not alias:
                continue

            raw_path = str(entry.get("path", "")).strip()
            resolved_path = raw_path.replace("{username}", _USERNAME) if raw_path else ""

            if resolved_path:
                # Explicit path in apps.json always wins over discovery.
                merged[alias] = AppEntry(
                    name=str(entry.get("name", alias)),
                    alias=alias,
                    executable=str(entry.get("executable", "")),
                    path=resolved_path,
                )
            elif alias not in merged:
                # Register the alias even without a path (executor will try by name).
                merged[alias] = AppEntry(
                    name=str(entry.get("name", alias)),
                    alias=alias,
                    executable=str(entry.get("executable", "")),
                    path="",
                )

        return list(merged.values())

    def _load_aliases(self) -> dict[str, str]:
        """Load folder aliases from aliases.json, resolving {username}."""
        aliases_file = self._config_dir / "aliases.json"
        if not aliases_file.exists():
            return {}

        raw: dict[str, str] = json.loads(aliases_file.read_text(encoding="utf-8"))
        return {
            alias: path.replace("{username}", _USERNAME)
            for alias, path in raw.items()
            if alias and path
        }
