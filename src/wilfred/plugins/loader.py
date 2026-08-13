from __future__ import annotations

from collections.abc import Iterable, Mapping
from importlib import import_module
from types import ModuleType

from wilfred.plugins.contracts import (
    PluginDefinition,
    PluginLoadResult,
)
from wilfred.registry import ToolRegistry


def _plugin_from_module(
    module: ModuleType,
) -> PluginDefinition:
    plugin = getattr(module, "plugin", None)

    if not isinstance(plugin, PluginDefinition):
        raise TypeError(
            f"Module {module.__name__!r} must expose "
            "'plugin' as PluginDefinition."
        )

    return plugin


def discover_plugins(
    module_names: Iterable[str],
) -> list[PluginDefinition]:
    plugins = [
        _plugin_from_module(import_module(module_name))
        for module_name in sorted(set(module_names))
    ]

    names = [plugin.name for plugin in plugins]

    if len(names) != len(set(names)):
        duplicates = sorted(
            name
            for name in set(names)
            if names.count(name) > 1
        )
        raise ValueError(
            "Duplicate plugin names: "
            f"{', '.join(duplicates)}"
        )

    return sorted(
        plugins,
        key=lambda plugin: plugin.name,
    )



def _configured_plugin_from_spec(
    spec: str,
    *,
    environ: Mapping[str, str],
) -> PluginDefinition:
    module_name, separator, attribute = spec.partition(":")

    module_name = module_name.strip()
    attribute = attribute.strip()

    if (
        separator != ":"
        or not module_name
        or not attribute
    ):
        raise ValueError(
            "Configured plugin specification must use "
            "'module:factory' format."
        )

    module = import_module(module_name)

    factory = getattr(
        module,
        attribute,
        None,
    )

    if not callable(factory):
        raise TypeError(
            f"Configured plugin factory {spec!r} "
            "must be callable."
        )

    plugin = factory(environ)

    if not isinstance(
        plugin,
        PluginDefinition,
    ):
        raise TypeError(
            f"Configured plugin factory {spec!r} "
            "must return PluginDefinition."
        )

    return plugin


def discover_configured_plugins(
    specs: Iterable[str],
    *,
    environ: Mapping[str, str],
) -> list[PluginDefinition]:
    plugins = [
        _configured_plugin_from_spec(
            spec,
            environ=environ,
        )
        for spec in sorted(
            {
                value.strip()
                for value in specs
                if value.strip()
            }
        )
    ]

    names = [
        plugin.name
        for plugin in plugins
    ]

    if len(names) != len(set(names)):
        duplicates = sorted(
            name
            for name in set(names)
            if names.count(name) > 1
        )

        raise ValueError(
            "Duplicate plugin names: "
            f"{', '.join(duplicates)}"
        )

    return sorted(
        plugins,
        key=lambda plugin: plugin.name,
    )



def load_plugin(
    registry: ToolRegistry,
    plugin: PluginDefinition,
) -> PluginLoadResult:
    candidate = ToolRegistry()
    plugin.register(candidate)

    tool_names = tuple(candidate.names())

    if not tool_names:
        raise ValueError(
            f"Plugin {plugin.name!r} registered no tools."
        )

    conflicts = sorted(
        set(registry.names()).intersection(tool_names)
    )

    if conflicts:
        raise ValueError(
            f"Plugin {plugin.name!r} conflicts with "
            f"registered tools: {', '.join(conflicts)}"
        )

    for tool in sorted(
        candidate.list_tools(),
        key=lambda item: item.name,
    ):
        registry.register(tool)

    return PluginLoadResult(
        plugin_name=plugin.name,
        tool_names=tool_names,
    )


def load_plugins(
    registry: ToolRegistry,
    plugins: Iterable[PluginDefinition],
) -> tuple[PluginLoadResult, ...]:
    ordered = sorted(
        plugins,
        key=lambda plugin: plugin.name,
    )

    names = [plugin.name for plugin in ordered]

    if len(names) != len(set(names)):
        duplicates = sorted(
            name
            for name in set(names)
            if names.count(name) > 1
        )
        raise ValueError(
            "Duplicate plugin names: "
            f"{', '.join(duplicates)}"
        )

    return tuple(
        load_plugin(registry, plugin)
        for plugin in ordered
    )
