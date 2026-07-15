from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Clause(BaseModel):
    """A segment of a natural language command containing a verb and targets."""
    model_config = ConfigDict(frozen=True)

    verb: str | None = None
    targets: list[str] = Field(default_factory=list)


class GrammarTree(BaseModel):
    """The complete syntactic tree representing a command."""
    model_config = ConfigDict(frozen=True)

    clauses: list[Clause] = Field(default_factory=list)
    original_command: str
    normalized_command: str
    metadata: dict[str, str | int] = Field(default_factory=dict)
