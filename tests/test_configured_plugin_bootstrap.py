from __future__ import annotations

from pathlib import Path
import sys

import pytest

from wilfred import ToolDefinition, ToolPermission
from wilfred.plugins import (
    discover_configured_plugins,
)


def write_factory(
    directory: Path,
    *,
    return_plugin: bool = True,
) -> str:
    module = directory / "sample_distribution_plugin.py"

    body = """
from wilfred import (
    PluginDefinition,
    ToolDefinition,
    ToolPermission,
)


def factory(environ):
    expected = environ["PLUGIN_TEST_VALUE"]

    def register(registry):
        registry.register(
            ToolDefinition(
                name="sample_configured_tool",
                description="Configured test tool.",
                handler=lambda: {"value": expected},
                permission=ToolPermission.READ,
            )
        )

    return PluginDefinition(
        name="sample-configured",
        register=register,
    )
"""

    if not return_plugin:
        body = """
def factory(environ):
    return object()
"""

    module.write_text(
        body.strip() + "\n",
        encoding="utf-8",
    )

    return "sample_distribution_plugin:factory"


def test_discover_configured_plugin_factory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = write_factory(tmp_path)

    monkeypatch.syspath_prepend(
        str(tmp_path)
    )

    plugins = discover_configured_plugins(
        [spec],
        environ={
            "PLUGIN_TEST_VALUE": "ready",
        },
    )

    assert [
        plugin.name
        for plugin in plugins
    ] == [
        "sample-configured",
    ]


def test_configured_plugin_spec_requires_factory() -> None:
    with pytest.raises(
        ValueError,
        match="module:factory",
    ):
        discover_configured_plugins(
            ["invalid"],
            environ={},
        )


def test_configured_factory_must_return_plugin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = write_factory(
        tmp_path,
        return_plugin=False,
    )

    monkeypatch.syspath_prepend(
        str(tmp_path)
    )

    sys.modules.pop(
        "sample_distribution_plugin",
        None,
    )

    with pytest.raises(
        TypeError,
        match="PluginDefinition",
    ):
        discover_configured_plugins(
            [spec],
            environ={},
        )
