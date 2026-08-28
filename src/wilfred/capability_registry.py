from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

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

    def register_plugin(self, plugin: PluginDefinition) -> None:
        domain_conflicts = sorted(
            domain.identity
            for domain in plugin.domains
            if domain.identity in self._domains
        )
        capability_conflicts = sorted(
            capability.identity
            for capability in plugin.capabilities
            if capability.identity in self._capabilities
        )

        if domain_conflicts:
            raise ValueError(
                "Duplicate domain identities: "
                + ", ".join(domain_conflicts)
            )

        if capability_conflicts:
            raise ValueError(
                "Duplicate capability identities: "
                + ", ".join(capability_conflicts)
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
