from __future__ import annotations

from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.plugins.contracts import PluginDefinition
from wilfred.registry import ToolRegistry


def echo_message(message: str) -> dict[str, str]:
    return {
        "message": message,
    }


def register_demo_echo_tools(
    registry: ToolRegistry,
) -> None:
    registry.register(
        ToolDefinition(
            name="demo_echo",
            description=(
                "Return the supplied message unchanged."
            ),
            handler=echo_message,
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                    }
                },
                "required": [
                    "message",
                ],
                "additionalProperties": False,
            },
            category="demo",
            permission=ToolPermission.READ,
        )
    )


plugin = PluginDefinition(
    name="demo.echo",
    version="0.1.0",
    description=(
        "Harmless demonstration plugin for Wilfred."
    ),
    register=register_demo_echo_tools,
)
