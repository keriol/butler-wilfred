from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Callable

from wilfred.capabilities import (
    CapabilityDefinition,
    DomainDefinition,
)
from wilfred.verification import GoalExpectation


if TYPE_CHECKING:
    from wilfred.registry import ToolRegistry


PluginRegistrar = Callable[["ToolRegistry"], None]

_PLUGIN_NAME_PATTERN = re.compile(
    r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*"
)


@dataclass(frozen=True)
class PluginDefinition:
    name: str
    register: PluginRegistrar
    description: str = ""
    version: str = "0.1.0"
    domains: tuple[DomainDefinition, ...] = ()
    capabilities: tuple[CapabilityDefinition, ...] = ()
    verification: tuple[GoalExpectation, ...] = ()

    def __post_init__(self) -> None:
        if _PLUGIN_NAME_PATTERN.fullmatch(self.name) is None:
            raise ValueError(
                "Invalid plugin name: "
                f"{self.name!r}"
            )

        if not self.version.strip():
            raise ValueError(
                "Plugin version cannot be empty."
            )

        if not callable(self.register):
            raise TypeError(
                "Plugin register must be callable."
            )

        domains = tuple(self.domains)
        capabilities = tuple(self.capabilities)
        verification = tuple(self.verification)

        if not all(
            isinstance(domain, DomainDefinition)
            for domain in domains
        ):
            raise TypeError(
                "Plugin domains must contain DomainDefinition values."
            )

        if not all(
            isinstance(capability, CapabilityDefinition)
            for capability in capabilities
        ):
            raise TypeError(
                "Plugin capabilities must contain CapabilityDefinition values."
            )

        if not all(
            isinstance(expectation, GoalExpectation)
            for expectation in verification
        ):
            raise TypeError(
                "Plugin verification must contain GoalExpectation values."
            )

        domain_names = [domain.identity for domain in domains]
        duplicate_domains = sorted(
            name
            for name in set(domain_names)
            if domain_names.count(name) > 1
        )

        if duplicate_domains:
            raise ValueError(
                f"Plugin {self.name!r} declares duplicate domains: "
                f"{', '.join(duplicate_domains)}"
            )

        capability_names = [
            capability.identity
            for capability in capabilities
        ]
        duplicate_capabilities = sorted(
            name
            for name in set(capability_names)
            if capability_names.count(name) > 1
        )

        if duplicate_capabilities:
            raise ValueError(
                f"Plugin {self.name!r} declares duplicate capabilities: "
                f"{', '.join(duplicate_capabilities)}"
            )

        verification_names = [
            expectation.identity
            for expectation in verification
        ]
        duplicate_verification = sorted(
            name
            for name in set(verification_names)
            if verification_names.count(name) > 1
        )

        if duplicate_verification:
            raise ValueError(
                f"Plugin {self.name!r} declares duplicate verification expectations: "
                f"{', '.join(duplicate_verification)}"
            )

        owned_domains = set(domain_names)
        owned_capabilities = set(capability_names)

        for capability in capabilities:
            if capability.domain not in owned_domains:
                raise ValueError(
                    f"Plugin {self.name!r} capability "
                    f"{capability.identity!r} references undeclared domain "
                    f"{capability.domain!r}."
                )

        for expectation in verification:
            if expectation.capability not in owned_capabilities:
                raise ValueError(
                    f"Plugin {self.name!r} verification expectation "
                    f"{expectation.identity!r} references undeclared capability "
                    f"{expectation.capability!r}."
                )

        object.__setattr__(
            self,
            "domains",
            tuple(sorted(domains, key=lambda domain: domain.identity)),
        )
        object.__setattr__(
            self,
            "capabilities",
            tuple(
                sorted(
                    capabilities,
                    key=lambda capability: capability.identity,
                )
            ),
        )
        object.__setattr__(
            self,
            "verification",
            tuple(
                sorted(
                    verification,
                    key=lambda expectation: expectation.identity,
                )
            ),
        )


@dataclass(frozen=True)
class PluginLoadResult:
    plugin_name: str
    tool_names: tuple[str, ...]
    domain_names: tuple[str, ...] = ()
    capability_names: tuple[str, ...] = ()
