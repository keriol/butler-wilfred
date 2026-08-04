from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Callable


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


@dataclass(frozen=True)
class PluginLoadResult:
    plugin_name: str
    tool_names: tuple[str, ...]
