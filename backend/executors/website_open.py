"""Executor: website.open

Opens a registered website alias in the default system browser.

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
from backend.registry.website_registry import WebsiteRegistry


class WebsiteOpenExecutor(BaseExecutor):
    """Opens a registered website alias in the default browser.

    Required parameters:
        url (str): The registered alias name for the website.
                   Example: "chatgpt", "github", "cortex"

    The alias is resolved to a URL via WebsiteRegistry.
    The resolved URL is opened with: start <url> (Windows)
    """

    def __init__(self, registry: WebsiteRegistry) -> None:
        self._registry = registry

    @property
    def action_name(self) -> str:
        return "website.open"

    async def execute(
        self,
        context: ActionContext,
        parameters: dict[str, object],
    ) -> ActionResult:
        start = time.monotonic()
        step_id = context.workspace.step_id
        # Note: StubPlanner mapped the alias into 'url' parameter for website.open
        alias = str(parameters.get("url", "")).strip()

        # Resolve alias → URL via registry.
        resolved_url = self._registry.get(alias)
        if resolved_url is None:
            return ActionResult(
                step_id=step_id,
                success=False,
                message=(
                    f"Website alias '{alias}' is not registered. "
                    "Add it to config/websites.json."
                ),
                error_code=ErrorCode.INVALID_ALIAS,
                duration_ms=(time.monotonic() - start) * 1000,
            )

        try:
            # Use 'start' to open the URL in the default browser on Windows.
            # Must run with shell=True for 'start' command.
            await asyncio.to_thread(
                subprocess.Popen,
                f'start "" "{resolved_url}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.info(
                "Website opened",
                step_id=step_id,
                alias=alias,
                resolved_url=resolved_url,
                duration_ms=round(duration_ms, 2),
            )
            return ActionResult(
                step_id=step_id,
                success=True,
                message=f"Opened website '{alias}' ({resolved_url}).",
                duration_ms=duration_ms,
                metadata={"alias": alias, "resolved_url": resolved_url},
            )
        except (OSError, FileNotFoundError) as exc:
            duration_ms = (time.monotonic() - start) * 1000
            context.logger.error(
                "Failed to open website",
                step_id=step_id,
                alias=alias,
                resolved_url=resolved_url,
                error=str(exc),
            )
            return ActionResult(
                step_id=step_id,
                success=False,
                message=f"Failed to open website '{alias}': {exc}",
                error_code=ErrorCode.LAUNCH_FAILURE,
                duration_ms=duration_ms,
            )
