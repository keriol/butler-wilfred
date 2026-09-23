from __future__ import annotations

from butler_core import (
    ExecutionStatus,
    ToolPlan,
    ToolPlanSequence,
)

from wilfred import (
    SequenceExecutionStatus,
    SequentialExecution,
    ToolDefinition,
    ToolPermission,
    ToolRegistry,
)


def _registry(calls: list[str]) -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="read_first",
            description="Read first.",
            handler=lambda: calls.append("read_first") or {"value": 1},
            permission=ToolPermission.READ,
        )
    )
    registry.register(
        ToolDefinition(
            name="action_second",
            description="Action second.",
            handler=lambda: calls.append("action_second") or {"done": True},
            permission=ToolPermission.ACTION,
        )
    )
    registry.register(
        ToolDefinition(
            name="read_third",
            description="Read third.",
            handler=lambda: calls.append("read_third") or {"value": 3},
            permission=ToolPermission.READ,
        )
    )
    registry.register(
        ToolDefinition(
            name="explode",
            description="Raise an error.",
            handler=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
            permission=ToolPermission.READ,
        )
    )
    registry.register(
        ToolDefinition(
            name="dangerous_reset",
            description="Dangerous reset.",
            handler=lambda: calls.append("dangerous_reset") or {"reset": True},
            permission=ToolPermission.DANGEROUS,
        )
    )

    return registry


def test_read_only_sequence_executes_in_declared_order() -> None:
    calls: list[str] = []
    executor = SequentialExecution(_registry(calls))
    plan = ToolPlanSequence(
        steps=(
            ToolPlan(tool_name="read_first"),
            ToolPlan(tool_name="read_third"),
        )
    )

    result = executor.execute(plan)

    assert result.ok is True
    assert result.status is SequenceExecutionStatus.SUCCESS
    assert result.terminal_step_index is None
    assert calls == ["read_first", "read_third"]
    assert [
        execution.status
        for execution in result.executions
    ] == [
        ExecutionStatus.SUCCESS,
        ExecutionStatus.SUCCESS,
    ]


def test_sequence_stops_at_confirmation_required_step() -> None:
    calls: list[str] = []
    executor = SequentialExecution(_registry(calls))
    plan = ToolPlanSequence(
        steps=(
            ToolPlan(tool_name="read_first"),
            ToolPlan(tool_name="action_second"),
            ToolPlan(tool_name="read_third"),
        )
    )

    result = executor.execute(plan)

    assert result.ok is False
    assert result.status is SequenceExecutionStatus.STOPPED
    assert result.terminal_step_index == 1
    assert calls == ["read_first"]
    assert result.executions[-1].status is ExecutionStatus.CONFIRMATION_REQUIRED


def test_trusted_authorization_applies_only_to_its_step() -> None:
    calls: list[str] = []
    executor = SequentialExecution(_registry(calls))
    plan = ToolPlanSequence(
        steps=(
            ToolPlan(
                tool_name="action_second",
                user_authorized=True,
            ),
            ToolPlan(tool_name="read_third"),
        )
    )

    result = executor.execute(plan)

    assert result.ok is True
    assert calls == ["action_second", "read_third"]


def test_sequence_stops_after_execution_error() -> None:
    calls: list[str] = []
    executor = SequentialExecution(_registry(calls))
    plan = ToolPlanSequence(
        steps=(
            ToolPlan(tool_name="read_first"),
            ToolPlan(tool_name="explode"),
            ToolPlan(tool_name="read_third"),
        )
    )

    result = executor.execute(plan)

    assert result.ok is False
    assert result.terminal_step_index == 1
    assert calls == ["read_first"]
    assert result.executions[-1].status is ExecutionStatus.ERROR


def test_dangerous_step_remains_denied_even_when_user_authorized() -> None:
    calls: list[str] = []
    executor = SequentialExecution(_registry(calls))
    plan = ToolPlanSequence(
        steps=(
            ToolPlan(
                tool_name="dangerous_reset",
                user_authorized=True,
            ),
            ToolPlan(tool_name="read_third"),
        )
    )

    result = executor.execute(plan)

    assert result.ok is False
    assert result.terminal_step_index == 0
    assert calls == []
    assert result.executions[0].status is ExecutionStatus.DENIED


def test_sequence_result_serialization_is_deterministic() -> None:
    calls: list[str] = []
    executor = SequentialExecution(_registry(calls))
    plan = ToolPlanSequence(
        steps=(ToolPlan(tool_name="read_first"),),
        confidence=1.0,
        reason="Read once.",
    )

    payload = executor.execute(plan).to_dict()

    assert payload["status"] == "success"
    assert payload["ok"] is True
    assert payload["terminal_step_index"] is None
    assert payload["plan"]["reason"] == "Read once."
    assert payload["executions"][0]["tool_name"] == "read_first"


def test_runtime_exposes_programmatic_sequence_execution() -> None:
    calls: list[str] = []

    from wilfred import PluginDefinition, WilfredRuntime

    plugin = PluginDefinition(
        name="test.sequence",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="sequence_read",
                description="Read through runtime.",
                handler=lambda: calls.append("sequence_read") or {"ok": True},
                permission=ToolPermission.READ,
            )
        ),
    )
    runtime = WilfredRuntime(
        provider=lambda *args: "{}",
        system_prompt="Test.",
        plugins=(plugin,),
    )
    plan = ToolPlanSequence(
        steps=(ToolPlan(tool_name="sequence_read"),)
    )

    result = runtime.execute_sequence(plan)

    assert result.ok is True
    assert calls == ["sequence_read"]
