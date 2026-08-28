from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from butler_core import ResolverDefinition

from wilfred.capabilities import CapabilityDefinition, DomainDefinition


if TYPE_CHECKING:
    from wilfred.plugins.contracts import PluginDefinition


@dataclass(frozen=True)
class DomainRegistration:
    definition: DomainDefinition
    owner_plugin: str


@dataclass(frozen=True)
class CapabilityRegistration:
    definition: CapabilityDefinition
    owner_plugin: str


class CapabilityRegistry:
    """Deterministic semantic registry for loaded Wilfred domains/capabilities."""

    def __init__(self) -> None:
        self._domains: dict[str, DomainRegistration] = {}
        self._capabilities: dict[str, CapabilityRegistration] = {}
        self._resolver_owners: dict[str, str] = {}

    def register_plugin(self, plugin: PluginDefinition) -> None:
        for domain in plugin.domains:
            previous = self._domains.get(domain.identity)

            if previous is not None:
                raise ValueError(
                    f"Duplicate domain identity {domain.identity!r} "
                    f"declared by plugins {previous.owner_plugin!r} "
                    f"and {plugin.name!r}."
                )

        for capability in plugin.capabilities:
            previous = self._capabilities.get(capability.identity)

            if previous is not None:
                raise ValueError(
                    f"Duplicate capability identity {capability.identity!r} "
                    f"declared by plugins {previous.owner_plugin!r} "
                    f"and {plugin.name!r}."
                )

            for resolver in capability.resolvers:
                previous_capability = self._resolver_owners.get(resolver.name)

                if previous_capability is not None:
                    raise ValueError(
                        f"Duplicate resolver name {resolver.name!r} "
                        f"owned by capabilities {previous_capability!r} "
                        f"and {capability.identity!r}."
                    )

        for domain in plugin.domains:
            self._domains[domain.identity] = DomainRegistration(
                definition=domain,
                owner_plugin=plugin.name,
            )

        for capability in plugin.capabilities:
            self._capabilities[capability.identity] = CapabilityRegistration(
                definition=capability,
                owner_plugin=plugin.name,
            )
            for resolver in capability.resolvers:
                self._resolver_owners[resolver.name] = capability.identity

    @classmethod
    def from_plugins(
        cls,
        plugins: Iterable[PluginDefinition],
    ) -> "CapabilityRegistry":
        registry = cls()
        for plugin in sorted(plugins, key=lambda item: item.name):
            registry.register_plugin(plugin)
        return registry

    def domain_names(self) -> list[str]:
        return sorted(self._domains)

    def capability_names(self) -> list[str]:
        return sorted(self._capabilities)

    def resolver_definitions(self) -> tuple[ResolverDefinition, ...]:
        """Compose capability-owned resolvers in deterministic order."""

        resolvers: list[ResolverDefinition] = []
        for _, registration in sorted(self._capabilities.items()):
            resolvers.extend(registration.definition.resolvers)
        return tuple(resolvers)

    def describe_domains(self) -> list[dict[str, str]]:
        return [
            {
                "name": registration.definition.identity,
                "description": registration.definition.description,
                "owner_plugin": registration.owner_plugin,
            }
            for _, registration in sorted(self._domains.items())
        ]

    def describe_capabilities(self) -> list[dict[str, str]]:
        return [
            {
                "name": registration.definition.identity,
                "domain": registration.definition.domain,
                "description": registration.definition.description,
                "owner_plugin": registration.owner_plugin,
            }
            for _, registration in sorted(self._capabilities.items())
        ]


__all__ = [
    "CapabilityRegistration",
    "CapabilityRegistry",
    "DomainRegistration",
]
