"""Normalizer — second stage of the Natural Language Planning Engine.

Sprint 003: Converts a token stream (from Tokenizer) into a canonical,
normalised token sequence ready for Intent Detection and Target Resolution.

Responsibilities
----------------
SHALL:
  - Load alias mappings from planner_aliases.json
  - Expand multi-word aliases (e.g. "vs", "code" → "vscode")
  - Expand single-word aliases (e.g. "google-chrome" → "chrome")
  - Normalise connectors to the canonical "then"
  - Preserve token order
  - Return a flat, normalised string and a token value list

SHALL NOT:
  - Resolve applications, folders, or websites via registries
  - Detect user intent
  - Create ActionPlans
  - Modify the original token stream in-place

Design note on multi-word alias expansion
------------------------------------------
The Normalizer performs a sliding-window scan over the WORD token values.
It tries progressively shorter sub-sequences starting at each position.
The longest matching alias wins (greedy).

Example:
  Tokens:  [WORD("visual"), WORD("studio"), WORD("code")]
  Aliases: {"visual studio code": "vscode", "visual studio": "vs"}
  Result:  "vscode"   (longest match wins)
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.planner.tokenizer import Token, TokenType


class Normalizer:
    """Normalises a token stream using alias mappings from planner_aliases.json.

    Args:
        config_dir: Path to the directory containing planner_aliases.json.
    """

    #: Canonical connector token after normalisation.
    CANONICAL_CONNECTOR: str = "then"

    def __init__(self, config_dir: Path) -> None:
        self._aliases = self._load_aliases(config_dir)

    # ── Public API ─────────────────────────────────────────────────────────────

    def normalize(self, tokens: list[Token]) -> list[str]:
        """Normalise a token stream into a list of canonical string values.

        - CONNECTOR tokens → canonical "then"
        - WORD token sequences → expanded through alias table (longest match)

        Args:
            tokens: Output from Tokenizer.tokenize().

        Returns:
            Ordered list of normalised string values.
            Example: ["open", "chrome", "then", "github"]

        Raises:
            PlanningError(NORMALIZATION_ERROR): On any normalisation failure.
        """
        if not tokens:
            raise PlanningError(
                "Token stream is empty; cannot normalise.",
                PlannerErrorCode.NORMALIZATION_ERROR,
            )

        try:
            return self._expand_aliases(tokens)
        except PlanningError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PlanningError(
                f"Normalisation failed unexpectedly: {exc}",
                PlannerErrorCode.NORMALIZATION_ERROR,
            ) from exc

    # ── Private helpers ────────────────────────────────────────────────────────

    def _expand_aliases(self, tokens: list[Token]) -> list[str]:
        """Walk the token list, expanding multi-word aliases using greedy matching."""
        result: list[str] = []
        word_values: list[str] = [t.value if t.type == TokenType.WORD else "\x00" for t in tokens]
        # We'll process tokens with index tracking
        i = 0
        while i < len(tokens):
            tok = tokens[i]

            if tok.type == TokenType.CONNECTOR:
                result.append(self.CANONICAL_CONNECTOR)
                i += 1
                continue

            # WORD token: try greedy multi-word alias match
            matched, length = self._match_alias(word_values, i)
            if matched is not None:
                result.append(matched)
                i += length
            else:
                # No alias match — emit the word as-is
                result.append(tok.value)
                i += 1

        return result

    def _match_alias(
        self, word_values: list[str], start: int
    ) -> tuple[str | None, int]:
        """Try to match the longest alias starting at *start*.

        Returns (canonical_value, tokens_consumed) or (None, 0) if no match.
        """
        # How many consecutive WORD slots remain from start?
        max_window = 0
        for j in range(start, len(word_values)):
            if word_values[j] == "\x00":  # connector sentinel
                break
            max_window += 1

        # Try from longest window to shortest
        for window in range(max_window, 0, -1):
            phrase = " ".join(word_values[start : start + window])
            expanded = self._aliases.get(phrase)
            if expanded is not None:
                return expanded, window

        return None, 0

    @staticmethod
    def _load_aliases(config_dir: Path) -> dict[str, str]:
        """Load planner_aliases.json and flatten all resource-type sub-dicts.

        Returns a single dict mapping phrase → canonical_value for all alias
        categories (verbs, applications, folders, websites).
        """
        alias_path = config_dir / "planner_aliases.json"
        if not alias_path.exists():
            raise PlanningError(
                f"planner_aliases.json not found at '{alias_path}'.",
                PlannerErrorCode.NORMALIZATION_ERROR,
            )

        try:
            raw = json.loads(alias_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise PlanningError(
                f"Failed to load planner_aliases.json: {exc}",
                PlannerErrorCode.NORMALIZATION_ERROR,
            ) from exc

        merged: dict[str, str] = {}
        for section in ("verbs", "applications", "folders", "websites"):
            section_data = raw.get(section, {})
            if isinstance(section_data, dict):
                merged.update(section_data)

        return merged
