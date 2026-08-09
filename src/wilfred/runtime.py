from __future__ import annotations

from collections.abc import Iterable

from butler_core import (
    ExecutionPolicy,
    PlannerProvider,
)

from wilfred.native import register_native_tools
from wilfred.output import (
    OutputAdapter,
    OutputKind,
    OutputRequest,
)
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
        acknowledgement_adapter: OutputAdapter | None = None,
        acknowledgement_text: str | None = None,
    ) -> None:
        registry = ToolRegistry()

        register_native_tools(registry)
        load_plugins(registry, plugins)

        self._registry = registry
        self._acknowledgement_adapter = acknowledgement_adapter
        self._acknowledgement_text = acknowledgement_text
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
        self._acknowledge_provider_latency()

        return self._planned_execution.execute(
            message,
            confirmed=confirmed,
        )

    def _acknowledge_provider_latency(self) -> None:
        adapter = self._acknowledgement_adapter
        text = self._acknowledgement_text

        if adapter is None or text is None:
            return

        try:
            adapter.deliver(
                OutputRequest(
                    content=text,
                    kind=OutputKind.SPEECH,
                )
            )
        except Exception:
            # A best-effort acknowledgement must never block
            # planning or alter execution authorization.
            return


__all__ = ["WilfredRuntime"]
