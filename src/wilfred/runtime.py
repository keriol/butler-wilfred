from __future__ import annotations

from collections.abc import Iterable

from butler_core import (
    ExecutionPolicy,
    PlannerProvider,
    ResolverDefinition,
)

from wilfred import __version__
from wilfred.capability_registry import CapabilityRegistry
from wilfred.native import (
    describe_tool,
    register_native_tools,
)
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
        resolvers: Iterable[ResolverDefinition] = (),
        acknowledgement_adapter: OutputAdapter | None = None,
        acknowledgement_text: str | None = None,
    ) -> None:
        registry = ToolRegistry()
        loaded_plugins = tuple(plugins)
        capability_registry = CapabilityRegistry.from_plugins(loaded_plugins)

        register_native_tools(registry)
        load_plugins(registry, loaded_plugins)

        self._registry = registry
        self._capability_registry = capability_registry
        self._acknowledgement_adapter = acknowledgement_adapter
        self._acknowledgement_text = acknowledgement_text
        self._planned_execution = PlannedExecution(
            registry,
            provider=provider,
            system_prompt=system_prompt,
            model=model,
            enabled=enabled,
            policy=policy,
            resolvers=tuple(resolvers),
            before_fallback=self._acknowledge_provider_latency,
        )

    def tool_names(self) -> list[str]:
        return self._registry.names()

    def domain_names(self) -> list[str]:
        return self._capability_registry.domain_names()

    def capability_names(self) -> list[str]:
        return self._capability_registry.capability_names()

    def describe_runtime(self) -> dict[str, object]:
        """Return public, credential-free runtime metadata."""

        return {
            "name": "Wilfred",
            "status": "ok",
            "version": __version__,
            "runtime": "goal-runtime",
            "tool_count": len(self._registry.names()),
            "domain_count": len(self._capability_registry.domain_names()),
            "capability_count": len(
                self._capability_registry.capability_names()
            ),
        }

    def describe_tools(self) -> list[dict[str, object]]:
        """Return deterministic public tool descriptions."""

        tools = sorted(
            self._registry.list_tools(),
            key=lambda item: item.name,
        )

        return [describe_tool(tool) for tool in tools]

    def describe_domains(self) -> list[dict[str, str]]:
        """Return deterministic public domain metadata."""

        return self._capability_registry.describe_domains()

    def describe_capabilities(self) -> list[dict[str, str]]:
        """Return deterministic public capability metadata."""

        return self._capability_registry.describe_capabilities()

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
