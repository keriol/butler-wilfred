"""Public Wilfred Butler runtime."""

from importlib.metadata import (
    PackageNotFoundError,
    version as package_version,
)

from wilfred.config import (
    ButlerIdentity,
    ConfigurationError,
    RuntimeConfig,
    load_config,
)
from wilfred.execution import (
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    validate_arguments,
)
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.output import (
    OutputAdapter,
    OutputCapability,
    OutputDeliveryResult,
    OutputDeliveryStatus,
    OutputKind,
    OutputPriority,
    OutputRequest,
)
from wilfred.persistence import (
    SQLiteWorkflowStore,
    WorkflowPersistenceError,
    WorkflowRecord,
    WorkflowStore,
)
from wilfred.planning import (
    PlannedExecution,
    PlannedExecutionResult,
)
from wilfred.plugins import (
    PluginDefinition,
    PluginLoadResult,
    discover_plugins,
    load_plugin,
    load_plugins,
)
from wilfred.registry import ToolRegistry
from wilfred.workflows import (
    ReadActionVerifyRequest,
    ReadActionVerifyResult,
    ReadActionVerifyWorkflow,
    VerificationStatus,
)


try:
    __version__ = package_version("wilfred-butler")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = [
    "ButlerIdentity",
    "ConfigurationError",
    "ExecutionEngine",
    "ExecutionPolicy",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
    "OutputAdapter",
    "OutputCapability",
    "OutputDeliveryResult",
    "OutputDeliveryStatus",
    "OutputKind",
    "OutputPriority",
    "OutputRequest",
    "PlannedExecution",
    "PlannedExecutionResult",
    "PluginDefinition",
    "PluginLoadResult",
    "ReadActionVerifyRequest",
    "ReadActionVerifyResult",
    "ReadActionVerifyWorkflow",
    "RuntimeConfig",
    "SQLiteWorkflowStore",
    "ToolDefinition",
    "ToolPermission",
    "ToolRegistry",
    "VerificationStatus",
    "WorkflowPersistenceError",
    "WorkflowRecord",
    "WorkflowStore",
    "discover_plugins",
    "load_config",
    "load_plugin",
    "load_plugins",
    "validate_arguments",
    "__version__",
]
