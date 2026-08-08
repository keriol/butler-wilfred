from __future__ import annotations

import sqlite3

import pytest

from wilfred.execution import ExecutionRequest
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.persistence import (
    SQLiteWorkflowStore,
    WorkflowPersistenceError,
)
from wilfred.registry import ToolRegistry
from wilfred.workflows import (
    ReadActionVerifyRequest,
    ReadActionVerifyWorkflow,
    VerificationStatus,
)


def make_result(
    workflow_id: str,
    *,
    change_state: bool = True,
    action_value=None,
):
    state = {"power": "off"}
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="read_state",
            description="Read test state.",
            handler=lambda: dict(state),
            permission=ToolPermission.READ,
        )
    )

    def action():
        if change_state:
            state["power"] = "on"
        if action_value is not None:
            return action_value
        return {"accepted": True}

    registry.register(
        ToolDefinition(
            name="turn_on",
            description="Change test state.",
            handler=action,
            permission=ToolPermission.ACTION,
        )
    )

    request = ReadActionVerifyRequest(
        workflow_id=workflow_id,
        read_before=ExecutionRequest(
            tool_name="read_state",
        ),
        action=ExecutionRequest(
            tool_name="turn_on",
            confirmed=True,
        ),
        read_after=ExecutionRequest(
            tool_name="read_state",
        ),
        verifier=lambda _before, _action, after: (
            after["power"] == "on"
        ),
    )

    return ReadActionVerifyWorkflow(
        registry
    ).execute(request)


def test_file_round_trip_survives_reopen(tmp_path) -> None:
    database = tmp_path / "workflows.sqlite3"
    result = make_result("wf-round-trip")

    first = SQLiteWorkflowStore(database)
    saved = first.save(result)

    second = SQLiteWorkflowStore(database)
    loaded = second.get("wf-round-trip")

    assert loaded is not None
    assert loaded.persisted_at == saved.persisted_at
    assert loaded.result.workflow_id == result.workflow_id
    assert loaded.result.status is VerificationStatus.VERIFIED
    assert loaded.result.read_before is not None
    assert loaded.result.action is not None
    assert loaded.result.read_after is not None
    assert loaded.result.read_before.value == {"power": "off"}
    assert loaded.result.action.value == {"accepted": True}
    assert loaded.result.read_after.value == {"power": "on"}


def test_memory_store_survives_multiple_operations() -> None:
    store = SQLiteWorkflowStore(":memory:")
    result = make_result("wf-memory")

    store.save(result)
    loaded = store.get("wf-memory")

    assert loaded is not None
    assert loaded.result.status is VerificationStatus.VERIFIED
    assert len(store.list_recent()) == 1


def test_same_result_save_is_idempotent(tmp_path) -> None:
    store = SQLiteWorkflowStore(
        tmp_path / "workflows.sqlite3"
    )
    result = make_result("wf-idempotent")

    first = store.save(result)
    second = store.save(result)

    assert second.persisted_at == first.persisted_at
    assert len(store.list_recent()) == 1


def test_same_workflow_id_cannot_be_rewritten(tmp_path) -> None:
    store = SQLiteWorkflowStore(
        tmp_path / "workflows.sqlite3"
    )

    verified = make_result(
        "wf-collision",
        change_state=True,
    )
    failed = make_result(
        "wf-collision",
        change_state=False,
    )

    assert verified.status is VerificationStatus.VERIFIED
    assert failed.status is VerificationStatus.FAILED

    store.save(verified)

    with pytest.raises(
        WorkflowPersistenceError,
        match="different result",
    ):
        store.save(failed)


def test_list_recent_is_latest_first(tmp_path) -> None:
    store = SQLiteWorkflowStore(
        tmp_path / "workflows.sqlite3"
    )

    for workflow_id in ("wf-1", "wf-2", "wf-3"):
        store.save(make_result(workflow_id))

    recent = store.list_recent(limit=2)

    assert [x.workflow_id for x in recent] == [
        "wf-3",
        "wf-2",
    ]

    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        store.list_recent(limit=0)


def test_missing_result_returns_none(tmp_path) -> None:
    store = SQLiteWorkflowStore(
        tmp_path / "workflows.sqlite3"
    )

    assert store.get("does-not-exist") is None


def test_non_json_serializable_result_is_rejected(
    tmp_path,
) -> None:
    store = SQLiteWorkflowStore(
        tmp_path / "workflows.sqlite3"
    )
    result = make_result(
        "wf-not-json",
        action_value=object(),
    )

    with pytest.raises(
        WorkflowPersistenceError,
        match="not JSON serializable",
    ):
        store.save(result)

    assert store.get("wf-not-json") is None


def test_corrupt_stored_payload_is_rejected(tmp_path) -> None:
    database = tmp_path / "workflows.sqlite3"
    store = SQLiteWorkflowStore(database)
    store.save(make_result("wf-corrupt"))

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            UPDATE workflow_results
            SET payload_json = ?
            WHERE workflow_id = ?
            """,
            ("{broken-json", "wf-corrupt"),
        )

    with pytest.raises(
        WorkflowPersistenceError,
        match="Stored workflow result is invalid",
    ):
        store.get("wf-corrupt")
