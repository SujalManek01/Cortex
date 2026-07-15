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


@dataclass(frozen=True)
class GrammarConfig:
    """Configuration for connectors and sequences used by the Grammar Engine."""
    version: str
    connectors: tuple[str, ...]
    sequences: tuple[str, ...]


@dataclass(frozen=True)
class PlannerRulesConfig:
    """Configurable rules and severities for conflict analysis."""
    version: str
    duplicate_action: str
    contradictory_action: str
    redundant_action: str


@dataclass(frozen=True)
class PlannerAliasesConfig:
    """Dictionary mapping target synonyms/aliases to canonical values."""
    version: str
    verbs: MappingProxyType[str, str]
    applications: MappingProxyType[str, str]
    folders: MappingProxyType[str, str]
    websites: MappingProxyType[str, str]


@dataclass
class ReadOnlyConfig:
    """Read-only configuration container injected into ActionContext.

    MappingProxyType is used for aliases to enforce immutability at runtime.
    The _apps tuple is also immutable.
    """

    _apps: tuple[AppEntry, ...]
    _aliases: MappingProxyType  # str -> str (alias name -> resolved path)
    _websites: MappingProxyType # str -> str (alias name -> url)
    grammar: GrammarConfig | None = None
    planner_rules: PlannerRulesConfig | None = None
    planner_aliases: PlannerAliasesConfig | None = None

    def get_app(self, alias: str) -> AppEntry | None:
        """Return the AppEntry for the given alias, or None if not registered."""
        return next((a for a in self._apps if a.alias == alias), None)

    def get_alias(self, alias: str) -> str | None:
        """Return the resolved folder path for the given alias, or None."""
        return self._aliases.get(alias)

    def get_website(self, alias: str) -> str | None:
        """Return the URL for the given website alias, or None."""
        return self._websites.get(alias)

    @property
    def all_apps(self) -> tuple[AppEntry, ...]:
        """All registered applications."""
        return self._apps

    @property
    def all_aliases(self) -> MappingProxyType:
        """All registered folder aliases (read-only mapping)."""
        return self._aliases

    @property
    def all_websites(self) -> MappingProxyType:
        """All registered website aliases (read-only mapping)."""
        return self._websites


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
        websites = self._load_websites()
        grammar = self._load_grammar()
        planner_rules = self._load_planner_rules()
        planner_aliases = self._load_planner_aliases()
        return ReadOnlyConfig(
            _apps=tuple(apps),
            _aliases=MappingProxyType(aliases),
            _websites=MappingProxyType(websites),
            grammar=grammar,
            planner_rules=planner_rules,
            planner_aliases=planner_aliases,
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

        raw_data = json.loads(apps_file.read_text(encoding="utf-8"))
        # Handle Sprint 002 format vs Sprint 001 format
        entries = raw_data.get("entries", []) if isinstance(raw_data, dict) and "version" in raw_data else raw_data

        for entry in entries:
            alias = str(entry.get("alias", "")).strip()
            if not alias:
                continue

            raw_path = str(entry.get("path", "")).strip()
            resolved_path = os.path.expandvars(raw_path.replace("{username}", _USERNAME)) if raw_path else ""

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
        """Load folder aliases from folders.json or aliases.json, resolving {username}."""
        folders_file = self._config_dir / "folders.json"
        aliases_file = self._config_dir / "aliases.json"
        
        target_file = folders_file if folders_file.exists() else aliases_file
        if not target_file.exists():
            return {}

        raw_data = json.loads(target_file.read_text(encoding="utf-8"))
        
        # Sprint 002 format
        if isinstance(raw_data, dict) and "version" in raw_data:
            return {
                str(entry.get("alias", "")).strip(): os.path.expandvars(str(entry.get("path", "")).replace("{username}", _USERNAME))
                for entry in raw_data.get("entries", [])
                if entry.get("alias") and entry.get("path")
            }
        
        # Sprint 001 format (dict mapping)
        return {
            alias: os.path.expandvars(path.replace("{username}", _USERNAME))
            for alias, path in raw_data.items()
            if alias and path
        }

    def _load_websites(self) -> dict[str, str]:
        """Load website aliases from websites.json."""
        websites_file = self._config_dir / "websites.json"
        if not websites_file.exists():
            return {}

        raw_data = json.loads(websites_file.read_text(encoding="utf-8"))
        
        # Sprint 002 format
        if isinstance(raw_data, dict) and "version" in raw_data:
            return {
                str(entry.get("alias", "")).strip(): str(entry.get("url", "")).strip()
                for entry in raw_data.get("entries", [])
                if entry.get("alias") and entry.get("url")
            }
        
        # Sprint 001 fallback format if any
        if isinstance(raw_data, dict):
            return {
                alias: str(url).strip()
                for alias, url in raw_data.items()
                if alias and url
            }
        
        return {}

    def _load_grammar(self) -> GrammarConfig | None:
        """Load grammar connector and sequence specifications."""
        file = self._config_dir / "grammar.json"
        if not file.exists():
            return None
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
            return GrammarConfig(
                version=raw.get("version", "1.0"),
                connectors=tuple(raw.get("connectors", [])),
                sequences=tuple(raw.get("sequences", [])),
            )
        except Exception:
            return None

    def _load_planner_rules(self) -> PlannerRulesConfig | None:
        """Load configurable rules and severities for conflict analysis."""
        file = self._config_dir / "planner_rules.json"
        if not file.exists():
            return None
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
            return PlannerRulesConfig(
                version=raw.get("version", "1.0"),
                duplicate_action=raw.get("duplicate_action", "warning"),
                contradictory_action=raw.get("contradictory_action", "warning"),
                redundant_action=raw.get("redundant_action", "information"),
            )
        except Exception:
            return None

    def _load_planner_aliases(self) -> PlannerAliasesConfig | None:
        """Load verbs, applications, folders, and website alias mappings."""
        file = self._config_dir / "planner_aliases.json"
        if not file.exists():
            return None
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
            return PlannerAliasesConfig(
                version=raw.get("version", "1.0"),
                verbs=MappingProxyType(raw.get("verbs", {})),
                applications=MappingProxyType(raw.get("applications", {})),
                folders=MappingProxyType(raw.get("folders", {})),
                websites=MappingProxyType(raw.get("websites", {})),
            )
        except Exception:
            return None

