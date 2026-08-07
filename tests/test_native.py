from wilfred.execution import (
    ExecutionEngine,
    ExecutionRequest,
    ExecutionStatus,
)
from wilfred.models import ToolPermission
from wilfred.native import register_native_tools
from wilfred.registry import ToolRegistry


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_native_tools(registry)
    return registry


def test_native_tools_are_registered_as_read_capabilities() -> None:
    registry = build_registry()

    assert registry.names() == [
        "wilfred_status",
        "wilfred_tools",
    ]

    for name in registry.names():
        tool = registry.get(name)

        assert tool is not None
        assert tool.permission is ToolPermission.READ
        assert tool.category == "native"


def test_wilfred_status_runs_through_execution_engine() -> None:
    registry = build_registry()
    engine = ExecutionEngine(registry)

    result = engine.execute(
        ExecutionRequest(
            tool_name="wilfred_status",
        )
    )

    assert result.status is ExecutionStatus.SUCCESS
    assert result.ok is True
    assert result.value["name"] == "Wilfred"
    assert result.value["status"] == "ok"
    assert result.value["version"]
    assert result.value["runtime"] == "standalone"


def test_wilfred_tools_introspects_registry() -> None:
    registry = build_registry()
    engine = ExecutionEngine(registry)

    result = engine.execute(
        ExecutionRequest(
            tool_name="wilfred_tools",
        )
    )

    assert result.status is ExecutionStatus.SUCCESS

    tools = result.value["tools"]

    assert [tool["name"] for tool in tools] == [
        "wilfred_status",
        "wilfred_tools",
    ]

    assert all(
        tool["permission"] == "READ"
        for tool in tools
    )

    assert all(
        tool["category"] == "native"
        for tool in tools
    )
