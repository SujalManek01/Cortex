"""Executor: application.open

Launches a registered application by alias using a non-blocking Popen call.
The application is launched as a detached process — Cortex does not wait
for it to exit.

Engineering Rules 10, 12: Allow-list only. Safety before convenience.
Refinement 3: Path resolved from config (auto-discovered or apps.json).
"""
from __future__ import annotations

import asyncio
import subprocess
import time

from backend.executors.base_executor import BaseExecutor
from backend.models.action_context import ActionContext
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode


class ApplicationOpenExecutor(BaseExecutor):
    """Launches a registered application by alias.

    Required parameters:
        app (str): The registered alias of the application to open.
                   Example: "vscode", "chrome", "notepad"

    The executor resolves the alias to an executable path via ActionContext.config,
    then launches it with subprocess.Popen (fire-and-forget).
    """

    @property
    def action_name(self) -> str:
        return "application.open"

    async def execute(
        self,
        context: ActionContext,
        parameters: dict[str, object],
    ) -> ActionResult:
        start = time.monotonic()
        step_id = context.workspace.step_id
        app_alias = str(parameters.get("app", "")).strip()

        # Resolve alias → AppEntry via config.
        app_entry = context.config.get_app(app_alias)
        if app_entry is None:
            return ActionResult(
                step_id=step_id,
                success=False,
                message=f"Application '{app_alias}' is not registered in the allow-list.",
                error_code=ErrorCode.UNKNOWN_APPLICATION,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        # Determine the executable path.
        # Prefer the resolved path; fall back to the executable name (PATH lookup).
        launch_target = app_entry.path or app_entry.executable
        if not launch_target:
            return ActionResult(
                step_id=step_id,
                success=False,
                message=(
                    f"No executable path or name configured for '{app_alias}'. "
                    "Add a path to config/apps.json."
                ),
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        try:
            # Fire-and-forget: Popen returns immediately after the OS forks the process.
            # We run it in a thread to avoid blocking the event loop.
            await asyncio.to_thread(
                subprocess.Popen,
                [launch_target],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.info(
                "Application launched",
                step_id=step_id,
                app=app_alias,
                path=launch_target,
                duration_ms=round(duration_ms, 2),
            )
            return ActionResult(
                step_id=step_id,
                success=True,
                message=f"Launched '{app_entry.name}' successfully.",
                duration_ms=duration_ms,
                metadata={"app": app_alias, "path": launch_target},
            )
        except (OSError, FileNotFoundError) as exc:
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.error(
                "Application launch failed",
                step_id=step_id,
                app=app_alias,
                path=launch_target,
                error=str(exc),
            )
            return ActionResult(
                step_id=step_id,
                success=False,
                message=f"Failed to launch '{app_entry.name}': {exc}",
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=duration_ms,
            )
