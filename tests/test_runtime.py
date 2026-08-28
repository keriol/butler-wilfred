from __future__ import annotations

import json

from butler_core import ExecutionStatus, PlannerStatus

from wilfred import CapabilityDefinition, DomainDefinition
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.plugins import PluginDefinition


def _provider(tool_name, arguments=None):
    def provider(message, system_prompt, tools):
        return json.dumps(
            {
                "tool_name": tool_name,
                "arguments": arguments or {},
                "confidence": 1.0,
                "reason": "deterministic runtime test",
            }
        )

    return provider


def test_runtime_registers_native_tools():
    from wilfred.runtime import WilfredRuntime

    runtime = WilfredRuntime(
        provider=_provider(None),
        system_prompt="Test Wilfred runtime.",
    )

    assert runtime.tool_names() == [
        "wilfred_status",
        "wilfred_tools",
    ]

    description = runtime.describe_runtime()

    assert description["name"] == "Wilfred"
    assert description["status"] == "ok"
    assert description["runtime"] == "goal-runtime"
    assert description["tool_count"] == 2
    assert description["domain_count"] == 0
    assert description["capability_count"] == 0

    tools = runtime.describe_tools()

    assert [tool["name"] for tool in tools] == [
        "wilfred_status",
        "wilfred_tools",
    ]
    assert all("handler" not in tool for tool in tools)
    assert all("parameters" in tool for tool in tools)


def test_runtime_loads_public_plugins():
    from wilfred.runtime import WilfredRuntime

    plugin = PluginDefinition(
        name="test.read",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_read",
                description="Return a test value.",
                handler=lambda: {"value": 42},
                permission=ToolPermission.READ,
            )
        ),
    )

    runtime = WilfredRuntime(
        provider=_provider("test_read"),
        system_prompt="Test Wilfred runtime.",
        plugins=[plugin],
    )

    assert runtime.tool_names() == [
        "test_read",
        "wilfred_status",
        "wilfred_tools",
    ]

    result = runtime.execute_goal("read test value")

    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
    assert result.execution.value == {"value": 42}


def test_runtime_exposes_loaded_domains_and_capabilities():
    from wilfred.runtime import WilfredRuntime

    plugin = PluginDefinition(
        name="test.media",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_playback",
                description="Play a test item.",
                handler=lambda: {"playing": True},
            )
        ),
        domains=(
            DomainDefinition(
                name="media",
                description="Media knowledge and behavior.",
            ),
        ),
        capabilities=(
            CapabilityDefinition(
                name="playback",
                domain="media",
                description="Play resolved media.",
            ),
        ),
    )

    runtime = WilfredRuntime(
        provider=_provider("test_playback"),
        system_prompt="Test Wilfred runtime.",
        plugins=[plugin],
    )

    assert runtime.domain_names() == ["media"]
    assert runtime.capability_names() == ["media.playback"]
    assert runtime.describe_domains() == [
        {
            "name": "media",
            "description": "Media knowledge and behavior.",
            "owner_plugin": "test.media",
        }
    ]
    assert runtime.describe_capabilities() == [
        {
            "name": "media.playback",
            "domain": "media",
            "description": "Play resolved media.",
            "owner_plugin": "test.media",
        }
    ]

    description = runtime.describe_runtime()
    assert description["domain_count"] == 1
    assert description["capability_count"] == 1


def test_runtime_executes_native_goal():
    from wilfred.runtime import WilfredRuntime

    runtime = WilfredRuntime(
        provider=_provider("wilfred_status"),
        system_prompt="Test Wilfred runtime.",
    )

    result = runtime.execute_goal("what is your status?")

    assert result.planning.status is PlannerStatus.SUCCESS
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
    assert result.execution.value["name"] == "Wilfred"


def test_runtime_does_not_self_confirm_actions():
    from wilfred.runtime import WilfredRuntime

    plugin = PluginDefinition(
        name="test.action",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_action",
                description="Perform a test action.",
                handler=lambda: {"done": True},
                permission=ToolPermission.ACTION,
            )
        ),
    )

    runtime = WilfredRuntime(
        provider=_provider("test_action"),
        system_prompt="Test Wilfred runtime.",
        plugins=[plugin],
    )

    result = runtime.execute_goal("do the action")

    assert result.execution is not None
    assert (
        result.execution.status
        is ExecutionStatus.CONFIRMATION_REQUIRED
    )


def test_runtime_accepts_explicit_confirmation():
    from wilfred.runtime import WilfredRuntime

    plugin = PluginDefinition(
        name="test.action",
        register=lambda registry: registry.register(
            ToolDefinition(
                name="test_action",
                description="Perform a test action.",
                handler=lambda: {"done": True},
                permission=ToolPermission.ACTION,
            )
        ),
    )

    runtime = WilfredRuntime(
        provider=_provider("test_action"),
        system_prompt="Test Wilfred runtime.",
        plugins=[plugin],
    )

    result = runtime.execute_goal(
        "do the action",
        confirmed=True,
    )

    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
    assert result.execution.value == {"done": True}


def test_runtime_is_public_api():
    from wilfred import WilfredRuntime as PublicWilfredRuntime
    from wilfred.runtime import WilfredRuntime

    assert PublicWilfredRuntime is WilfredRuntime
