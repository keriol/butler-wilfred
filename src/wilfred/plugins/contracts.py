from __future__ import annotations

from dataclasses import dataclass

from butler_core import PluginDefinition, PluginRegistrar


@dataclass(frozen=True)
class PluginLoadResult:
    plugin_name: str
    tool_names: tuple[str, ...]
    domain_names: tuple[str, ...] = ()
    capability_names: tuple[str, ...] = ()


__all__ = [
    "PluginDefinition",
    "PluginLoadResult",
    "PluginRegistrar",
]
