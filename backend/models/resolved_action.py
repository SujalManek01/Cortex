from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict


class ResolvedAction(BaseModel):
    """An action resolved by the TargetResolver.

    This replaces the legacy ResolvedTarget dataclass with a strict, frozen
    Pydantic model.
    """

    model_config = ConfigDict(frozen=True)

    capability: str
    target: str
    resource_type: Literal["application", "folder", "website"]
