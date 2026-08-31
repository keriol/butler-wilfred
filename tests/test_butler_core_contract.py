from butler_core import (
    CapabilityDefinition as CoreCapabilityDefinition,
    DomainDefinition as CoreDomainDefinition,
    ExecutionEngine as CoreExecutionEngine,
    ExecutionRequest as CoreExecutionRequest,
    GoalExpectation as CoreGoalExpectation,
    OutputAdapter as CoreOutputAdapter,
    OutputDeliveryResult as CoreOutputDeliveryResult,
    OutputDeliveryStatus as CoreOutputDeliveryStatus,
    OutputKind as CoreOutputKind,
    OutputPriority as CoreOutputPriority,
    OutputRequest as CoreOutputRequest,
    PluginDefinition as CorePluginDefinition,
    ToolDefinition as CoreToolDefinition,
    ToolPermission as CoreToolPermission,
    ToolRegistry as CoreToolRegistry,
)

from wilfred import (
    CapabilityDefinition,
    DomainDefinition,
    GoalExpectation,
    PluginDefinition,
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


def test_semantic_contributions_are_core_contracts() -> None:
    assert DomainDefinition is CoreDomainDefinition
    assert CapabilityDefinition is CoreCapabilityDefinition
    assert PluginDefinition is CorePluginDefinition
    assert GoalExpectation is CoreGoalExpectation


def test_output_is_core_contract() -> None:
    from wilfred.output import (
        OutputAdapter,
        OutputDeliveryResult,
        OutputDeliveryStatus,
        OutputKind,
        OutputPriority,
        OutputRequest,
    )

    assert OutputAdapter is CoreOutputAdapter
    assert OutputDeliveryResult is CoreOutputDeliveryResult
    assert OutputDeliveryStatus is CoreOutputDeliveryStatus
    assert OutputKind is CoreOutputKind
    assert OutputPriority is CoreOutputPriority
    assert OutputRequest is CoreOutputRequest


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
