"""SafetyPolicy — enforces allow-list and alias-only constraints.

From the spec, the Safety Policy:
  - Application allow-list
  - Alias validation
  - Reject raw executable paths
  - Reject unsafe plans

Engineering Rules:
  10. Allow-list application execution.
  11. Alias-only folder resolution.
  12. Safety before convenience.

Refinement 4: ReadOnlyConfig is injected via constructor.
"""
from __future__ import annotations

import re

from backend.config.config_loader import ReadOnlyConfig
from backend.models.action_plan import ActionPlan
from backend.models.error_codes import ErrorCode

# Detects raw Windows absolute paths and UNC paths anywhere in a parameter value.
# This catches: C:\..., D:\..., \\server\share, and Unix-style /path.
_RAW_PATH_PATTERN: re.Pattern = re.compile(
    r"""
    (
        [A-Za-z]:\\          #  Windows drive root: C:\
        | \\\\               #  UNC path:           \\server
        | /[a-zA-Z0-9_\-]   #  Unix absolute path: /usr
    )
    """,
    re.VERBOSE,
)

# Actions that involve launching or closing applications.
_APPLICATION_ACTIONS: frozenset[str] = frozenset({"application.open", "application.close"})

# Actions that involve folder operations.
_FOLDER_ACTIONS: frozenset[str] = frozenset({"folder.open"})


class SafetyViolation(Exception):
    """Raised when an ActionPlan violates the safety policy.

    Always carries ErrorCode.SAFETY_VIOLATION.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.error_code = ErrorCode.SAFETY_VIOLATION


class SafetyPolicy:
    """Enforces Cortex safety rules before any plan reaches the execution engine.

    Order of checks per step:
    1. No raw paths anywhere in parameters (Rule 11).
    2. Application actions: app alias must be on the allow-list (Rule 10).
    3. Folder actions: folder alias must be in the alias registry (Rule 11).

    Refinement 4: ReadOnlyConfig injected via constructor.
    """

    def __init__(self, config: ReadOnlyConfig) -> None:
        self._config = config

    def enforce(self, plan: ActionPlan) -> None:
        """Enforce all safety rules. Raises SafetyViolation on the first violation.

        Args:
            plan: The validated ActionPlan to inspect.

        Raises:
            SafetyViolation: With a descriptive message explaining the violation.
        """
        for step in plan.steps:
            self._check_no_raw_paths(step.id, step.parameters)

            if step.action in _APPLICATION_ACTIONS:
                self._check_application(step.id, step.parameters)
            elif step.action in _FOLDER_ACTIONS:
                self._check_folder(step.id, step.parameters)

    # ── Private safety checks ──────────────────────────────────────────────────

    def _check_no_raw_paths(self, step_id: str, parameters: dict) -> None:
        """Reject any parameter value that looks like a raw file system path.

        Engineering Rule 11: Alias-only folder resolution.
        Engineering Rule 12: Safety before convenience.
        """
        for key, value in parameters.items():
            if isinstance(value, str) and _RAW_PATH_PATTERN.search(value):
                raise SafetyViolation(
                    f"Step '{step_id}': parameter '{key}' contains a raw path "
                    f"('{value}'). Raw file system paths are not permitted. "
                    "Use a registered alias instead. "
                    "(Engineering Rule 11: Alias-only folder resolution.)"
                )

    def _check_application(self, step_id: str, parameters: dict) -> None:
        """Verify the app alias is on the allow-list.

        Engineering Rule 10: Allow-list application execution.
        """
        app_alias = parameters.get("app")
        if not app_alias:
            raise SafetyViolation(
                f"Step '{step_id}': application actions require an 'app' parameter."
            )
        if not isinstance(app_alias, str):
            raise SafetyViolation(
                f"Step '{step_id}': 'app' parameter must be a string, "
                f"got {type(app_alias).__name__}."
            )
        if self._config.get_app(app_alias) is None:
            raise SafetyViolation(
                f"Step '{step_id}': application '{app_alias}' is not on the "
                "allow-list. Only registered applications may be launched or closed. "
                "(Engineering Rule 10: Allow-list application execution.) "
                f"Registered apps: {[a.alias for a in self._config.all_apps]}."
            )

    def _check_folder(self, step_id: str, parameters: dict) -> None:
        """Verify the folder alias is in the alias registry.

        Engineering Rule 11: Alias-only folder resolution.
        """
        alias = parameters.get("alias")
        if not alias:
            raise SafetyViolation(
                f"Step '{step_id}': folder actions require an 'alias' parameter."
            )
        if not isinstance(alias, str):
            raise SafetyViolation(
                f"Step '{step_id}': 'alias' parameter must be a string, "
                f"got {type(alias).__name__}."
            )
        if self._config.get_alias(alias) is None:
            raise SafetyViolation(
                f"Step '{step_id}': folder alias '{alias}' is not registered. "
                "Only configured aliases may be used to open folders. "
                "(Engineering Rule 11: Alias-only folder resolution.) "
                f"Registered aliases: {list(self._config.all_aliases.keys())}."
            )
