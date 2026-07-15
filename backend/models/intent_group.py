from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IntentGroup(BaseModel):
    """A semantic group of targets governed by a single verb/intent."""
    model_config = ConfigDict(frozen=True)

    verb: str | None
    targets: list[str] = Field(default_factory=list)
    sequence_index: int
    source_clause: str
