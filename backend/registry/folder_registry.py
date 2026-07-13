"""FolderRegistry — stores registered folder aliases and their filesystem paths.

Sprint 002 introduces specialized registries to separate domain models from configuration parsing.
"""
from __future__ import annotations

from backend.config.config_loader import ReadOnlyConfig


class FolderRegistry:
    """Registry for discovering and resolving folder configurations."""

    def __init__(self, config: ReadOnlyConfig) -> None:
        self._config = config

    def get(self, alias: str) -> str | None:
        """Return the resolved absolute path for the given alias, or None if not registered."""
        return self._config.get_alias(alias)

    def is_registered(self, alias: str) -> bool:
        """Return True if a folder is registered under the given alias."""
        return self.get(alias) is not None

    @property
    def registered_aliases(self) -> list[str]:
        """List of all registered folder aliases."""
        return list(self._config.all_aliases.keys())

    @property
    def all_aliases(self) -> dict[str, str]:
        """All registered alias → path mappings."""
        return dict(self._config.all_aliases)
