from datetime import datetime, timedelta, timezone

import pytest

from wilfred.pending_actions import (
    InMemoryPendingActionStore,
    InvalidPendingActionTransition,
    JsonPendingActionStore,
    PendingActionStatus,
    PendingActionWorkflow,
)


class Clock:
    def __init__(self):
        self.value = datetime(
            2026, 8, 15, 12, 0,
            tzinfo=timezone.utc,
        )

    def __call__(self):
        return self.value

    def advance(self, **kwargs):
        self.value += timedelta(**kwargs)


def workflow(clock):
    ids = iter(("a1", "a2", "a3"))

    return PendingActionWorkflow(
        InMemoryPendingActionStore(),
        clock=clock,
        id_factory=lambda: next(ids),
    )


def test_create_and_get_next_are_deterministic():
    clock = Clock()
    pending = workflow(clock)

    first = pending.create(
        "first",
        data={"value": 1},
    )

    clock.advance(seconds=1)
    pending.create("second")

    assert first.status is PendingActionStatus.PENDING
    assert pending.get_next().id == "a1"

    assert [
        item.id
        for item in pending.list_pending()
    ] == ["a1", "a2"]


def test_snoozed_action_resumes_when_ready():
    clock = Clock()
    pending = workflow(clock)

    action = pending.create("reminder")

    pending.snooze(
        action.id,
        until=clock.value + timedelta(minutes=30),
    )

    assert pending.get_next() is None

    clock.advance(minutes=31)

    resumed = pending.get(action.id)

    assert resumed.status is PendingActionStatus.PENDING
    assert resumed.snooze_until is None


def test_expiration_is_explicit_terminal_state():
    clock = Clock()
    pending = workflow(clock)

    action = pending.create(
        "temporary",
        expires_at=(
            clock.value + timedelta(minutes=5)
        ),
    )

    clock.advance(minutes=6)

    expired = pending.get(action.id)

    assert expired.status is PendingActionStatus.EXPIRED
    assert expired.is_terminal
    assert pending.get_next() is None


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        ("complete", PendingActionStatus.DONE),
        ("dismiss", PendingActionStatus.DISMISSED),
        ("fail", PendingActionStatus.FAILED),
    ],
)
def test_terminal_transitions(operation, expected):
    clock = Clock()
    pending = workflow(clock)

    action = pending.create("operation")

    terminal = getattr(
        pending,
        operation,
    )(action.id)

    assert terminal.status is expected
    assert terminal.is_terminal

    with pytest.raises(
        InvalidPendingActionTransition
    ):
        pending.complete(action.id)


def test_json_store_round_trip(tmp_path):
    clock = Clock()
    path = tmp_path / "pending-actions.json"

    pending = PendingActionWorkflow(
        JsonPendingActionStore(path),
        clock=clock,
        id_factory=lambda: "persistent",
    )

    created = pending.create(
        "persistent",
        data={"number": 7},
        expires_at=(
            clock.value + timedelta(hours=2)
        ),
    )

    reloaded = PendingActionWorkflow(
        JsonPendingActionStore(path),
        clock=clock,
    ).get(created.id)

    assert reloaded == created


def test_snooze_must_precede_expiration():
    clock = Clock()
    pending = workflow(clock)

    action = pending.create(
        "expiring",
        expires_at=(
            clock.value + timedelta(minutes=30)
        ),
    )

    with pytest.raises(ValueError):
        pending.snooze(
            action.id,
            until=(
                clock.value
                + timedelta(minutes=30)
            ),
        )


def test_datetime_inputs_must_be_timezone_aware():
    clock = Clock()
    pending = workflow(clock)

    with pytest.raises(ValueError):
        pending.create(
            "invalid",
            expires_at=datetime(
                2026, 8, 16, 12, 0
            ),
        )
