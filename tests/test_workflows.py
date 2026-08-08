from __future__ import annotations

from wilfred.execution import (
    ExecutionRequest,
    ExecutionStatus,
)
from wilfred.models import (
    ToolDefinition,
    ToolPermission,
)
from wilfred.registry import ToolRegistry
from wilfred.workflows import (
    ReadActionVerifyRequest,
    ReadActionVerifyWorkflow,
    VerificationStatus,
)


def register(
    registry: ToolRegistry,
    name: str,
    handler,
    permission: ToolPermission,
) -> None:
    registry.register(
        ToolDefinition(
            name=name,
            description=f"Test tool: {name}",
            handler=handler,
            permission=permission,
        )
    )


def request() -> ReadActionVerifyRequest:
    return ReadActionVerifyRequest(
        read_before=ExecutionRequest(
            tool_name="read_state",
        ),
        action=ExecutionRequest(
            tool_name="action",
            confirmed=True,
        ),
        read_after=ExecutionRequest(
            tool_name="read_state",
        ),
        verifier=lambda before, _action, after: (
            before["power"] == "off"
            and after["power"] == "on"
        ),
    )


def test_verified_after_real_state_change() -> None:
    state = {"power": "off"}
    registry = ToolRegistry()

    register(
        registry,
        "read_state",
        lambda: dict(state),
        ToolPermission.READ,
    )

    def turn_on():
        state["power"] = "on"
        return {"accepted": True}

    register(
        registry,
        "action",
        turn_on,
        ToolPermission.ACTION,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(request())

    assert result.ok
    assert result.status is VerificationStatus.VERIFIED
    assert result.action is not None
    assert result.action.ok
    assert result.read_after is not None
    assert result.read_after.value["power"] == "on"


def test_dispatch_success_is_not_verification() -> None:
    state = {"power": "off"}
    registry = ToolRegistry()

    register(
        registry,
        "read_state",
        lambda: dict(state),
        ToolPermission.READ,
    )

    register(
        registry,
        "action",
        lambda: {"accepted": True},
        ToolPermission.ACTION,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(request())

    assert not result.ok
    assert result.status is VerificationStatus.FAILED
    assert result.action is not None
    assert result.action.ok
    assert result.error_code == "verification_failed"


def test_failed_initial_read_prevents_action() -> None:
    calls = {"action": 0}
    registry = ToolRegistry()

    def broken_read():
        raise RuntimeError("sensor unavailable")

    def action():
        calls["action"] += 1

    register(
        registry,
        "read_state",
        broken_read,
        ToolPermission.READ,
    )
    register(
        registry,
        "action",
        action,
        ToolPermission.ACTION,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(request())

    assert result.status is VerificationStatus.INDETERMINATE
    assert result.error_code == "read_before_failed"
    assert result.action is None
    assert calls["action"] == 0


def test_failed_action_prevents_post_read() -> None:
    reads = {"count": 0}
    registry = ToolRegistry()

    def read_state():
        reads["count"] += 1
        return {"power": "off"}

    def broken_action():
        raise RuntimeError("dispatch failed")

    register(
        registry,
        "read_state",
        read_state,
        ToolPermission.READ,
    )
    register(
        registry,
        "action",
        broken_action,
        ToolPermission.ACTION,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(request())

    assert result.status is VerificationStatus.FAILED
    assert result.error_code == "action_failed"
    assert result.action is not None
    assert result.action.status is ExecutionStatus.ERROR
    assert result.read_after is None
    assert reads["count"] == 1


def test_failed_post_read_is_indeterminate() -> None:
    reads = {"count": 0}
    registry = ToolRegistry()

    def read_state():
        reads["count"] += 1
        if reads["count"] == 2:
            raise RuntimeError("sensor unavailable")
        return {"power": "off"}

    register(
        registry,
        "read_state",
        read_state,
        ToolPermission.READ,
    )
    register(
        registry,
        "action",
        lambda: {"accepted": True},
        ToolPermission.ACTION,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(request())

    assert result.status is VerificationStatus.INDETERMINATE
    assert result.error_code == "read_after_failed"
    assert result.action is not None
    assert result.action.ok
    assert result.read_after is not None
    assert result.read_after.status is ExecutionStatus.ERROR


def test_action_tool_cannot_be_used_as_read() -> None:
    calls = {"bad_read": 0}
    registry = ToolRegistry()

    def bad_read():
        calls["bad_read"] += 1
        return {"power": "off"}

    register(
        registry,
        "read_state",
        bad_read,
        ToolPermission.ACTION,
    )
    register(
        registry,
        "action",
        lambda: None,
        ToolPermission.ACTION,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(request())

    assert result.status is VerificationStatus.FAILED
    assert result.error_code == "invalid_read_tool"
    assert calls["bad_read"] == 0


def test_verifier_can_report_indeterminate() -> None:
    registry = ToolRegistry()

    register(
        registry,
        "read_state",
        lambda: {"power": "off"},
        ToolPermission.READ,
    )
    register(
        registry,
        "action",
        lambda: {"accepted": True},
        ToolPermission.ACTION,
    )

    workflow_request = request()
    workflow_request = ReadActionVerifyRequest(
        read_before=workflow_request.read_before,
        action=workflow_request.action,
        read_after=workflow_request.read_after,
        verifier=lambda *_: None,
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(workflow_request)

    assert result.status is VerificationStatus.INDETERMINATE
    assert result.error_code == "verification_indeterminate"


def test_invalid_verifier_result_is_indeterminate() -> None:
    registry = ToolRegistry()

    register(
        registry,
        "read_state",
        lambda: {"power": "off"},
        ToolPermission.READ,
    )
    register(
        registry,
        "action",
        lambda: {"accepted": True},
        ToolPermission.ACTION,
    )

    workflow_request = request()
    workflow_request = ReadActionVerifyRequest(
        read_before=workflow_request.read_before,
        action=workflow_request.action,
        read_after=workflow_request.read_after,
        verifier=lambda *_: "yes",
    )

    result = ReadActionVerifyWorkflow(
        registry
    ).execute(workflow_request)

    assert result.status is VerificationStatus.INDETERMINATE
    assert result.error_code == "invalid_verifier_result"
