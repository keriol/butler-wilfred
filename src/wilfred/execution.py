from __future__ import annotations

from collections.abc import Mapping
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic_ns
from typing import Any
from uuid import uuid4

from wilfred.models import ToolDefinition, ToolPermission
from wilfred.registry import ToolRegistry


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    CONFIRMATION_REQUIRED = "confirmation_required"
    DENIED = "denied"
    INVALID_ARGUMENTS = "invalid_arguments"
    TOOL_NOT_FOUND = "tool_not_found"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class ExecutionPolicy:
    require_action_confirmation: bool = True
    require_dangerous_confirmation: bool = True
    allow_dangerous: bool = False


@dataclass(frozen=True)
class ExecutionRequest:
    tool_name: str
    arguments: Mapping[str, Any] = field(
        default_factory=dict
    )
    confirmed: bool = False
    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    tool_name: str
    status: ExecutionStatus
    duration_ms: float
    permission: ToolPermission | None = None
    value: Any = None
    error_code: str | None = None
    error_message: str | None = None
    validation_errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status is ExecutionStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        error = None

        if self.error_code is not None:
            error = {
                "code": self.error_code,
                "message": self.error_message,
            }

        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "permission": (
                self.permission.value
                if self.permission is not None
                else None
            ),
            "value": self.value,
            "error": error,
            "validation_errors": list(
                self.validation_errors
            ),
        }


def _matches_type(expected: str, value: Any) -> bool:
    if expected == "string":
        return isinstance(value, str)

    if expected == "integer":
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
        )

    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    if expected == "boolean":
        return isinstance(value, bool)

    if expected == "object":
        return isinstance(value, Mapping)

    if expected == "array":
        return isinstance(value, list)

    if expected == "null":
        return value is None

    return False


def _validate_value(
    schema: Mapping[str, Any],
    value: Any,
    path: str,
) -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")

    if expected is not None:
        expected_types = (
            [expected]
            if isinstance(expected, str)
            else expected
            if isinstance(expected, list)
            else []
        )

        if not expected_types:
            return [
                f"{path}: invalid schema type declaration."
            ]

        if not any(
            isinstance(item, str)
            and _matches_type(item, value)
            for item in expected_types
        ):
            names = " or ".join(
                str(item)
                for item in expected_types
            )
            return [
                f"{path}: expected {names}, "
                f"received {type(value).__name__}."
            ]

    enum = schema.get("enum")

    if isinstance(enum, list) and value not in enum:
        errors.append(
            f"{path}: value must be one of {enum!r}."
        )

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get(
            "additionalProperties",
            True,
        )

        if not isinstance(properties, Mapping):
            return [
                f"{path}: schema properties must be an object."
            ]

        if not isinstance(required, list):
            return [
                f"{path}: schema required must be an array."
            ]

        for name in required:
            if name not in value:
                errors.append(
                    f"{path}.{name}: required argument missing."
                )

        if additional is False:
            for name in sorted(
                set(value) - set(properties)
            ):
                errors.append(
                    f"{path}.{name}: unexpected argument."
                )

        for name, child_schema in properties.items():
            if name not in value:
                continue

            if not isinstance(child_schema, Mapping):
                errors.append(
                    f"{path}.{name}: invalid property schema."
                )
                continue

            errors.extend(
                _validate_value(
                    child_schema,
                    value[name],
                    f"{path}.{name}",
                )
            )

    if isinstance(value, list):
        item_schema = schema.get("items")

        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                errors.extend(
                    _validate_value(
                        item_schema,
                        item,
                        f"{path}[{index}]",
                    )
                )

    return errors


def validate_arguments(
    tool: ToolDefinition,
    arguments: Mapping[str, Any],
) -> tuple[str, ...]:
    schema: Mapping[str, Any] = tool.parameters

    if not schema:
        return ()

    schema_keywords = {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "enum",
        "items",
    }

    if not set(schema).intersection(schema_keywords):
        schema = {
            "type": "object",
            "properties": schema,
        }

    return tuple(
        _validate_value(
            schema,
            arguments,
            "$",
        )
    )


class ExecutionEngine:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        policy: ExecutionPolicy | None = None,
    ) -> None:
        self._registry = registry
        self._policy = policy or ExecutionPolicy()

    def execute(
        self,
        request: ExecutionRequest,
    ) -> ExecutionResult:
        started = monotonic_ns()
        tool = self._registry.get(request.tool_name)

        if tool is None:
            return self._result(
                request,
                started,
                ExecutionStatus.TOOL_NOT_FOUND,
                error_code="tool_not_found",
                error_message=(
                    f"Tool not registered: "
                    f"{request.tool_name}"
                ),
            )

        validation_errors = validate_arguments(
            tool,
            request.arguments,
        )

        if validation_errors:
            return self._result(
                request,
                started,
                ExecutionStatus.INVALID_ARGUMENTS,
                tool=tool,
                error_code="invalid_arguments",
                error_message=(
                    "Tool arguments failed validation."
                ),
                validation_errors=validation_errors,
            )

        policy_result = self._apply_policy(
            request,
            tool,
            started,
        )

        if policy_result is not None:
            return policy_result

        executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="wilfred-tool",
        )

        future = executor.submit(
            tool.handler,
            **dict(request.arguments),
        )

        try:
            value = future.result(
                timeout=tool.timeout_seconds
            )
        except FutureTimeoutError:
            future.cancel()

            return self._result(
                request,
                started,
                ExecutionStatus.TIMEOUT,
                tool=tool,
                error_code="timeout",
                error_message=(
                    f"Tool exceeded timeout of "
                    f"{tool.timeout_seconds} seconds."
                ),
            )
        except Exception as exc:
            return self._result(
                request,
                started,
                ExecutionStatus.ERROR,
                tool=tool,
                error_code=type(exc).__name__,
                error_message=str(exc),
            )
        finally:
            executor.shutdown(
                wait=False,
                cancel_futures=True,
            )

        return self._result(
            request,
            started,
            ExecutionStatus.SUCCESS,
            tool=tool,
            value=value,
        )

    def _apply_policy(
        self,
        request: ExecutionRequest,
        tool: ToolDefinition,
        started: int,
    ) -> ExecutionResult | None:
        if tool.permission is ToolPermission.READ:
            return None

        if tool.permission is ToolPermission.ACTION:
            if (
                self._policy.require_action_confirmation
                and not request.confirmed
            ):
                return self._result(
                    request,
                    started,
                    ExecutionStatus.CONFIRMATION_REQUIRED,
                    tool=tool,
                    error_code="confirmation_required",
                    error_message=(
                        "ACTION tool requires confirmation."
                    ),
                )

            return None

        if not self._policy.allow_dangerous:
            return self._result(
                request,
                started,
                ExecutionStatus.DENIED,
                tool=tool,
                error_code="dangerous_denied",
                error_message=(
                    "DANGEROUS tools are disabled "
                    "by execution policy."
                ),
            )

        if (
            self._policy.require_dangerous_confirmation
            and not request.confirmed
        ):
            return self._result(
                request,
                started,
                ExecutionStatus.CONFIRMATION_REQUIRED,
                tool=tool,
                error_code="confirmation_required",
                error_message=(
                    "DANGEROUS tool requires confirmation."
                ),
            )

        return None

    @staticmethod
    def _result(
        request: ExecutionRequest,
        started: int,
        status: ExecutionStatus,
        *,
        tool: ToolDefinition | None = None,
        value: Any = None,
        error_code: str | None = None,
        error_message: str | None = None,
        validation_errors: tuple[str, ...] = (),
    ) -> ExecutionResult:
        duration_ms = (
            monotonic_ns() - started
        ) / 1_000_000

        return ExecutionResult(
            execution_id=request.execution_id,
            tool_name=request.tool_name,
            status=status,
            duration_ms=round(
                max(duration_ms, 0.0),
                3,
            ),
            permission=(
                tool.permission
                if tool is not None
                else None
            ),
            value=value,
            error_code=error_code,
            error_message=error_message,
            validation_errors=validation_errors,
        )
