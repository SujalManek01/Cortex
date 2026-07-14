"""RulePlanner — deterministic Natural Language Planner for Sprint 003.

Implements BasePlanner using the four-stage pipeline:
  Tokenizer → Normalizer → IntentDetector → TargetResolver → ActionPlan

Engineering Rules:
  - Implements BasePlanner — the only planner contract accepted downstream.
  - Returns PlannerResult, not ActionPlan directly.
  - Never executes actions; never accesses the OS.
  - Never bypasses the Validator or Safety Policy.
  - Sets plan.created_by = "rule_planner".
  - Sets plan.goal = normalised command text.
  - Detects and warns on duplicate targets (does not fail).
  - Emits a structured log entry after each pipeline stage.

Performance target: entire pipeline < 20 ms for commands with ≤ 10 actions.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from backend.logging.logger import StructuredLogger
from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.planner_result import PlannerResult
from backend.planner.base_planner import BasePlanner
from backend.planner.intent_detector import IntentDetector
from backend.planner.normalizer import Normalizer
from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.planner.target_resolver import TargetResolver
from backend.planner.tokenizer import Tokenizer
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry

_PLANNER_NAME = "rule_planner"


class RulePlanner(BasePlanner):
    """Deterministic rule-based planner that converts natural language into ActionPlans.

    Args:
        app_registry:     ApplicationRegistry (injected from app.state).
        folder_registry:  FolderRegistry (injected from app.state).
        website_registry: WebsiteRegistry (injected from app.state).
        config_dir:       Path to the directory containing planner_aliases.json.
        logger:           StructuredLogger for pipeline observability.
    """

    def __init__(
        self,
        app_registry: ApplicationRegistry,
        folder_registry: FolderRegistry,
        website_registry: WebsiteRegistry,
        config_dir: Path,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._tokenizer      = Tokenizer()
        self._normalizer     = Normalizer(config_dir=config_dir)
        self._intent_detector = IntentDetector()
        self._target_resolver = TargetResolver(
            app_registry=app_registry,
            folder_registry=folder_registry,
            website_registry=website_registry,
        )
        self._logger = logger

    # ── BasePlanner contract ───────────────────────────────────────────────────

    async def plan(self, command: str) -> PlannerResult:
        """Convert a natural language command into a PlannerResult.

        Stages (in order):
          1. Tokenizer
          2. Normalizer
          3. IntentDetector
          4. TargetResolver
          5. ActionPlan construction

        Args:
            command: Plain-text command from the user.
                     Example: "Open Chrome and GitHub"

        Returns:
            PlannerResult with success=True if all stages succeed, or
            success=False with error_code and error_message if any stage fails.
        """
        start_ms = time.perf_counter() * 1000

        try:
            return await self._run_pipeline(command, start_ms)
        except PlanningError as exc:
            elapsed = time.perf_counter() * 1000 - start_ms
            self._log("pipeline_failed", {
                "command": command,
                "error_code": exc.error_code,
                "error_message": str(exc),
                "planning_time_ms": round(elapsed, 2),
            })
            return PlannerResult(
                success=False,
                plan=None,
                normalized_input="",
                confidence=0.0,
                warnings=[],
                planning_time_ms=round(elapsed, 2),
                token_count=0,
                step_count=0,
                planner_name=_PLANNER_NAME,
                error_code=exc.error_code,
                error_message=str(exc),
            )

    # ── Private pipeline ───────────────────────────────────────────────────────

    async def _run_pipeline(self, command: str, start_ms: float) -> PlannerResult:
        """Execute all planning stages. Raises PlanningError on any failure."""

        # ── Stage 1: Tokenizer ─────────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        tokens = self._tokenizer.tokenize(command)
        self._log("stage_tokenizer", {
            "token_count": len(tokens),
            "duration_ms": round(time.perf_counter() * 1000 - stage_start, 2),
        })

        # ── Stage 2: Normalizer ────────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        normalised = self._normalizer.normalize(tokens)
        normalised_str = " ".join(normalised)
        self._log("stage_normalizer", {
            "normalised_input": normalised_str,
            "duration_ms": round(time.perf_counter() * 1000 - stage_start, 2),
        })

        # ── Stage 3: IntentDetector ────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        sub_commands = self._intent_detector.detect(normalised)
        self._log("stage_intent_detector", {
            "sub_command_count": len(sub_commands),
            "intents": [sc.intent for sc in sub_commands],
            "duration_ms": round(time.perf_counter() * 1000 - stage_start, 2),
        })

        # ── Stage 4: TargetResolver ────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        all_resolved = []
        for sc in sub_commands:
            resolved = self._target_resolver.resolve_all(sc.intent, sc.targets)
            all_resolved.extend(resolved)
        self._log("stage_target_resolver", {
            "resolved_count": len(all_resolved),
            "resolved": [(r.alias, r.capability) for r in all_resolved],
            "duration_ms": round(time.perf_counter() * 1000 - stage_start, 2),
        })

        # ── Stage 5: Build ActionPlan ──────────────────────────────────────────
        warnings: list[str] = []
        seen_targets: set[str] = set()
        steps: list[ActionStep] = []

        for i, resolved in enumerate(all_resolved):
            # Warn on duplicates — do not fail.
            target_key = f"{resolved.capability}:{resolved.alias}"
            if target_key in seen_targets:
                warnings.append(f"Duplicate target detected: '{resolved.alias}' ({resolved.capability}).")
            seen_targets.add(target_key)

            # Build ActionStep with correct parameter key per capability.
            parameters = self._build_parameters(resolved.capability, resolved.alias)
            steps.append(ActionStep(
                id=f"step-{i + 1}",
                action=resolved.capability,
                parameters=parameters,
            ))

        plan = ActionPlan(
            plan_id=uuid.uuid4(),
            goal=normalised_str,
            version="1.0",
            created_by=_PLANNER_NAME,
            steps=steps,
        )

        elapsed = time.perf_counter() * 1000 - start_ms
        self._log("pipeline_complete", {
            "step_count": len(steps),
            "warning_count": len(warnings),
            "planning_time_ms": round(elapsed, 2),
        })

        return PlannerResult(
            success=True,
            plan=plan,
            normalized_input=normalised_str,
            confidence=1.0,
            warnings=warnings,
            planning_time_ms=round(elapsed, 2),
            token_count=len(tokens),
            step_count=len(steps),
            planner_name=_PLANNER_NAME,
            error_code=None,
            error_message=None,
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_parameters(capability: str, alias: str) -> dict:
        """Build the parameters dict for an ActionStep.

        Each executor expects a specific parameter key:
          application.open / application.close  → {"app": alias}
          folder.open                            → {"alias": alias}
          website.open                           → {"alias": alias}
        """
        if capability in ("application.open", "application.close"):
            return {"app": alias}
        # folder.open and website.open both use "alias"
        return {"alias": alias}

    def _log(self, event: str, data: dict) -> None:
        """Emit a structured log entry if a logger is available."""
        if self._logger is not None:
            self._logger.info(
                f"rule_planner.{event}",
                planner=_PLANNER_NAME,
                **data,
            )
