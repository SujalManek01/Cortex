"""CapabilityRegistry — wrapper over ActionRegistry.

Sprint 002 introduces the Capability layer. To minimize churn, this registry
inherits from ActionRegistry, effectively acting as an alias.
Future sprints will phase out ActionRegistry entirely.
"""
from __future__ import annotations

from backend.registry.action_registry import ActionRegistry


class CapabilityRegistry(ActionRegistry):
    """Registry for capabilities, inheriting ActionRegistry to avoid codebase churn."""
    pass
