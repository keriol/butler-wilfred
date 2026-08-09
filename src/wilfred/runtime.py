from __future__ import annotations

from collections.abc import Iterable

from butler_core import (
    ExecutionPolicy,
    PlannerProvider,
)

from wilfred.native import register_native_tools
from wilfred.planning import (
    PlannedExecution,
    PlannedExecutionResult,
)
from wilfred.plugins import (
    PluginDefinition,
    load_plugins,
)
from wilfred.registry import ToolRegistry


class WilfredRuntime:
    """Compose Wilfred's public tools, plugins and planned execution."""

    def __init__(
        self,
        *,
        provider: PlannerProvider,
        system_prompt: str,
        plugins: Iterable[PluginDefinition] = (),
        model: str | None = None,
        enabled: bool = True,
        policy: ExecutionPolicy | None = None,
    ) -> None:
        registry = ToolRegistry()

        register_native_tools(registry)
        load_plugins(registry, plugins)

        self._registry = registry
        self._planned_execution = PlannedExecution(
            registry,
            provider=provider,
            system_prompt=system_prompt,
            model=model,
            enabled=enabled,
            policy=policy,
        )

    def tool_names(self) -> list[str]:
        return self._registry.names()

    def execute_goal(
        self,
        message: str,
        *,
        confirmed: bool = False,
    ) -> PlannedExecutionResult:
        return self._planned_execution.execute(
            message,
            confirmed=confirmed,
        )


__all__ = ["WilfredRuntime"]
