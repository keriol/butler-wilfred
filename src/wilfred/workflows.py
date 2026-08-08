from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic_ns
from typing import Any
from uuid import uuid4

from wilfred.execution import (
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
)
from wilfred.models import ToolPermission
from wilfred.registry import ToolRegistry


Verifier = Callable[[Any, Any, Any], bool | None]


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class ReadActionVerifyRequest:
    read_before: ExecutionRequest
    action: ExecutionRequest
    read_after: ExecutionRequest
    verifier: Verifier
    workflow_id: str = field(
        default_factory=lambda: str(uuid4())
    )


@dataclass(frozen=True)
class ReadActionVerifyResult:
    workflow_id: str
    status: VerificationStatus
    duration_ms: float
    read_before: ExecutionResult | None = None
    action: ExecutionResult | None = None
    read_after: ExecutionResult | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is VerificationStatus.VERIFIED

    def to_dict(self) -> dict[str, Any]:
        error = None
        if self.error_code is not None:
            error = {
                "code": self.error_code,
                "message": self.error_message,
            }

        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "read_before": (
                self.read_before.to_dict()
                if self.read_before is not None
                else None
            ),
            "action": (
                self.action.to_dict()
                if self.action is not None
                else None
            ),
            "read_after": (
                self.read_after.to_dict()
                if self.read_after is not None
                else None
            ),
            "error": error,
        }


class ReadActionVerifyWorkflow:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        policy: ExecutionPolicy | None = None,
    ) -> None:
        self._registry = registry
        self._engine = ExecutionEngine(
            registry,
            policy=policy,
        )

    def execute(
        self,
        request: ReadActionVerifyRequest,
    ) -> ReadActionVerifyResult:
        started = monotonic_ns()

        error = self._validate_contract(request)
        if error is not None:
            return self._result(
                request,
                started,
                VerificationStatus.FAILED,
                error_code=error[0],
                error_message=error[1],
            )

        before = self._engine.execute(request.read_before)
        if not before.ok:
            return self._result(
                request,
                started,
                VerificationStatus.INDETERMINATE,
                read_before=before,
                error_code="read_before_failed",
                error_message="Initial READ failed.",
            )

        action = self._engine.execute(request.action)
        if not action.ok:
            return self._result(
                request,
                started,
                VerificationStatus.FAILED,
                read_before=before,
                action=action,
                error_code="action_failed",
                error_message="ACTION did not complete.",
            )

        after = self._engine.execute(request.read_after)
        if not after.ok:
            return self._result(
                request,
                started,
                VerificationStatus.INDETERMINATE,
                read_before=before,
                action=action,
                read_after=after,
                error_code="read_after_failed",
                error_message="Post-action READ failed.",
            )

        try:
            decision = request.verifier(
                before.value,
                action.value,
                after.value,
            )
        except Exception as exc:
            return self._result(
                request,
                started,
                VerificationStatus.INDETERMINATE,
                read_before=before,
                action=action,
                read_after=after,
                error_code="verification_error",
                error_message=f"{type(exc).__name__}: {exc}",
            )

        if decision is True:
            status = VerificationStatus.VERIFIED
            code = None
            message = None
        elif decision is False:
            status = VerificationStatus.FAILED
            code = "verification_failed"
            message = "Observed state did not satisfy verifier."
        elif decision is None:
            status = VerificationStatus.INDETERMINATE
            code = "verification_indeterminate"
            message = "Verifier could not determine outcome."
        else:
            status = VerificationStatus.INDETERMINATE
            code = "invalid_verifier_result"
            message = "Verifier must return True, False or None."

        return self._result(
            request,
            started,
            status,
            read_before=before,
            action=action,
            read_after=after,
            error_code=code,
            error_message=message,
        )

    def _validate_contract(
        self,
        request: ReadActionVerifyRequest,
    ) -> tuple[str, str] | None:
        for name, step in (
            ("read_before", request.read_before),
            ("read_after", request.read_after),
        ):
            tool = self._registry.get(step.tool_name)
            if tool is None:
                return (
                    "tool_not_found",
                    f"{name} tool not registered: {step.tool_name}",
                )

            if tool.permission is not ToolPermission.READ:
                return (
                    "invalid_read_tool",
                    f"{name} must use a READ tool.",
                )

        tool = self._registry.get(request.action.tool_name)
        if tool is None:
            return (
                "tool_not_found",
                (
                    "action tool not registered: "
                    f"{request.action.tool_name}"
                ),
            )

        if tool.permission not in {
            ToolPermission.ACTION,
            ToolPermission.DANGEROUS,
        }:
            return (
                "invalid_action_tool",
                "action must use ACTION or DANGEROUS tool.",
            )

        return None

    @staticmethod
    def _result(
        request: ReadActionVerifyRequest,
        started: int,
        status: VerificationStatus,
        *,
        read_before: ExecutionResult | None = None,
        action: ExecutionResult | None = None,
        read_after: ExecutionResult | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ReadActionVerifyResult:
        elapsed = (monotonic_ns() - started) / 1_000_000

        return ReadActionVerifyResult(
            workflow_id=request.workflow_id,
            status=status,
            duration_ms=round(max(elapsed, 0.0), 3),
            read_before=read_before,
            action=action,
            read_after=read_after,
            error_code=error_code,
            error_message=error_message,
        )
