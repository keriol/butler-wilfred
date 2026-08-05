from __future__ import annotations

from time import sleep
import unittest

from wilfred import (
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    ToolDefinition,
    ToolPermission,
    ToolRegistry,
)


def register_tool(
    registry: ToolRegistry,
    *,
    name: str,
    handler,
    permission: ToolPermission = ToolPermission.READ,
    timeout_seconds: int = 10,
    parameters=None,
) -> None:
    registry.register(
        ToolDefinition(
            name=name,
            description=f"Test tool {name}.",
            handler=handler,
            permission=permission,
            timeout_seconds=timeout_seconds,
            parameters=parameters or {},
        )
    )


class ExecutionEngineTests(unittest.TestCase):
    def test_read_executes_without_confirmation(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="read",
            handler=lambda: {"state": "ok"},
        )

        result = ExecutionEngine(registry).execute(
            ExecutionRequest(tool_name="read")
        )

        self.assertTrue(result.ok)
        self.assertEqual(
            result.status,
            ExecutionStatus.SUCCESS,
        )
        self.assertEqual(
            result.value,
            {"state": "ok"},
        )
        self.assertTrue(result.execution_id)
        self.assertGreaterEqual(result.duration_ms, 0)

    def test_action_requires_confirmation(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="action",
            handler=lambda: "done",
            permission=ToolPermission.ACTION,
        )

        result = ExecutionEngine(registry).execute(
            ExecutionRequest(tool_name="action")
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.CONFIRMATION_REQUIRED,
        )

    def test_confirmed_action_executes(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="action",
            handler=lambda: "done",
            permission=ToolPermission.ACTION,
        )

        result = ExecutionEngine(registry).execute(
            ExecutionRequest(
                tool_name="action",
                confirmed=True,
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.value, "done")

    def test_dangerous_is_denied_by_default(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="danger",
            handler=lambda: "done",
            permission=ToolPermission.DANGEROUS,
        )

        result = ExecutionEngine(registry).execute(
            ExecutionRequest(
                tool_name="danger",
                confirmed=True,
            )
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.DENIED,
        )
        self.assertEqual(
            result.error_code,
            "dangerous_denied",
        )

    def test_dangerous_can_be_enabled(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="danger",
            handler=lambda: "done",
            permission=ToolPermission.DANGEROUS,
        )

        engine = ExecutionEngine(
            registry,
            policy=ExecutionPolicy(
                allow_dangerous=True,
            ),
        )

        pending = engine.execute(
            ExecutionRequest(tool_name="danger")
        )
        confirmed = engine.execute(
            ExecutionRequest(
                tool_name="danger",
                confirmed=True,
            )
        )

        self.assertEqual(
            pending.status,
            ExecutionStatus.CONFIRMATION_REQUIRED,
        )
        self.assertTrue(confirmed.ok)

    def test_arguments_are_validated(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="echo",
            handler=lambda message: message,
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                    }
                },
                "required": ["message"],
                "additionalProperties": False,
            },
        )

        missing = ExecutionEngine(registry).execute(
            ExecutionRequest(tool_name="echo")
        )
        wrong_type = ExecutionEngine(registry).execute(
            ExecutionRequest(
                tool_name="echo",
                arguments={"message": 42},
            )
        )
        extra = ExecutionEngine(registry).execute(
            ExecutionRequest(
                tool_name="echo",
                arguments={
                    "message": "hello",
                    "extra": True,
                },
            )
        )

        self.assertEqual(
            missing.status,
            ExecutionStatus.INVALID_ARGUMENTS,
        )
        self.assertIn(
            "$.message: required argument missing.",
            missing.validation_errors,
        )
        self.assertTrue(
            any(
                "expected string" in error
                for error in wrong_type.validation_errors
            )
        )
        self.assertIn(
            "$.extra: unexpected argument.",
            extra.validation_errors,
        )

    def test_unknown_tool_is_structured(self) -> None:
        result = ExecutionEngine(
            ToolRegistry()
        ).execute(
            ExecutionRequest(tool_name="missing")
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.TOOL_NOT_FOUND,
        )
        self.assertEqual(
            result.error_code,
            "tool_not_found",
        )

    def test_handler_exception_is_structured(self) -> None:
        def fail() -> None:
            raise RuntimeError("boom")

        registry = ToolRegistry()
        register_tool(
            registry,
            name="fail",
            handler=fail,
        )

        result = ExecutionEngine(registry).execute(
            ExecutionRequest(tool_name="fail")
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.ERROR,
        )
        self.assertEqual(
            result.error_code,
            "RuntimeError",
        )
        self.assertEqual(
            result.error_message,
            "boom",
        )

    def test_timeout_is_structured(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="slow",
            handler=lambda: sleep(1.2),
            timeout_seconds=1,
        )

        result = ExecutionEngine(registry).execute(
            ExecutionRequest(tool_name="slow")
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.TIMEOUT,
        )
        self.assertEqual(
            result.error_code,
            "timeout",
        )

    def test_registry_routes_through_engine(self) -> None:
        registry = ToolRegistry()
        register_tool(
            registry,
            name="read",
            handler=lambda: "ok",
        )

        result = registry.execute("read")

        self.assertEqual(
            result.status,
            ExecutionStatus.SUCCESS,
        )
        self.assertEqual(result.value, "ok")


if __name__ == "__main__":
    unittest.main()
