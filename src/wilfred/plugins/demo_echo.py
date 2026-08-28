from __future__ import annotations

from typing import Protocol

from butler_core import (
    PlannerResult,
    PlannerStatus,
    ResolutionResult,
    ResolverDefinition,
    ToolPlan,
)

from wilfred.capabilities import (
    CapabilityDefinition,
    DomainDefinition,
)
from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.plugins.contracts import PluginDefinition
from wilfred.registry import ToolRegistry


class EchoProvider(Protocol):
    """Provider boundary used by the reference plugin."""

    def echo(self, message: str) -> str:
        ...


class LocalEchoProvider:
    """Dependency-free provider used by the built-in reference example."""

    def echo(self, message: str) -> str:
        return message


_provider: EchoProvider = LocalEchoProvider()


def echo_message(message: str) -> dict[str, str]:
    return {
        "message": _provider.echo(message),
    }


def resolve_demo_echo(message: str) -> ResolutionResult:
    prefix = "echo "
    normalized = message.strip()

    if not normalized.lower().startswith(prefix):
        return ResolutionResult.not_handled_result()

    echoed = normalized[len(prefix):].strip()
    if not echoed:
        return ResolutionResult.not_handled_result()

    return ResolutionResult.handled_result(
        PlannerResult(
            status=PlannerStatus.SUCCESS,
            duration_ms=0.0,
            plan=ToolPlan(
                tool_name="demo_echo",
                arguments={
                    "message": echoed,
                },
                confidence=1.0,
                reason="demo.echo deterministic resolver",
            ),
        )
    )


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


demo_domain = DomainDefinition(
    name="demo",
    description="Dependency-free examples for Wilfred plugin authors.",
)


demo_echo_capability = CapabilityDefinition(
    name="echo",
    domain="demo",
    description="Echo a message through the reference provider and tool.",
    resolvers=(
        ResolverDefinition(
            name="demo.echo.text",
            handler=resolve_demo_echo,
        ),
    ),
)


plugin = PluginDefinition(
    name="demo.echo",
    version="0.1.0",
    description=(
        "Reference capability plugin for Wilfred authors."
    ),
    register=register_demo_echo_tools,
    domains=(demo_domain,),
    capabilities=(demo_echo_capability,),
)
