from __future__ import annotations

import json

import pytest

from butler_core import (
    ExecutionStatus,
    PlannerResult,
    PlannerStatus,
    ResolutionResult,
    ResolverDefinition,
    ToolPlan,
)
from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.planning import PlannedExecution
from wilfred.registry import ToolRegistry


def _registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="read_state",
            description="Read state.",
            handler=lambda: {"state": "on"},
            permission=ToolPermission.READ,
        )
    )

    return registry


def _plan(tool_name: str | None) -> PlannerResult:
    return PlannerResult(
        status=PlannerStatus.SUCCESS,
        duration_ms=0.0,
        plan=ToolPlan(
            tool_name=tool_name,
            arguments={},
            confidence=1.0,
            reason="deterministic resolver",
        ),
    )


def test_deterministic_hit_skips_planner_provider():
    provider_calls = []

    def provider(message, prompt, tools):
        provider_calls.append(message)
        raise AssertionError(
            "planner provider must not be called"
        )

    def resolver(message):
        assert message == "read locally"
        return ResolutionResult.handled_result(
            _plan("read_state")
        )

    runtime = PlannedExecution(
        _registry(),
        provider=provider,
        system_prompt="Test.",
        resolvers=(
            ResolverDefinition(
                "local",
                resolver,
            ),
        ),
    )

    result = runtime.execute("read locally")

    assert provider_calls == []
    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
    assert result.execution.value == {"state": "on"}


def test_not_handled_falls_back_to_planner():
    provider_calls = []

    def provider(message, prompt, tools):
        provider_calls.append(message)

        return json.dumps(
            {
                "tool_name": "read_state",
                "arguments": {},
                "confidence": 1.0,
                "reason": "planner fallback",
            }
        )

    def resolver(message):
        return ResolutionResult.not_handled_result()

    runtime = PlannedExecution(
        _registry(),
        provider=provider,
        system_prompt="Test.",
        resolvers=(
            ResolverDefinition(
                "local",
                resolver,
            ),
        ),
    )

    result = runtime.execute("use planner")

    assert provider_calls == ["use planner"]
    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS


def test_resolver_error_stops_before_planner():
    provider_calls = []

    def provider(message, prompt, tools):
        provider_calls.append(message)
        return "{}"

    def resolver(message):
        raise ValueError("resolver exploded")

    runtime = PlannedExecution(
        _registry(),
        provider=provider,
        system_prompt="Test.",
        resolvers=(
            ResolverDefinition(
                "broken",
                resolver,
            ),
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="resolver_exception",
    ):
        runtime.execute("boom")

    assert provider_calls == []
