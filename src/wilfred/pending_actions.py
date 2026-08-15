from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4


class PendingActionError(RuntimeError):
    """Base error for pending-action lifecycle operations."""


class PendingActionNotFound(PendingActionError):
    """Raised when a pending action cannot be found."""


class InvalidPendingActionTransition(PendingActionError):
    """Raised when a lifecycle transition is not valid."""


class PendingActionStatus(str, Enum):
    PENDING = "pending"
    SNOOZED = "snoozed"
    DONE = "done"
    DISMISSED = "dismissed"
    EXPIRED = "expired"
    FAILED = "failed"


_ACTIVE_STATUSES = {
    PendingActionStatus.PENDING,
    PendingActionStatus.SNOOZED,
}

_TERMINAL_STATUSES = {
    PendingActionStatus.DONE,
    PendingActionStatus.DISMISSED,
    PendingActionStatus.EXPIRED,
    PendingActionStatus.FAILED,
}


@dataclass(frozen=True, slots=True)
class PendingAction:
    id: str
    action_type: str
    status: PendingActionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    snooze_until: datetime | None = None
    data: dict[str, Any] | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATUSES


class PendingActionStore(Protocol):
    """Persistence boundary for reusable pending actions."""

    def add(self, action: PendingAction) -> PendingAction:
        ...

    def get(self, action_id: str) -> PendingAction | None:
        ...

    def list(self) -> list[PendingAction]:
        ...

    def update(self, action: PendingAction) -> PendingAction:
        ...


class InMemoryPendingActionStore:
    """Simple store useful for embedded runtimes and tests."""

    def __init__(self) -> None:
        self._actions: dict[str, PendingAction] = {}

    def add(self, action: PendingAction) -> PendingAction:
        if action.id in self._actions:
            raise PendingActionError(
                f"Pending action already exists: {action.id}"
            )

        self._actions[action.id] = action
        return action

    def get(self, action_id: str) -> PendingAction | None:
        return self._actions.get(action_id)

    def list(self) -> list[PendingAction]:
        return list(self._actions.values())

    def update(self, action: PendingAction) -> PendingAction:
        if action.id not in self._actions:
            raise PendingActionNotFound(action.id)

        self._actions[action.id] = action
        return action


class JsonPendingActionStore:
    """JSON-backed pending-action store with atomic replacement."""

    _FORMAT_VERSION = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, action: PendingAction) -> PendingAction:
        actions = self._load()

        if action.id in actions:
            raise PendingActionError(
                f"Pending action already exists: {action.id}"
            )

        actions[action.id] = action
        self._save(actions)
        return action

    def get(self, action_id: str) -> PendingAction | None:
        return self._load().get(action_id)

    def list(self) -> list[PendingAction]:
        return list(self._load().values())

    def update(self, action: PendingAction) -> PendingAction:
        actions = self._load()

        if action.id not in actions:
            raise PendingActionNotFound(action.id)

        actions[action.id] = action
        self._save(actions)
        return action

    def _load(self) -> dict[str, PendingAction]:
        if not self.path.exists():
            return {}

        payload = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        if payload.get("version") != self._FORMAT_VERSION:
            raise PendingActionError(
                "Unsupported pending-action store format"
            )

        actions: dict[str, PendingAction] = {}

        for raw in payload.get("actions", []):
            action = PendingAction(
                id=raw["id"],
                action_type=raw["action_type"],
                status=PendingActionStatus(raw["status"]),
                created_at=_parse_datetime(
                    raw["created_at"]
                ),
                updated_at=_parse_datetime(
                    raw["updated_at"]
                ),
                expires_at=_parse_optional_datetime(
                    raw.get("expires_at")
                ),
                snooze_until=_parse_optional_datetime(
                    raw.get("snooze_until")
                ),
                data=dict(raw.get("data") or {}),
            )

            actions[action.id] = action

        return actions

    def _save(
        self,
        actions: dict[str, PendingAction],
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": self._FORMAT_VERSION,
            "actions": [
                _serialize_action(action)
                for action in sorted(
                    actions.values(),
                    key=lambda item: (
                        item.created_at,
                        item.id,
                    ),
                )
            ],
        }

        text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"

        fd, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            text=True,
        )

        temporary_path = Path(temporary_name)

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(text)

            os.replace(
                temporary_path,
                self.path,
            )
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError(
            "datetime values must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    return _as_utc(
        datetime.fromisoformat(value)
    )


def _parse_optional_datetime(
    value: str | None,
) -> datetime | None:
    if value is None:
        return None

    return _parse_datetime(value)


def _serialize_action(
    action: PendingAction,
) -> dict[str, Any]:
    payload = asdict(action)

    payload["status"] = action.status.value
    payload["created_at"] = action.created_at.isoformat()
    payload["updated_at"] = action.updated_at.isoformat()

    payload["expires_at"] = (
        action.expires_at.isoformat()
        if action.expires_at is not None
        else None
    )

    payload["snooze_until"] = (
        action.snooze_until.isoformat()
        if action.snooze_until is not None
        else None
    )

    return payload


class PendingActionWorkflow:
    """Provider-neutral lifecycle for deferred Butler actions."""

    def __init__(
        self,
        store: PendingActionStore,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.store = store
        self._clock = clock or _utc_now
        self._id_factory = id_factory or (
            lambda: str(uuid4())
        )

    def create(
        self,
        action_type: str,
        *,
        data: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> PendingAction:
        action_type = action_type.strip()

        if not action_type:
            raise ValueError(
                "action_type must not be empty"
            )

        now = self._now()

        normalized_expiration = (
            _as_utc(expires_at)
            if expires_at is not None
            else None
        )

        if (
            normalized_expiration is not None
            and normalized_expiration <= now
        ):
            raise ValueError(
                "expires_at must be in the future"
            )

        action = PendingAction(
            id=self._id_factory(),
            action_type=action_type,
            status=PendingActionStatus.PENDING,
            created_at=now,
            updated_at=now,
            expires_at=normalized_expiration,
            data=dict(data or {}),
        )

        return self.store.add(action)

    def get(
        self,
        action_id: str,
    ) -> PendingAction:
        action = self.store.get(action_id)

        if action is None:
            raise PendingActionNotFound(action_id)

        return self._normalize(action)

    def list_pending(
        self,
    ) -> list[PendingAction]:
        actions = [
            self._normalize(action)
            for action in self.store.list()
        ]

        return sorted(
            (
                action
                for action in actions
                if action.status in _ACTIVE_STATUSES
            ),
            key=lambda action: (
                action.created_at,
                action.id,
            ),
        )

    def get_next(
        self,
    ) -> PendingAction | None:
        available = [
            action
            for action in self.list_pending()
            if action.status
            is PendingActionStatus.PENDING
        ]

        if not available:
            return None

        return available[0]

    def snooze(
        self,
        action_id: str,
        *,
        until: datetime,
    ) -> PendingAction:
        action = self.get(action_id)
        self._require_active(action)

        now = self._now()
        normalized_until = _as_utc(until)

        if normalized_until <= now:
            raise ValueError(
                "snooze deadline must be in the future"
            )

        if (
            action.expires_at is not None
            and normalized_until >= action.expires_at
        ):
            raise ValueError(
                "snooze deadline must precede expiration"
            )

        return self.store.update(
            replace(
                action,
                status=PendingActionStatus.SNOOZED,
                snooze_until=normalized_until,
                updated_at=now,
            )
        )

    def complete(
        self,
        action_id: str,
    ) -> PendingAction:
        return self._finish(
            action_id,
            PendingActionStatus.DONE,
        )

    def dismiss(
        self,
        action_id: str,
    ) -> PendingAction:
        return self._finish(
            action_id,
            PendingActionStatus.DISMISSED,
        )

    def fail(
        self,
        action_id: str,
    ) -> PendingAction:
        return self._finish(
            action_id,
            PendingActionStatus.FAILED,
        )

    def _finish(
        self,
        action_id: str,
        status: PendingActionStatus,
    ) -> PendingAction:
        action = self.get(action_id)
        self._require_active(action)

        return self.store.update(
            replace(
                action,
                status=status,
                snooze_until=None,
                updated_at=self._now(),
            )
        )

    def _normalize(
        self,
        action: PendingAction,
    ) -> PendingAction:
        if action.is_terminal:
            return action

        now = self._now()

        if (
            action.expires_at is not None
            and action.expires_at <= now
        ):
            return self.store.update(
                replace(
                    action,
                    status=PendingActionStatus.EXPIRED,
                    snooze_until=None,
                    updated_at=now,
                )
            )

        if (
            action.status
            is PendingActionStatus.SNOOZED
            and action.snooze_until is not None
            and action.snooze_until <= now
        ):
            return self.store.update(
                replace(
                    action,
                    status=PendingActionStatus.PENDING,
                    snooze_until=None,
                    updated_at=now,
                )
            )

        return action

    @staticmethod
    def _require_active(
        action: PendingAction,
    ) -> None:
        if action.status not in _ACTIVE_STATUSES:
            raise InvalidPendingActionTransition(
                f"Action {action.id} is "
                f"{action.status.value}"
            )

    def _now(self) -> datetime:
        return _as_utc(self._clock())
