"""Executor: application.close

Terminates a running application by alias using Windows taskkill.
Uses /F (force) to ensure the process is terminated even if it does not
respond to close requests.

Engineering Rules 10, 12: Allow-list only. Safety before convenience.
"""
from __future__ import annotations

import asyncio
import subprocess
import time

from backend.executors.base_executor import BaseExecutor
from backend.models.action_context import ActionContext
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode


class ApplicationCloseExecutor(BaseExecutor):
    """Terminates a running application by alias using taskkill.

    Required parameters:
        app (str): The registered alias of the application to close.
                   Example: "vscode", "chrome", "notepad"

    Uses: taskkill /F /IM <executable_name>
    /F = Force terminate (does not wait for graceful close).
    /IM = Image name (executable filename, e.g. "Code.exe").

    Returns success even if the process was not running (taskkill exit code 128
    means "process not found" — treated as a no-op success).
    """

    @property
    def action_name(self) -> str:
        return "application.close"

    async def execute(
        self,
        context: ActionContext,
        parameters: dict[str, object],
    ) -> ActionResult:
        start = time.monotonic()
        step_id = context.workspace.step_id
        app_alias = str(parameters.get("app", "")).strip()

        # Resolve alias → AppEntry.
        app_entry = context.config.get_app(app_alias)
        if app_entry is None:
            return ActionResult(
                step_id=step_id,
                success=False,
                message=f"Application '{app_alias}' is not registered in the allow-list.",
                error_code=ErrorCode.UNKNOWN_APPLICATION,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        if not app_entry.executable:
            return ActionResult(
                step_id=step_id,
                success=False,
                message=(
                    f"No executable name configured for '{app_alias}'. "
                    "Cannot determine process image name for taskkill."
                ),
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                ["taskkill", "/F", "/IM", app_entry.executable],
                capture_output=True,
                text=True,
                timeout=10,  # taskkill itself should complete in well under 10s.
            )
            duration_ms = (time.monotonic() - start) * 1000

            # Exit code 0 = success, 128 = process not found (already closed).
            # Both are treated as a successful outcome.
            if proc.returncode in (0, 128):
                was_running = proc.returncode == 0
                context.logger.info(
                    "Application closed" if was_running else "Application was not running",
                    step_id=step_id,
                    app=app_alias,
                    executable=app_entry.executable,
                    duration_ms=round(duration_ms, 2),
                )
                return ActionResult(
                    step_id=step_id,
                    success=True,
                    message=(
                        f"Closed '{app_entry.name}' successfully."
                        if was_running
                        else f"'{app_entry.name}' was not running."
                    ),
                    duration_ms=duration_ms,
                    metadata={
                        "app": app_alias,
                        "executable": app_entry.executable,
                        "was_running": was_running,
                    },
                )
            else:
                context.logger.error(
                    "taskkill failed",
                    step_id=step_id,
                    app=app_alias,
                    executable=app_entry.executable,
                    returncode=proc.returncode,
                    stderr=proc.stderr.strip(),
                )
                return ActionResult(
                    step_id=step_id,
                    success=False,
                    message=(
                        f"Failed to close '{app_entry.name}'. "
                        f"taskkill exited with code {proc.returncode}: {proc.stderr.strip()}"
                    ),
                    error_code=ErrorCode.LAUNCH_FAILURE,
                    duration_ms=duration_ms,
                    metadata={"returncode": proc.returncode, "stderr": proc.stderr.strip()},
                )
        except (OSError, FileNotFoundError) as exc:
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.error(
                "taskkill not available",
                step_id=step_id,
                error=str(exc),
            )
            return ActionResult(
                step_id=step_id,
                success=False,
                message=f"taskkill is not available on this system: {exc}",
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=duration_ms,
            )
