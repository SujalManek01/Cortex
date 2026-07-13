"""WebsiteRegistry — stores registered website aliases and their URLs.

Sprint 002 introduces specialized registries to separate domain models from configuration parsing.
"""
from __future__ import annotations

from backend.config.config_loader import ReadOnlyConfig


class WebsiteRegistry:
    """Registry for discovering and resolving website configurations."""

    def __init__(self, config: ReadOnlyConfig) -> None:
        self._config = config

    def get(self, alias: str) -> str | None:
        """Return the URL for the given alias, or None if not registered."""
        return self._config.get_website(alias)

    def is_registered(self, alias: str) -> bool:
        """Return True if a website is registered under the given alias."""
        return self.get(alias) is not None

    @property
    def registered_aliases(self) -> list[str]:
        """List of all registered website aliases."""
        return list(self._config.all_websites.keys())

    @property
    def all_websites(self) -> dict[str, str]:
        """All registered alias → URL mappings."""
        return dict(self._config.all_websites)
