from __future__ import annotations

import time
import uuid
from pathlib import Path

from backend.logging.logger import StructuredLogger
from backend.models.action_plan import ActionPlan, ActionStep
from backend.models.planner_result import PlannerResult, PlannerDiagnostics
from backend.planner.base_planner import BasePlanner
from backend.planner.normalizer import Normalizer
from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.planner.target_resolver import TargetResolver
from backend.planner.tokenizer import Tokenizer
from backend.planner.grammar_parser import GrammarParser
from backend.planner.intent_grouper import IntentGrouper
from backend.planner.scope_resolver import ScopeResolver
from backend.planner.conflict_analyzer import ConflictAnalyzer
from backend.registry.application_registry import ApplicationRegistry
from backend.registry.folder_registry import FolderRegistry
from backend.registry.website_registry import WebsiteRegistry
from backend.config.config_loader import ReadOnlyConfig

_PLANNER_NAME = "rule_planner"


class RulePlanner(BasePlanner):
    """Deterministic rule-based planner that converts natural language into ActionPlans.

    Args:
        app_registry:     ApplicationRegistry (injected from app.state).
        folder_registry:  FolderRegistry (injected from app.state).
        website_registry: WebsiteRegistry (injected from app.state).
        config_dir:       Path to the directory containing planner configs.
        logger:           StructuredLogger for pipeline observability.
        config:           Pre-loaded ReadOnlyConfig containing grammar/rules.
    """

    def __init__(
        self,
        app_registry: ApplicationRegistry,
        folder_registry: FolderRegistry,
        website_registry: WebsiteRegistry,
        config_dir: Path | None = None,
        logger: StructuredLogger | None = None,
        config: ReadOnlyConfig | None = None,
    ) -> None:
        from backend.config.config_loader import ConfigLoader
        # 1. Resolve configuration
        if config is None and config_dir is not None:
            config_loader = ConfigLoader(config_dir=config_dir)
            config = config_loader.load()

        grammar_cfg = config.grammar if config is not None else None
        aliases_cfg = config.planner_aliases if config is not None else None
        rules_cfg = config.planner_rules if config is not None else None

        self._tokenizer = Tokenizer(grammar_config=grammar_cfg)
        self._normalizer = Normalizer(planner_aliases=aliases_cfg, config_dir=config_dir)
        self._grammar_parser = GrammarParser(grammar_config=grammar_cfg)
        self._intent_grouper = IntentGrouper()
        self._scope_resolver = ScopeResolver()
        self._conflict_analyzer = ConflictAnalyzer(rules_config=rules_cfg)
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
          3. Grammar Parser
          4. Intent Grouper
          5. Verb Scope Resolver
          6. Target Resolver
          7. Conflict Analyzer
          8. ActionPlan construction

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
        tokenizer_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_tokenizer", {
            "token_count": len(tokens),
            "duration_ms": round(tokenizer_ms, 2),
        })

        # ── Stage 2: Normalizer ────────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        normalised = self._normalizer.normalize(tokens)
        normalised_str = " ".join(normalised)
        normalizer_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_normalizer", {
            "normalised_input": normalised_str,
            "duration_ms": round(normalizer_ms, 2),
        })

        # ── Stage 3: Grammar Parser ────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        grammar_tree = self._grammar_parser.parse(normalised, command)
        grammar_parser_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_grammar_parser", {
            "clause_count": len(grammar_tree.clauses),
            "duration_ms": round(grammar_parser_ms, 2),
        })

        # ── Stage 4: Intent Grouper ────────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        intent_groups = self._intent_grouper.group(grammar_tree)
        intent_grouper_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_intent_grouper", {
            "intent_group_count": len(intent_groups),
            "duration_ms": round(intent_grouper_ms, 2),
        })

        # ── Stage 5: Verb Scope Resolver ───────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        expanded_groups = self._scope_resolver.resolve_scope(intent_groups)
        scope_resolver_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_scope_resolver", {
            "expanded_count": len(expanded_groups),
            "duration_ms": round(scope_resolver_ms, 2),
        })

        # ── Stage 6: Target Resolver ───────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        resolved_actions = []
        for eg in expanded_groups:
            resolved = self._target_resolver.resolve(eg.verb, eg.targets[0])
            resolved_actions.append(resolved)
        target_resolver_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_target_resolver", {
            "resolved_count": len(resolved_actions),
            "duration_ms": round(target_resolver_ms, 2),
        })

        # ── Stage 7: Conflict Analyzer ─────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        warnings, infos = self._conflict_analyzer.analyze(resolved_actions)
        conflict_analyzer_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_conflict_analyzer", {
            "warning_count": len(warnings),
            "info_count": len(infos),
            "duration_ms": round(conflict_analyzer_ms, 2),
        })

        # ── Stage 8: Build ActionPlan ──────────────────────────────────────────
        stage_start = time.perf_counter() * 1000
        steps: list[ActionStep] = []
        for i, action in enumerate(resolved_actions):
            parameters = self._build_parameters(action.capability, action.target)
            steps.append(ActionStep(
                id=f"step-{i + 1}",
                action=action.capability,
                parameters=parameters,
            ))

        plan = ActionPlan(
            plan_id=uuid.uuid4(),
            goal=normalised_str,
            version="1.0",
            created_by=_PLANNER_NAME,
            steps=steps,
        )
        rule_planner_ms = time.perf_counter() * 1000 - stage_start
        self._log("stage_rule_planner", {
            "step_count": len(steps),
            "duration_ms": round(rule_planner_ms, 2),
        })

        # ── Calculate total and compile diagnostics ────────────────────────────
        total_ms = time.perf_counter() * 1000 - start_ms

        self._log("timing_breakdown", {
            "Tokenizer": f"{tokenizer_ms:.2f} ms",
            "Normalizer": f"{normalizer_ms:.2f} ms",
            "Grammar Parser": f"{grammar_parser_ms:.2f} ms",
            "Intent Grouper": f"{intent_grouper_ms:.2f} ms",
            "Scope Resolver": f"{scope_resolver_ms:.2f} ms",
            "Target Resolver": f"{target_resolver_ms:.2f} ms",
            "Conflict Analyzer": f"{conflict_analyzer_ms:.2f} ms",
            "Rule Planner": f"{rule_planner_ms:.2f} ms",
            "Total": f"{total_ms:.2f} ms",
        })

        diagnostics = PlannerDiagnostics(
            planning_time_ms=round(total_ms, 2),
            token_count=len(tokens),
            clause_count=len(grammar_tree.clauses),
            intent_group_count=len(intent_groups),
            resolved_target_count=len(resolved_actions),
            warning_count=len(warnings),
        )

        return PlannerResult(
            success=True,
            plan=plan,
            normalized_input=normalised_str,
            confidence=1.0,
            warnings=warnings,
            information=infos,
            diagnostics=diagnostics,
            planning_time_ms=round(total_ms, 2),
            token_count=len(tokens),
            step_count=len(steps),
            planner_name=_PLANNER_NAME,
            error_code=None,
            error_message=None,
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_parameters(capability: str, target: str) -> dict:
        """Build the parameters dict for an ActionStep.

        Each executor expects a specific parameter key:
          application.open / application.close  → {"app": target}
          folder.open                            → {"alias": target}
          website.open                           → {"alias": target}
        """
        if capability in ("application.open", "application.close"):
            return {"app": target}
        # folder.open and website.open both use "alias"
        return {"alias": target}

    def _log(self, event: str, data: dict) -> None:
        """Emit a structured log entry if a logger is available."""
        if self._logger is not None:
            self._logger.info(
                f"rule_planner.{event}",
                planner=_PLANNER_NAME,
                **data,
            )

