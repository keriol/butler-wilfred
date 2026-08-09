from __future__ import annotations

import json

from butler_core import (
    ExecutionStatus,
    PlannerStatus,
)
from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.registry import ToolRegistry


def _provider_for(
    tool_name: str | None,
    arguments: dict | None = None,
):
    def provider(message, system_prompt, tools):
        return json.dumps(
            {
                "tool_name": tool_name,
                "arguments": arguments or {},
                "confidence": 1.0,
                "reason": "deterministic test plan",
            }
        )

    return provider


def _registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="read_state",
            description="Read current state.",
            handler=lambda: {"state": "on"},
            permission=ToolPermission.READ,
        )
    )

    registry.register(
        ToolDefinition(
            name="set_state",
            description="Change state.",
            handler=lambda state: {"state": state},
            parameters={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                    },
                },
                "required": ["state"],
                "additionalProperties": False,
            },
            permission=ToolPermission.ACTION,
        )
    )

    registry.register(
        ToolDefinition(
            name="dangerous_reset",
            description="Dangerous reset.",
            handler=lambda: {"reset": True},
            permission=ToolPermission.DANGEROUS,
        )
    )

    return registry


def test_read_plan_executes_without_confirmation():
    from wilfred.planning import PlannedExecution

    runtime = PlannedExecution(
        _registry(),
        provider=_provider_for("read_state"),
        system_prompt="Public Wilfred test planner.",
    )

    result = runtime.execute("read the state")

    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS


def test_action_plan_does_not_self_confirm():
    from wilfred.planning import PlannedExecution

    runtime = PlannedExecution(
        _registry(),
        provider=_provider_for(
            "set_state",
            {"state": "off"},
        ),
        system_prompt="Public Wilfred test planner.",
    )

    result = runtime.execute("turn it off")

    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.execution is not None
    assert (
        result.execution.status
        is ExecutionStatus.CONFIRMATION_REQUIRED
    )


def test_explicit_confirmation_can_execute_action():
    from wilfred.planning import PlannedExecution

    runtime = PlannedExecution(
        _registry(),
        provider=_provider_for(
            "set_state",
            {"state": "off"},
        ),
        system_prompt="Public Wilfred test planner.",
    )

    result = runtime.execute(
        "turn it off",
        confirmed=True,
    )

    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS


def test_dangerous_plan_remains_denied_by_default():
    from wilfred.planning import PlannedExecution

    runtime = PlannedExecution(
        _registry(),
        provider=_provider_for("dangerous_reset"),
        system_prompt="Public Wilfred test planner.",
    )

    result = runtime.execute(
        "reset everything",
        confirmed=True,
    )

    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.DENIED


def test_no_tool_plan_does_not_execute():
    from wilfred.planning import PlannedExecution

    runtime = PlannedExecution(
        _registry(),
        provider=_provider_for(None),
        system_prompt="Public Wilfred test planner.",
    )

    result = runtime.execute("just chatting")

    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.planning.plan is not None
    assert result.planning.plan.tool_name is None
    assert result.execution is None


def test_planner_failure_does_not_execute():
    from wilfred.planning import PlannedExecution

    runtime = PlannedExecution(
        _registry(),
        provider=lambda message, prompt, tools: "not-json",
        system_prompt="Public Wilfred test planner.",
    )

    result = runtime.execute("anything")

    assert result.planning.status is PlannerStatus.INVALID_RESPONSE
    assert result.execution is None


def test_planned_execution_is_public_api():
    from wilfred import (
        PlannedExecution as PublicPlannedExecution,
        PlannedExecutionResult as PublicPlannedExecutionResult,
    )
    from wilfred.planning import (
        PlannedExecution,
        PlannedExecutionResult,
    )

    assert PublicPlannedExecution is PlannedExecution
    assert PublicPlannedExecutionResult is PlannedExecutionResult
