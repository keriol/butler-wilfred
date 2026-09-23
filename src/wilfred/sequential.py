from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from butler_core import (
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ToolPlanSequence,
)

from wilfred.registry import ToolRegistry


class SequenceExecutionStatus(str, Enum):
    SUCCESS = "success"
    STOPPED = "stopped"


@dataclass(frozen=True)
class SequenceExecutionResult:
    plan: ToolPlanSequence
    executions: tuple[ExecutionResult, ...]
    status: SequenceExecutionStatus
    terminal_step_index: int | None = None

    @property
    def ok(self) -> bool:
        return self.status is SequenceExecutionStatus.SUCCESS

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "ok": self.ok,
            "terminal_step_index": self.terminal_step_index,
            "plan": self.plan.to_dict(),
            "executions": [
                execution.to_dict()
                for execution in self.executions
            ],
        }


class SequentialExecution:
    """Execute an already-resolved tool sequence through normal policy."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        policy: ExecutionPolicy | None = None,
    ) -> None:
        self._engine = ExecutionEngine(
            registry,
            policy=policy,
        )

    def execute(
        self,
        plan: ToolPlanSequence,
    ) -> SequenceExecutionResult:
        executions: list[ExecutionResult] = []

        for index, step in enumerate(plan.steps):
            result = self._engine.execute(
                ExecutionRequest(
                    tool_name=step.tool_name,
                    arguments=step.arguments,
                    confirmed=step.user_authorized,
                )
            )
            executions.append(result)

            if not result.ok:
                return SequenceExecutionResult(
                    plan=plan,
                    executions=tuple(executions),
                    status=SequenceExecutionStatus.STOPPED,
                    terminal_step_index=index,
                )

        return SequenceExecutionResult(
            plan=plan,
            executions=tuple(executions),
            status=SequenceExecutionStatus.SUCCESS,
        )


__all__ = [
    "SequenceExecutionResult",
    "SequenceExecutionStatus",
    "SequentialExecution",
]
