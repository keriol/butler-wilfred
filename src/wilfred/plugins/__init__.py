"""Public plugin contract and deterministic loader."""

from wilfred.plugins.contracts import (
    PluginDefinition,
    PluginLoadResult,
)
from wilfred.plugins.loader import (
    discover_plugins,
    load_plugin,
    load_plugins,
)


__all__ = [
    "PluginDefinition",
    "PluginLoadResult",
    "discover_plugins",
    "load_plugin",
    "load_plugins",
]
