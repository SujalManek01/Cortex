"""IntentDetector — third stage of the Natural Language Planning Engine.

Sprint 003: Converts normalised verb tokens into canonical Cortex intents.

Responsibilities
----------------
SHALL:
  - Map normalised verbs to canonical intents ("open" | "close")
  - Detect the intent for each sub-command in the normalised token stream
  - Raise UNKNOWN_INTENT for unrecognised verbs
  - Raise MIXED_INTENTS when multiple distinct canonical intents appear
    in a single command (deferred to Sprint 004; currently rejected)

SHALL NOT:
  - Resolve resource targets
  - Access registries
  - Create ActionPlans

Intent model
-------------
Sprint 003 supports exactly two canonical intents:

  "open"   — open/launch/start/run a resource
  "close"  — close/exit/quit a running application

All verb synonyms are resolved by the Normalizer before this stage runs.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.planner.planning_errors import PlannerErrorCode, PlanningError

# ── Canonical intents ─────────────────────────────────────────────────────────

#: Every normalised verb that maps to "open".
_OPEN_VERBS: frozenset[str] = frozenset({"open"})

#: Every normalised verb that maps to "close".
#: "exit" and "quit" are normalised to "close" by the Normalizer (via aliases).
_CLOSE_VERBS: frozenset[str] = frozenset({"close"})

#: Union of all recognised verbs.
_ALL_VERBS: frozenset[str] = _OPEN_VERBS | _CLOSE_VERBS

#: Token value that separates sub-commands after normalisation.
_CANONICAL_CONNECTOR: str = "then"


@dataclass(frozen=True)
class SubCommand:
    """A single intent + its target tokens, extracted from the normalised stream."""
    intent: str          # "open" | "close"
    targets: list[str]   # Ordered list of target aliases


class IntentDetector:
    """Extracts canonical intents and their target lists from a normalised token stream.

    Input: A flat list of normalised string values from the Normalizer.
    Output: An ordered list of SubCommand objects.

    Example:
        Input:  ["open", "chrome", "then", "github"]
        Output: [SubCommand(intent="open", targets=["chrome"]),
                 SubCommand(intent="open", targets=["github"])]
    """

    def detect(self, normalised_tokens: list[str]) -> list[SubCommand]:
        """Detect intents and targets from the normalised token stream.

        Args:
            normalised_tokens: Output from Normalizer.normalize().

        Returns:
            Ordered list of SubCommand objects, one per logical sub-command.

        Raises:
            PlanningError(UNKNOWN_INTENT): If the first token is not a recognised verb,
                                           or if a token after a connector is unrecognised.
            PlanningError(MIXED_INTENTS): If more than one canonical intent is detected.
            PlanningError(EMPTY_COMMAND): If the token stream is empty.
        """
        if not normalised_tokens:
            raise PlanningError(
                "Token stream is empty; cannot detect intent.",
                PlannerErrorCode.EMPTY_COMMAND,
            )

        sub_commands = self._split_into_sub_commands(normalised_tokens)
        self._enforce_single_intent(sub_commands)
        return sub_commands

    # ── Private ────────────────────────────────────────────────────────────────

    def _split_into_sub_commands(self, tokens: list[str]) -> list[SubCommand]:
        """Split the normalised stream into sub-commands at connector boundaries.

        The algorithm:
          1. A verb is required at the start.
          2. After each connector, re-use the same verb unless a new verb appears.
             (Sprint 003: single-intent, so a new different verb → MIXED_INTENTS later.)
          3. Collect all non-verb, non-connector tokens as targets for the current verb.
        """
        sub_commands: list[SubCommand] = []
        current_intent: str | None = None
        current_targets: list[str] = []
        needs_verb_or_target: bool = True  # True at the start and after each connector

        for token in tokens:
            if token == _CANONICAL_CONNECTOR:
                # Flush the current sub-command (if we have targets)
                if current_intent is not None and current_targets:
                    sub_commands.append(
                        SubCommand(intent=current_intent, targets=list(current_targets))
                    )
                    current_targets = []
                elif current_intent is not None and not current_targets:
                    # Connector with no targets preceding it — still valid (targets may follow)
                    pass
                needs_verb_or_target = True
                continue

            if token in _ALL_VERBS:
                # A verb found: flush previous sub-command if it had targets
                if current_intent is not None and current_targets:
                    sub_commands.append(
                        SubCommand(intent=current_intent, targets=list(current_targets))
                    )
                    current_targets = []
                current_intent = "open" if token in _OPEN_VERBS else "close"
                needs_verb_or_target = False
                continue

            if current_intent is None:
                # First non-connector token is not a verb
                raise PlanningError(
                    f"Command must begin with a recognised verb "
                    f"(e.g. 'open', 'close'). Got: '{token}'.",
                    PlannerErrorCode.UNKNOWN_INTENT,
                )

            # Regular target token
            current_targets.append(token)
            needs_verb_or_target = False

        # Flush the last sub-command
        if current_intent is not None and current_targets:
            sub_commands.append(
                SubCommand(intent=current_intent, targets=list(current_targets))
            )

        if not sub_commands:
            raise PlanningError(
                "No valid sub-commands were detected. "
                "Ensure your command contains a verb and at least one target.",
                PlannerErrorCode.UNKNOWN_INTENT,
            )

        return sub_commands

    @staticmethod
    def _enforce_single_intent(sub_commands: list[SubCommand]) -> None:
        """Reject commands that mix canonical intents (Sprint 003 constraint).

        Sprint 003: One canonical intent per command.
        Mixed-intent parsing is deferred to Sprint 004.
        """
        intents = {sc.intent for sc in sub_commands}
        if len(intents) > 1:
            raise PlanningError(
                f"This command mixes intents: {sorted(intents)}. "
                "Sprint 003 supports only one canonical intent per command. "
                "Please split into separate commands "
                "(e.g. 'Open Chrome' then 'Close VS Code').",
                PlannerErrorCode.MIXED_INTENTS,
            )
