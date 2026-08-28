from __future__ import annotations

import unittest

from wilfred import (
    CapabilityDefinition,
    DomainDefinition,
    ToolDefinition,
    ToolRegistry,
)
from wilfred.plugins import (
    PluginDefinition,
    load_plugins,
)


def _register_tool(name: str):
    def register(registry: ToolRegistry) -> None:
        registry.register(
            ToolDefinition(
                name=name,
                description=f"Test tool {name}.",
                handler=lambda: name,
            )
        )

    return register


class PluginCapabilityTests(unittest.TestCase):
    def test_tool_only_plugin_remains_compatible(self) -> None:
        plugin = PluginDefinition(
            name="demo.tool-only",
            register=_register_tool("demo_tool_only"),
        )

        results = load_plugins(
            ToolRegistry(),
            [plugin],
        )

        self.assertEqual(results[0].domain_names, ())
        self.assertEqual(results[0].capability_names, ())

    def test_plugin_declares_domains_and_capabilities_deterministically(self) -> None:
        plugin = PluginDefinition(
            name="demo.media",
            register=_register_tool("demo_media"),
            domains=(
                DomainDefinition(name="system"),
                DomainDefinition(name="media"),
            ),
            capabilities=(
                CapabilityDefinition(
                    name="search",
                    domain="media",
                ),
                CapabilityDefinition(
                    name="status",
                    domain="system",
                ),
                CapabilityDefinition(
                    name="playback",
                    domain="media",
                ),
            ),
        )

        self.assertEqual(
            tuple(domain.identity for domain in plugin.domains),
            ("media", "system"),
        )
        self.assertEqual(
            tuple(
                capability.identity
                for capability in plugin.capabilities
            ),
            (
                "media.playback",
                "media.search",
                "system.status",
            ),
        )

        results = load_plugins(
            ToolRegistry(),
            [plugin],
        )

        self.assertEqual(
            results[0].domain_names,
            ("media", "system"),
        )
        self.assertEqual(
            results[0].capability_names,
            (
                "media.playback",
                "media.search",
                "system.status",
            ),
        )

    def test_capability_must_belong_to_plugin_owned_domain(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "references undeclared domain 'media'",
        ):
            PluginDefinition(
                name="demo.invalid",
                register=_register_tool("demo_invalid"),
                capabilities=(
                    CapabilityDefinition(
                        name="playback",
                        domain="media",
                    ),
                ),
            )

    def test_duplicate_domain_ownership_is_rejected_before_tool_loading(self) -> None:
        registry = ToolRegistry()
        first = PluginDefinition(
            name="demo.first",
            register=_register_tool("demo_first"),
            domains=(DomainDefinition(name="media"),),
        )
        second = PluginDefinition(
            name="demo.second",
            register=_register_tool("demo_second"),
            domains=(DomainDefinition(name="media"),),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate domain identity 'media'",
        ):
            load_plugins(
                registry,
                [second, first],
            )

        self.assertEqual(registry.names(), [])

    def test_duplicate_declarations_inside_plugin_are_rejected(self) -> None:
        domain = DomainDefinition(name="media")

        with self.assertRaisesRegex(
            ValueError,
            "declares duplicate domains: media",
        ):
            PluginDefinition(
                name="demo.duplicate",
                register=_register_tool("demo_duplicate"),
                domains=(domain, domain),
            )


if __name__ == "__main__":
    unittest.main()
