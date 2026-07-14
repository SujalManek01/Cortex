"""Tokenizer — first stage of the Natural Language Planning Engine.

Sprint 003: Converts raw user text into a flat list of normalized tokens.

Responsibilities
----------------
SHALL:
  - Split words preserving order
  - Identify CONNECTOR tokens (and, then, ,, &)
  - Collapse redundant whitespace
  - Normalize Unicode whitespace
  - Lowercase all tokens
  - Enforce maximum command length

SHALL NOT:
  - Detect intent
  - Resolve aliases
  - Access registries
  - Create ActionPlans

Token types
-----------
  WORD       — a meaningful lexical unit (e.g. "chrome")
  CONNECTOR  — a separator between sub-commands (e.g. "and", "then", ",", "&")
  UNKNOWN    — an unrecognised symbol; triggers TOKENIZATION_ERROR
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from backend.planner.planning_errors import PlannerErrorCode, PlanningError

# ── Constants ─────────────────────────────────────────────────────────────────

#: Hard ceiling for raw command input.
MAX_COMMAND_CHARS: int = 500

#: Shell metacharacters that must be rejected before any interpretation.
#: Note: bare '&' is a CONNECTOR; '&&' is a shell metacharacter.
_SHELL_METACHAR_PATTERN: re.Pattern = re.compile(
    r"&&|[|;`$<>]",
)

#: Single-character connectors that stand alone as tokens.
_CHAR_CONNECTORS: frozenset[str] = frozenset({",", "&"})

#: Word connectors (lowercased match).
_WORD_CONNECTORS: frozenset[str] = frozenset({"and", "then", "afterwards"})


class TokenType(StrEnum):
    WORD      = "WORD"
    CONNECTOR = "CONNECTOR"
    UNKNOWN   = "UNKNOWN"


@dataclass(frozen=True)
class Token:
    """A single lexical unit produced by the Tokenizer."""
    type: TokenType
    value: str

    def __repr__(self) -> str:
        return f"{self.type}({self.value!r})"


# ── Tokenizer ─────────────────────────────────────────────────────────────────

class Tokenizer:
    """Converts raw command text into a list of Token objects.

    This class has no external dependencies — it performs only lexical analysis.
    """

    def tokenize(self, raw: str) -> list[Token]:
        """Tokenize *raw* command text.

        Args:
            raw: The raw user-supplied command string.

        Returns:
            An ordered list of Token objects.

        Raises:
            PlanningError(EMPTY_COMMAND): If the command is empty after trimming.
            PlanningError(COMMAND_TOO_LONG): If the command exceeds MAX_COMMAND_CHARS.
            PlanningError(TOKENIZATION_ERROR): If the command contains shell metacharacters
                                               or other unacceptable input.
        """
        # ── 1. Guard: empty ───────────────────────────────────────────────────
        if not raw or not raw.strip():
            raise PlanningError(
                "Command must not be empty.",
                PlannerErrorCode.EMPTY_COMMAND,
            )

        # ── 2. Guard: length ─────────────────────────────────────────────────
        if len(raw) > MAX_COMMAND_CHARS:
            raise PlanningError(
                f"Command is too long ({len(raw)} characters). "
                f"Maximum allowed: {MAX_COMMAND_CHARS}.",
                PlannerErrorCode.COMMAND_TOO_LONG,
            )

        # ── 3. Reject shell metacharacters (before any other processing) ─────
        if _SHELL_METACHAR_PATTERN.search(raw):
            raise PlanningError(
                "Command contains invalid characters (shell metacharacters are not allowed).",
                PlannerErrorCode.TOKENIZATION_ERROR,
            )

        # ── 4. Unicode normalisation ─────────────────────────────────────────
        normalized = unicodedata.normalize("NFKC", raw)

        # ── 5. Lowercase ─────────────────────────────────────────────────────
        normalized = normalized.lower()

        # ── 6. Replace comma with ' , ' so it survives word splitting ─────────
        normalized = normalized.replace(",", " , ")

        # ── 7. Collapse whitespace ────────────────────────────────────────────
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # ── 8. Split into raw words ──────────────────────────────────────────
        raw_words = normalized.split(" ")

        # ── 9. Classify each word ────────────────────────────────────────────
        tokens: list[Token] = []
        for word in raw_words:
            if not word:
                continue
            token_type = self._classify(word)
            if token_type == TokenType.UNKNOWN:
                raise PlanningError(
                    f"Unrecognised token '{word}' in command.",
                    PlannerErrorCode.TOKENIZATION_ERROR,
                )
            tokens.append(Token(type=token_type, value=word))

        if not tokens:
            raise PlanningError(
                "Command produced no tokens after processing.",
                PlannerErrorCode.EMPTY_COMMAND,
            )

        return tokens

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _classify(word: str) -> TokenType:
        """Classify a single lowercased word into a TokenType."""
        if word in _CHAR_CONNECTORS or word in _WORD_CONNECTORS:
            return TokenType.CONNECTOR
        # Reject anything that is not alphanumeric or hyphen/apostrophe
        # (these appear legitimately in application names like "vs-code")
        if re.fullmatch(r"[a-z0-9][a-z0-9\-']*", word):
            return TokenType.WORD
        return TokenType.UNKNOWN
