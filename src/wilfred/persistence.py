from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Protocol
from uuid import uuid4

from wilfred.execution import (
    ExecutionResult,
    ExecutionStatus,
)
from wilfred.models import ToolPermission
from wilfred.workflows import (
    ReadActionVerifyResult,
    VerificationStatus,
)


class WorkflowPersistenceError(RuntimeError):
    """Raised when a workflow result cannot be persisted safely."""


@dataclass(frozen=True)
class WorkflowRecord:
    workflow_id: str
    persisted_at: str
    result: ReadActionVerifyResult


class WorkflowStore(Protocol):
    def save(
        self,
        result: ReadActionVerifyResult,
    ) -> WorkflowRecord:
        ...

    def get(
        self,
        workflow_id: str,
    ) -> WorkflowRecord | None:
        ...

    def list_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[WorkflowRecord, ...]:
        ...


class SQLiteWorkflowStore:
    def __init__(
        self,
        database: str | Path,
    ) -> None:
        requested = str(database)
        self._memory_anchor: sqlite3.Connection | None = None

        if requested == ":memory:":
            self._database = (
                f"file:wilfred-workflows-{uuid4().hex}"
                "?mode=memory&cache=shared"
            )
            self._use_uri = True
            self._memory_anchor = self._new_connection()
        else:
            self._database = requested
            self._use_uri = False

        self._initialize()

    def save(
        self,
        result: ReadActionVerifyResult,
    ) -> WorkflowRecord:
        payload = self._serialize(result)

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT persisted_at, payload_json
                FROM workflow_results
                WHERE workflow_id = ?
                """,
                (result.workflow_id,),
            ).fetchone()

            if existing is not None:
                if existing["payload_json"] != payload:
                    raise WorkflowPersistenceError(
                        "workflow_id already exists with "
                        "a different result."
                    )

                return WorkflowRecord(
                    workflow_id=result.workflow_id,
                    persisted_at=existing["persisted_at"],
                    result=result,
                )

            persisted_at = datetime.now(
                timezone.utc
            ).isoformat()

            connection.execute(
                """
                INSERT INTO workflow_results (
                    workflow_id,
                    status,
                    persisted_at,
                    payload_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    result.workflow_id,
                    result.status.value,
                    persisted_at,
                    payload,
                ),
            )

        return WorkflowRecord(
            workflow_id=result.workflow_id,
            persisted_at=persisted_at,
            result=result,
        )

    def get(
        self,
        workflow_id: str,
    ) -> WorkflowRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT workflow_id, persisted_at, payload_json
                FROM workflow_results
                WHERE workflow_id = ?
                """,
                (workflow_id,),
            ).fetchone()

        if row is None:
            return None

        return WorkflowRecord(
            workflow_id=row["workflow_id"],
            persisted_at=row["persisted_at"],
            result=self._deserialize(row["payload_json"]),
        )

    def list_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[WorkflowRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be at least 1.")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT workflow_id, persisted_at, payload_json
                FROM workflow_results
                ORDER BY persisted_at DESC, rowid DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return tuple(
            WorkflowRecord(
                workflow_id=row["workflow_id"],
                persisted_at=row["persisted_at"],
                result=self._deserialize(
                    row["payload_json"]
                ),
            )
            for row in rows
        )

    def _initialize(self) -> None:
        if not self._use_uri:
            Path(self._database).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_results (
                    workflow_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    persisted_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_workflow_results_persisted_at
                ON workflow_results (persisted_at DESC)
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = self._new_connection()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _new_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database,
            uri=self._use_uri,
        )
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _serialize(
        result: ReadActionVerifyResult,
    ) -> str:
        try:
            return json.dumps(
                result.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise WorkflowPersistenceError(
                "Workflow result is not JSON serializable."
            ) from exc

    @staticmethod
    def _deserialize(
        payload: str,
    ) -> ReadActionVerifyResult:
        try:
            data = json.loads(payload)
            error = data.get("error")

            return ReadActionVerifyResult(
                workflow_id=data["workflow_id"],
                status=VerificationStatus(
                    data["status"]
                ),
                duration_ms=float(data["duration_ms"]),
                read_before=_execution_result(
                    data.get("read_before")
                ),
                action=_execution_result(
                    data.get("action")
                ),
                read_after=_execution_result(
                    data.get("read_after")
                ),
                error_code=(
                    error.get("code")
                    if error is not None
                    else None
                ),
                error_message=(
                    error.get("message")
                    if error is not None
                    else None
                ),
            )
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise WorkflowPersistenceError(
                "Stored workflow result is invalid."
            ) from exc


def _execution_result(
    data: dict | None,
) -> ExecutionResult | None:
    if data is None:
        return None

    error = data.get("error")
    permission = data.get("permission")

    return ExecutionResult(
        execution_id=data["execution_id"],
        tool_name=data["tool_name"],
        status=ExecutionStatus(data["status"]),
        duration_ms=float(data["duration_ms"]),
        permission=(
            ToolPermission(permission)
            if permission is not None
            else None
        ),
        value=data.get("value"),
        error_code=(
            error.get("code")
            if error is not None
            else None
        ),
        error_message=(
            error.get("message")
            if error is not None
            else None
        ),
        validation_errors=tuple(
            data.get("validation_errors", ())
        ),
    )
