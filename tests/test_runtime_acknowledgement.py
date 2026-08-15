from __future__ import annotations

import json

from butler_core import ExecutionStatus

from wilfred import (
    OutputCapability,
    OutputDeliveryResult,
    OutputDeliveryStatus,
    OutputKind,
    OutputRequest,
    WilfredRuntime,
)
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.plugins import PluginDefinition


class RecordingSpeechAdapter:
    def __init__(
        self,
        events: list[str],
        *,
        status: OutputDeliveryStatus = OutputDeliveryStatus.DELIVERED,
    ) -> None:
        self.events = events
        self.status = status
        self.requests: list[OutputRequest] = []

    @property
    def name(self) -> str:
        return "recording-speech"

    def capabilities(self) -> frozenset[OutputCapability]:
        return frozenset({OutputCapability.SPEECH})

    def deliver(
        self,
        request: OutputRequest,
    ) -> OutputDeliveryResult:
        self.events.append("ack")
        self.requests.append(request)

        return OutputDeliveryResult(
            status=self.status,
        )


def _provider(events: list[str], tool_name=None):
    def provider(message, system_prompt, tools):
        events.append("provider")

        return json.dumps(
            {
                "tool_name": tool_name,
                "arguments": {},
                "confidence": 1.0,
                "reason": "deterministic test",
            }
        )

    return provider


def test_acknowledgement_happens_before_provider_call():
    events: list[str] = []
    adapter = RecordingSpeechAdapter(events)

    runtime = WilfredRuntime(
        provider=_provider(events),
        system_prompt="Test runtime.",
        acknowledgement_adapter=adapter,
        acknowledgement_text="Thinking about it.",
    )

    runtime.execute_goal("hello")

    assert events == ["ack", "provider"]

    request = adapter.requests[0]

    assert request.kind is OutputKind.SPEECH
    assert request.content == "Thinking about it."


def test_runtime_without_acknowledgement_is_unchanged():
    events: list[str] = []

    runtime = WilfredRuntime(
        provider=_provider(events),
        system_prompt="Test runtime.",
    )

    runtime.execute_goal("hello")

    assert events == ["provider"]


def test_failed_acknowledgement_does_not_block_planning():
    events: list[str] = []

    runtime = WilfredRuntime(
        provider=_provider(events),
        system_prompt="Test runtime.",
        acknowledgement_adapter=RecordingSpeechAdapter(
            events,
            status=OutputDeliveryStatus.FAILED,
        ),
        acknowledgement_text="Thinking about it.",
    )

    result = runtime.execute_goal("hello")

    assert events == ["ack", "provider"]
    assert result.planning.ok


def test_acknowledgement_never_grants_action_confirmation():
    events: list[str] = []

    plugin = PluginDefinition(
        name="test.action",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_action",
                description="Perform test action.",
                handler=lambda: {"done": True},
                permission=ToolPermission.ACTION,
            )
        ),
    )

    runtime = WilfredRuntime(
        provider=_provider(events, "test_action"),
        system_prompt="Test runtime.",
        plugins=[plugin],
        acknowledgement_adapter=RecordingSpeechAdapter(events),
        acknowledgement_text="Thinking about it.",
    )

    result = runtime.execute_goal("do it")

    assert events == ["ack", "provider"]
    assert result.execution is not None
    assert (
        result.execution.status
        is ExecutionStatus.CONFIRMATION_REQUIRED
    )


def test_deterministic_resolution_skips_provider_acknowledgement():
    from butler_core import (
        PlannerResult,
        PlannerStatus,
        ResolutionResult,
        ResolverDefinition,
        ToolPlan,
    )

    events: list[str] = []
    adapter = RecordingSpeechAdapter(events)

    def provider(message, system_prompt, tools):
        events.append("provider")
        raise AssertionError(
            "provider must not run for deterministic resolution"
        )

    def resolver(message):
        return ResolutionResult.handled_result(
            PlannerResult(
                status=PlannerStatus.SUCCESS,
                duration_ms=0.0,
                plan=ToolPlan(
                    tool_name="wilfred_status",
                    arguments={},
                    confidence=1.0,
                    reason="deterministic native resolution",
                ),
            )
        )

    runtime = WilfredRuntime(
        provider=provider,
        system_prompt="Test runtime.",
        resolvers=(
            ResolverDefinition(
                "native-status",
                resolver,
            ),
        ),
        acknowledgement_adapter=adapter,
        acknowledgement_text="Thinking about it.",
    )

    result = runtime.execute_goal(
        "what is your status?"
    )

    assert events == []
    assert result.execution is not None
    assert (
        result.execution.status
        is ExecutionStatus.SUCCESS
    )
