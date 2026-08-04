from __future__ import annotations

import unittest

from wilfred import (
    ToolDefinition,
    ToolPermission,
    ToolRegistry,
)


def echo_handler(message: str) -> str:
    return message


class WilfredContractTests(unittest.TestCase):
    def test_registry_registers_and_lists_tool(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="echo",
            description="Return the supplied message.",
            handler=echo_handler,
            parameters={
                "message": {
                    "type": "string",
                }
            },
        )

        registry.register(tool)

        self.assertIs(registry.get("echo"), tool)
        self.assertEqual(registry.names(), ["echo"])
        self.assertEqual(registry.list_tools(), [tool])

    def test_duplicate_tool_is_rejected(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="echo",
            description="Return the supplied message.",
            handler=echo_handler,
        )

        registry.register(tool)

        with self.assertRaisesRegex(
            ValueError,
            "Tool already registered: echo",
        ):
            registry.register(tool)

    def test_default_permission_is_read(self) -> None:
        tool = ToolDefinition(
            name="echo",
            description="Return the supplied message.",
            handler=echo_handler,
        )

        self.assertEqual(
            tool.permission,
            ToolPermission.READ,
        )

    def test_public_import_surface(self) -> None:
        self.assertEqual(ToolPermission.ACTION.value, "ACTION")
        self.assertEqual(
            ToolPermission.DANGEROUS.value,
            "DANGEROUS",
        )


if __name__ == "__main__":
    unittest.main()
