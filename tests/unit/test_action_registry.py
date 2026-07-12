"""Unit tests: ActionRegistry.

Covers registration, lookup, duplicate detection, and unknown action errors.
"""
from __future__ import annotations

import pytest

from backend.executors.application_open import ApplicationOpenExecutor
from backend.executors.folder_open import FolderOpenExecutor
from backend.registry.action_registry import (
    ActionRegistry,
    RegistrationError,
    UnknownActionError,
)


class TestActionRegistryRegistration:
    def test_register_executor(self):
        registry = ActionRegistry()
        executor = ApplicationOpenExecutor()
        registry.register(executor)
        assert registry.is_registered("application.open")

    def test_register_multiple_executors(self):
        registry = ActionRegistry()
        registry.register(ApplicationOpenExecutor())
        registry.register(FolderOpenExecutor())
        assert registry.is_registered("application.open")
        assert registry.is_registered("folder.open")

    def test_duplicate_registration_raises(self):
        registry = ActionRegistry()
        registry.register(ApplicationOpenExecutor())
        with pytest.raises(RegistrationError) as exc_info:
            registry.register(ApplicationOpenExecutor())
        assert "application.open" in str(exc_info.value)

    def test_registered_actions_sorted(self):
        registry = ActionRegistry()
        registry.register(FolderOpenExecutor())
        registry.register(ApplicationOpenExecutor())
        actions = registry.registered_actions
        assert actions == sorted(actions)


class TestActionRegistryLookup:
    def test_get_registered_executor(self):
        registry = ActionRegistry()
        executor = ApplicationOpenExecutor()
        registry.register(executor)
        result = registry.get("application.open")
        assert result is executor

    def test_get_unknown_action_raises(self):
        registry = ActionRegistry()
        with pytest.raises(UnknownActionError) as exc_info:
            registry.get("browser.open")
        assert exc_info.value.action_name == "browser.open"

    def test_is_registered_true(self):
        registry = ActionRegistry()
        registry.register(ApplicationOpenExecutor())
        assert registry.is_registered("application.open") is True

    def test_is_registered_false(self):
        registry = ActionRegistry()
        assert registry.is_registered("nonexistent.action") is False

    def test_empty_registry_has_no_actions(self):
        registry = ActionRegistry()
        assert registry.registered_actions == []

    def test_action_name_from_executor(self):
        """Verify executor action_name property is what gets registered."""
        executor = ApplicationOpenExecutor()
        assert executor.action_name == "application.open"
        registry = ActionRegistry()
        registry.register(executor)
        assert registry.is_registered(executor.action_name)
