from __future__ import annotations

from butler_core import (
    OutputAdapter as CoreOutputAdapter,
    OutputDeliveryResult as CoreOutputDeliveryResult,
    OutputDeliveryStatus as CoreOutputDeliveryStatus,
    OutputKind as CoreOutputKind,
    OutputPriority as CoreOutputPriority,
    OutputRequest as CoreOutputRequest,
)

from wilfred import (
    OutputAdapter,
    OutputCapability,
    OutputDeliveryResult,
    OutputDeliveryStatus,
    OutputKind,
    OutputPriority,
    OutputRequest,
)


class FakeSpeechAdapter:
    def __init__(
        self,
        status: OutputDeliveryStatus = OutputDeliveryStatus.DELIVERED,
    ) -> None:
        self.status = status
        self.requests: list[OutputRequest] = []

    @property
    def supported_kinds(self) -> frozenset[OutputKind]:
        return frozenset({OutputKind.SPEECH})

    def deliver(
        self,
        request: OutputRequest,
    ) -> OutputDeliveryResult:
        self.requests.append(request)

        if request.kind not in self.supported_kinds:
            return OutputDeliveryResult(
                status=OutputDeliveryStatus.UNSUPPORTED,
                error_code="unsupported_kind",
            )

        return OutputDeliveryResult(
            status=self.status,
        )


def test_output_contracts_are_butler_core_contracts() -> None:
    assert OutputAdapter is CoreOutputAdapter
    assert OutputDeliveryResult is CoreOutputDeliveryResult
    assert OutputDeliveryStatus is CoreOutputDeliveryStatus
    assert OutputKind is CoreOutputKind
    assert OutputPriority is CoreOutputPriority
    assert OutputRequest is CoreOutputRequest


def test_output_capability_is_pre_020_compatibility_alias() -> None:
    assert OutputCapability is OutputKind
    assert OutputCapability.SPEECH is OutputKind.SPEECH


def test_request_uses_core_delivery_context() -> None:
    request = OutputRequest(
        content="Laundry completed.",
        kind=OutputKind.SPEECH,
        target="kitchen",
        correlation_id="job-42",
    )

    assert request.priority is OutputPriority.NORMAL
    assert request.target == "kitchen"
    assert request.correlation_id == "job-42"


def test_adapter_uses_supported_kinds() -> None:
    adapter: OutputAdapter = FakeSpeechAdapter()

    request = OutputRequest(
        content="Laundry completed.",
        kind=OutputKind.SPEECH,
    )

    result = adapter.deliver(request)

    assert result.status is OutputDeliveryStatus.DELIVERED
    assert result.accepted is True
    assert result.delivered is True
    assert result.ok is True
    assert adapter.requests == [request]


def test_accepted_is_not_claimed_as_delivered() -> None:
    adapter: OutputAdapter = FakeSpeechAdapter(
        status=OutputDeliveryStatus.ACCEPTED,
    )

    result = adapter.deliver(
        OutputRequest(
            content="Queued.",
            kind=OutputKind.SPEECH,
        )
    )

    assert result.accepted is True
    assert result.delivered is False
    assert result.ok is True


def test_unsupported_and_failed_are_not_ok() -> None:
    adapter: OutputAdapter = FakeSpeechAdapter()

    unsupported = adapter.deliver(
        OutputRequest(
            content="Show status.",
            kind=OutputKind.DISPLAY,
        )
    )

    failed = OutputDeliveryResult(
        status=OutputDeliveryStatus.FAILED,
        error_code="delivery_failed",
    )

    assert unsupported.status is OutputDeliveryStatus.UNSUPPORTED
    assert unsupported.ok is False
    assert failed.ok is False


def test_priority_uses_core_urgent_name() -> None:
    assert OutputPriority.URGENT.value == "urgent"
