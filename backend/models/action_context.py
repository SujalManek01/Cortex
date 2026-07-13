"""ActionContext — dependency container passed to every executor at execution time.

Engineering Rule 6: Every executor receives ActionContext.
Engineering Rule 8: Configuration lives outside code.

WorkspaceMetadata includes step_id so executors can self-identify their result
without needing the step ID passed as a separate parameter.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # TYPE_CHECKING-only imports prevent circular dependencies at runtime.
    # backend/models must remain the foundation layer with no runtime deps on
    # backend/logging or backend/config.
    from backend.config.config_loader import ReadOnlyConfig
    from backend.logging.logger import StructuredLogger


@dataclass(frozen=True)
class WorkspaceMetadata:
    """Read-only plan and step metadata available to executors during execution.

    Recreated per step so executors always have the correct step_id context.
    """

    plan_id: uuid.UUID
    goal: str
    version: str
    step_id: str = field(default="")


@dataclass(frozen=True)
class ActionContext:
    """Dependency container injected into every executor at execution time.

    Executors must treat this as read-only. They must not cache or store
    it beyond the scope of a single execute() call.

    Refinement 4: All services are injected; no hidden globals.
    """

    logger: StructuredLogger
    config: ReadOnlyConfig
    workspace: WorkspaceMetadata
