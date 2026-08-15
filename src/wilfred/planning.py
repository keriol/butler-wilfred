from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from butler_core import (
    ButlerPlanner,
    DeterministicResolutionPipeline,
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    PlannerProvider,
    PlannerResult,
    ResolutionResult,
    ResolutionStatus,
    ResolverDefinition,
)

from wilfred.registry import ToolRegistry


@dataclass(frozen=True)
class PlannedExecutionResult:
    """Result of provider-neutral planning followed by safe execution."""

    planning: PlannerResult
    execution: ExecutionResult | None = None

    def to_dict(self) -> dict[str, object]:
        """Return the shared CLI and HTTP representation."""

        plan = self.planning.plan

        planning = {
            "status": self.planning.status.value,
            "duration_ms": self.planning.duration_ms,
            "plan": (
                None
                if plan is None
                else {
                    "tool_name": plan.tool_name,
                    "arguments": dict(plan.arguments),
                    "confidence": plan.confidence,
                    "reason": plan.reason,
                }
            ),
            "model": self.planning.model,
            "error_code": self.planning.error_code,
            "error_message": self.planning.error_message,
            "validation_errors": list(
                self.planning.validation_errors
            ),
        }

        return {
            "planning": planning,
            "execution": (
                None
                if self.execution is None
                else self.execution.to_dict()
            ),
        }


class PlannedExecution:
    """
    Bridge a Butler Core planner result into the Execution Engine.

    Planning never grants confirmation. ACTION and DANGEROUS tools
    remain governed by ExecutionPolicy.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        provider: PlannerProvider,
        system_prompt: str,
        model: str | None = None,
        enabled: bool = True,
        policy: ExecutionPolicy | None = None,
        resolvers: tuple[ResolverDefinition, ...] = (),
        before_fallback: Callable[[], None] | None = None,
    ) -> None:
        self._planner = ButlerPlanner(
            registry,
            provider=provider,
            system_prompt=system_prompt,
            model=model,
            enabled=enabled,
        )
        self._engine = ExecutionEngine(
            registry,
            policy=policy,
        )
        self._before_fallback = before_fallback
        self._resolution = DeterministicResolutionPipeline(
            resolvers,
            fallback=self._plan_fallback,
        )

    def execute(
        self,
        message: str,
        *,
        confirmed: bool = False,
    ) -> PlannedExecutionResult:
        resolution = self._resolution.resolve(message)

        if resolution.status is ResolutionStatus.ERROR:
            raise RuntimeError(
                "Goal resolution failed"
                + (
                    f" [{resolution.error_code}]"
                    if resolution.error_code
                    else ""
                )
                + (
                    f": {resolution.error_message}"
                    if resolution.error_message
                    else ""
                )
            )

        planning = resolution.value

        if not isinstance(planning, PlannerResult):
            raise RuntimeError(
                "Goal resolver must produce PlannerResult."
            )

        if not planning.ok:
            return PlannedExecutionResult(
                planning=planning,
            )

        plan = planning.plan

        if plan is None or plan.tool_name is None:
            return PlannedExecutionResult(
                planning=planning,
            )

        execution = self._engine.execute(
            ExecutionRequest(
                tool_name=plan.tool_name,
                arguments=plan.arguments,
                confirmed=confirmed,
            )
        )

        return PlannedExecutionResult(
            planning=planning,
            execution=execution,
        )

    def _plan_fallback(
        self,
        message: object,
    ) -> ResolutionResult:
        if not isinstance(message, str):
            raise TypeError(
                "Goal resolution requires a string message."
            )

        if self._before_fallback is not None:
            self._before_fallback()

        return ResolutionResult.handled_result(
            self._planner.plan(message)
        )


__all__ = [
    "PlannedExecution",
    "PlannedExecutionResult",
]
