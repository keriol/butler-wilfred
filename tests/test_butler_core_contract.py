from butler_core import (
    ExecutionEngine as CoreExecutionEngine,
    ExecutionRequest as CoreExecutionRequest,
    ToolDefinition as CoreToolDefinition,
    ToolPermission as CoreToolPermission,
    ToolRegistry as CoreToolRegistry,
)

from wilfred.execution import (
    ExecutionEngine,
    ExecutionRequest,
)
from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.registry import ToolRegistry


def test_models_are_core_contracts() -> None:
    assert ToolDefinition is CoreToolDefinition
    assert ToolPermission is CoreToolPermission


def test_registry_is_core_contract() -> None:
    assert ToolRegistry is CoreToolRegistry


def test_execution_is_core_contract() -> None:
    assert ExecutionEngine is CoreExecutionEngine
    assert ExecutionRequest is CoreExecutionRequest


def test_legacy_wilfred_import_path_still_executes() -> None:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="ping",
            description="Compatibility smoke.",
            handler=lambda: "pong",
        )
    )

    result = registry.execute("ping")

    assert result.ok
    assert result.value == "pong"
