"""Executor: folder.open

Opens a registered folder alias in Windows Explorer.
Raw paths are rejected by SafetyPolicy before this executor is reached.

Engineering Rules 11, 12: Alias-only folder resolution. Safety before convenience.
"""
from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

from backend.executors.base_executor import BaseExecutor
from backend.models.action_context import ActionContext
from backend.models.action_result import ActionResult
from backend.models.error_codes import ErrorCode


class FolderOpenExecutor(BaseExecutor):
    """Opens a registered folder alias in Windows Explorer.

    Required parameters:
        alias (str): The registered alias name for the folder.
                     Example: "desktop", "downloads", "chatbot_project"

    The alias is resolved to an absolute path via ActionContext.config.
    The resolved path is opened with: explorer.exe <path>

    Engineering Rule 11: Only aliases resolve to folders. Raw paths are
    rejected by SafetyPolicy before this executor is ever reached.
    """

    @property
    def action_name(self) -> str:
        return "folder.open"

    async def execute(
        self,
        context: ActionContext,
        parameters: dict[str, object],
    ) -> ActionResult:
        start = time.monotonic()
        step_id = context.workspace.step_id
        alias = str(parameters.get("alias", "")).strip()

        # Resolve alias → absolute path via config.
        resolved_path = context.config.get_alias(alias)
        if resolved_path is None:
            return ActionResult(
                step_id=step_id,
                success=False,
                message=(
                    f"Folder alias '{alias}' is not registered. "
                    "Add it to config/aliases.json."
                ),
                error_code=ErrorCode.INVALID_ALIAS,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        # Verify the folder exists on disk.
        folder_path = Path(resolved_path)
        if not folder_path.exists():
            context.logger.warning(
                "Folder alias target does not exist",
                step_id=step_id,
                alias=alias,
                resolved_path=resolved_path,
            )
            return ActionResult(
                step_id=step_id,
                success=False,
                message=(
                    f"Folder '{alias}' resolves to '{resolved_path}' "
                    "but that path does not exist on disk."
                ),
                error_code=ErrorCode.INVALID_ALIAS,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        try:
            # Open Explorer at the resolved path (fire-and-forget).
            await asyncio.to_thread(
                subprocess.Popen,
                ["explorer", resolved_path],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.info(
                "Folder opened",
                step_id=step_id,
                alias=alias,
                resolved_path=resolved_path,
                duration_ms=round(duration_ms, 2),
            )
            return ActionResult(
                step_id=step_id,
                success=True,
                message=f"Opened folder '{alias}' ({resolved_path}) in Explorer.",
                duration_ms=duration_ms,
                metadata={"alias": alias, "resolved_path": resolved_path},
            )
        except (OSError, FileNotFoundError) as exc:
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.error(
                "Failed to open folder",
                step_id=step_id,
                alias=alias,
                resolved_path=resolved_path,
                error=str(exc),
            )
            return ActionResult(
                step_id=step_id,
                success=False,
                message=f"Failed to open folder '{alias}': {exc}",
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=duration_ms,
            )
