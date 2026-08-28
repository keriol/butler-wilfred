from __future__ import annotations

import unittest

from wilfred import (
    ExecutionStatus,
    ToolPermission,
    ToolRegistry,
    WilfredRuntime,
)
from wilfred.plugins import (
    PluginDefinition,
    discover_plugins,
    load_plugins,
)


class WilfredPluginTests(unittest.TestCase):
    def test_discovers_public_plugin_module(self) -> None:
        plugins = discover_plugins(
            [
                "wilfred.plugins.demo_echo",
            ]
        )

        self.assertEqual(
            [plugin.name for plugin in plugins],
            ["demo.echo"],
        )

    def test_invalid_plugin_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Invalid plugin name",
        ):
            PluginDefinition(
                name="Invalid Plugin",
                register=lambda registry: None,
            )

    def test_empty_plugin_is_rejected(self) -> None:
        plugin = PluginDefinition(
            name="demo.empty",
            register=lambda registry: None,
        )

        with self.assertRaisesRegex(
            ValueError,
            "registered no tools",
        ):
            load_plugins(
                ToolRegistry(),
                [plugin],
            )

    def test_demo_tool_is_read_only(self) -> None:
        registry = ToolRegistry()
        plugins = discover_plugins(
            [
                "wilfred.plugins.demo_echo",
            ]
        )

        load_plugins(registry, plugins)

        tool = registry.get("demo_echo")

        self.assertIsNotNone(tool)
        self.assertEqual(
            tool.permission,
            ToolPermission.READ,
        )

    def test_load_result_is_deterministic(self) -> None:
        registry = ToolRegistry()
        plugins = discover_plugins(
            [
                "wilfred.plugins.demo_echo",
            ]
        )

        results = load_plugins(registry, plugins)

        self.assertEqual(
            results[0].plugin_name,
            "demo.echo",
        )
        self.assertEqual(
            results[0].tool_names,
            ("demo_echo",),
        )
        self.assertEqual(
            results[0].domain_names,
            ("demo",),
        )
        self.assertEqual(
            results[0].capability_names,
            ("demo.echo",),
        )
        self.assertEqual(
            registry.names(),
            ["demo_echo"],
        )

    def test_demo_execution_is_deterministic(self) -> None:
        registry = ToolRegistry()
        plugins = discover_plugins(
            [
                "wilfred.plugins.demo_echo",
            ]
        )

        load_plugins(registry, plugins)

        first = registry.execute(
            "demo_echo",
            message="hello",
        )
        second = registry.execute(
            "demo_echo",
            message="hello",
        )

        self.assertEqual(
            first.status,
            ExecutionStatus.SUCCESS,
        )
        self.assertEqual(
            first.value,
            {
                "message": "hello",
            },
        )
        self.assertEqual(
            first.value,
            second.value,
        )

    def test_demo_capability_resolves_and_executes_without_planner(self) -> None:
        plugins = discover_plugins(
            [
                "wilfred.plugins.demo_echo",
            ]
        )

        runtime = WilfredRuntime(
            provider=lambda *args: (_ for _ in ()).throw(
                AssertionError("planner provider must not be called")
            ),
            system_prompt="Reference plugin test.",
            plugins=plugins,
        )

        result = runtime.execute_goal("echo hello from capability")

        self.assertIsNotNone(result.execution)
        self.assertEqual(
            result.execution.status,
            ExecutionStatus.SUCCESS,
        )
        self.assertEqual(
            result.execution.value,
            {"message": "hello from capability"},
        )
        self.assertEqual(
            runtime.domain_names(),
            ["demo"],
        )
        self.assertEqual(
            runtime.capability_names(),
            ["demo.echo"],
        )

    def test_unknown_tool_is_rejected(self) -> None:
        registry = ToolRegistry()

        result = registry.execute("missing")

        self.assertEqual(
            result.status,
            ExecutionStatus.TOOL_NOT_FOUND,
        )
        self.assertEqual(
            result.error_code,
            "tool_not_found",
        )


if __name__ == "__main__":
    unittest.main()
