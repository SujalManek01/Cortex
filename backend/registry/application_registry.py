"""ApplicationRegistry — stores application aliases, executable paths, and discovery metadata.

Sprint 002 introduces specialized registries to separate domain models from configuration parsing.
"""
from __future__ import annotations

from backend.config.config_loader import AppEntry, ReadOnlyConfig


class ApplicationRegistry:
    """Registry for discovering and resolving application configurations."""

    def __init__(self, config: ReadOnlyConfig) -> None:
        self._config = config

    def get(self, alias: str) -> AppEntry | None:
        """Return the AppEntry for the given alias, or None if not registered."""
        return self._config.get_app(alias)

    def is_registered(self, alias: str) -> bool:
        """Return True if an application is registered under the given alias."""
        return self.get(alias) is not None

    @property
    def registered_aliases(self) -> list[str]:
        """List of all registered application aliases."""
        return [app.alias for app in self._config.all_apps]

    @property
    def all_apps(self) -> tuple[AppEntry, ...]:
        """All registered AppEntry objects."""
        return self._config.all_apps
