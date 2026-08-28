from __future__ import annotations

from dataclasses import dataclass
import re

from butler_core import ResolverDefinition


_PUBLIC_NAME_PATTERN = re.compile(
    r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*"
)


def _validate_public_name(kind: str, value: str) -> None:
    if _PUBLIC_NAME_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"Invalid {kind} name: {value!r}"
        )


@dataclass(frozen=True)
class DomainDefinition:
    """Provider-neutral public identity for one Wilfred behavior domain."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        _validate_public_name("domain", self.name)

    @property
    def identity(self) -> str:
        """Return the stable public domain identity."""

        return self.name


@dataclass(frozen=True)
class CapabilityDefinition:
    """Provider-neutral public identity for something Wilfred can do."""

    name: str
    domain: str
    description: str = ""
    resolvers: tuple[ResolverDefinition, ...] = ()

    def __post_init__(self) -> None:
        _validate_public_name("capability", self.name)
        _validate_public_name("domain", self.domain)

        resolvers = tuple(self.resolvers)

        if not all(
            isinstance(resolver, ResolverDefinition)
            for resolver in resolvers
        ):
            raise TypeError(
                "Capability resolvers must contain ResolverDefinition values."
            )

        resolver_names = [resolver.name for resolver in resolvers]
        duplicate_resolvers = sorted(
            name
            for name in set(resolver_names)
            if resolver_names.count(name) > 1
        )

        if duplicate_resolvers:
            raise ValueError(
                f"Capability {self.identity!r} declares duplicate resolvers: "
                f"{', '.join(duplicate_resolvers)}"
            )

        object.__setattr__(self, "resolvers", resolvers)

    @property
    def identity(self) -> str:
        """Return the stable domain-qualified capability identity."""

        return f"{self.domain}.{self.name}"


__all__ = [
    "CapabilityDefinition",
    "DomainDefinition",
]
