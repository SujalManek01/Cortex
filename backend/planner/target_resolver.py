"""TargetResolver — fourth stage of the Natural Language Planning Engine.

Sprint 003: Maps normalised target tokens to registered Cortex resources.

This is the ONLY planning stage that is permitted to access registries.

Responsibilities
----------------
SHALL:
  - Resolve targets through ApplicationRegistry, FolderRegistry, WebsiteRegistry
  - Follow the spec-defined resolution order:
      1. ApplicationRegistry
      2. FolderRegistry
      3. WebsiteRegistry
  - Return a ResolvedTarget per target string
  - Raise UNKNOWN_TARGET for unrecognised targets
  - Raise AMBIGUOUS_TARGET if a target matches more than one registry
    (e.g. an alias registered in both ApplicationRegistry and FolderRegistry)

SHALL NOT:
  - Perform filesystem scanning
  - Access the internet
  - Create ActionPlans
  - Perform tokenisation or intent detection

Resolution order
-----------------
ApplicationRegistry is checked first (most specific).
FolderRegistry is checked second.
WebsiteRegistry is checked last.
The first successful match wins.

An AMBIGUOUS_TARGET error is raised only when a target matches in more than
one registry simultaneously — the configuration files themselves would need to
contain duplicates for this to occur.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry

# ── Capability constants ───────────────────────────────────────────────────────

_CAPABILITY_APP_OPEN    = "application.open"
_CAPABILITY_APP_CLOSE   = "application.close"
_CAPABILITY_FOLDER_OPEN = "folder.open"
_CAPABILITY_WEBSITE_OPEN = "website.open"


@dataclass(frozen=True)
class ResolvedTarget:
    """The result of resolving a normalised target string against registries.

    Fields
    ------
    alias       : The canonical alias used for registry lookup.
    capability  : The Cortex capability string (e.g. "application.open").
    resource_type : One of "application", "folder", "website".
    """
    alias: str
    capability: str
    resource_type: str


class TargetResolver:
    """Resolves normalised target strings to registered Cortex resources.

    Args:
        app_registry:     ApplicationRegistry instance.
        folder_registry:  FolderRegistry instance.
        website_registry: WebsiteRegistry instance.
    """

    def __init__(
        self,
        app_registry: ApplicationRegistry,
        folder_registry: FolderRegistry,
        website_registry: WebsiteRegistry,
    ) -> None:
        self._apps = app_registry
        self._folders = folder_registry
        self._websites = website_registry

    def resolve(self, intent: str, target: str) -> ResolvedTarget:
        """Resolve a single normalised target string for a given intent.

        Args:
            intent: Canonical intent ("open" | "close").
            target: Normalised target alias (e.g. "chrome", "downloads", "github").

        Returns:
            ResolvedTarget with capability and resource_type populated.

        Raises:
            PlanningError(UNKNOWN_TARGET): If the target is not registered.
            PlanningError(AMBIGUOUS_TARGET): If the target matches multiple registries.
        """
        matches: list[ResolvedTarget] = []

        # ── 1. Application Registry ───────────────────────────────────────────
        if self._apps.is_registered(target):
            cap = _CAPABILITY_APP_OPEN if intent == "open" else _CAPABILITY_APP_CLOSE
            matches.append(ResolvedTarget(
                alias=target,
                capability=cap,
                resource_type="application",
            ))

        # ── 2. Folder Registry ────────────────────────────────────────────────
        if self._folders.is_registered(target):
            matches.append(ResolvedTarget(
                alias=target,
                capability=_CAPABILITY_FOLDER_OPEN,
                resource_type="folder",
            ))

        # ── 3. Website Registry ───────────────────────────────────────────────
        if self._websites.is_registered(target):
            matches.append(ResolvedTarget(
                alias=target,
                capability=_CAPABILITY_WEBSITE_OPEN,
                resource_type="website",
            ))

        # ── Evaluate results ──────────────────────────────────────────────────
        if len(matches) == 0:
            raise PlanningError(
                f"Target '{target}' is not registered in any registry "
                f"(applications, folders, or websites).",
                PlannerErrorCode.UNKNOWN_TARGET,
            )

        if len(matches) > 1:
            types = [m.resource_type for m in matches]
            raise PlanningError(
                f"Target '{target}' is ambiguous: it matches multiple registries "
                f"({types}). Please use a more specific alias.",
                PlannerErrorCode.AMBIGUOUS_TARGET,
            )

        return matches[0]

    def resolve_all(
        self, intent: str, targets: list[str]
    ) -> list[ResolvedTarget]:
        """Resolve all targets for a sub-command, preserving order.

        Args:
            intent:  Canonical intent ("open" | "close").
            targets: Ordered list of normalised target aliases.

        Returns:
            Ordered list of ResolvedTarget objects.

        Raises:
            PlanningError(UNKNOWN_TARGET): On the first unresolvable target.
            PlanningError(AMBIGUOUS_TARGET): On the first ambiguous target.
        """
        return [self.resolve(intent, t) for t in targets]
