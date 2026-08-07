from __future__ import annotations

from typing import Any

from wilfred import __version__
from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.registry import ToolRegistry


def _runtime_status() -> dict[str, str]:
    return {
        "name": "Wilfred",
        "status": "ok",
        "version": __version__,
        "runtime": "standalone",
    }


def _describe_tool(
    tool: ToolDefinition,
) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description,
        "category": tool.category,
        "permission": tool.permission.value,
    }


def register_native_tools(
    registry: ToolRegistry,
) -> None:
    registry.register(
        ToolDefinition(
            name="wilfred_status",
            description=(
                "Return public status information "
                "about the Wilfred runtime."
            ),
            handler=_runtime_status,
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            category="native",
            permission=ToolPermission.READ,
        )
    )

    def list_registered_tools() -> dict[str, list[dict[str, Any]]]:
        tools = sorted(
            registry.list_tools(),
            key=lambda item: item.name,
        )

        return {
            "tools": [
                _describe_tool(tool)
                for tool in tools
            ]
        }

    registry.register(
        ToolDefinition(
            name="wilfred_tools",
            description=(
                "List the tools currently registered "
                "in the Wilfred runtime."
            ),
            handler=list_registered_tools,
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            category="native",
            permission=ToolPermission.READ,
        )
    )
