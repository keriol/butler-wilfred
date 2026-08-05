from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wilfred.models import ToolDefinition


if TYPE_CHECKING:
    from wilfred.execution import ExecutionResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"Tool already registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def execute(
        self,
        name: str,
        **arguments: Any,
    ) -> "ExecutionResult":
        from wilfred.execution import (
            ExecutionEngine,
            ExecutionRequest,
        )

        return ExecutionEngine(self).execute(
            ExecutionRequest(
                tool_name=name,
                arguments=arguments,
            )
        )
