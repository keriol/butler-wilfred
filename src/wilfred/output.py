from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable
from uuid import uuid4


class OutputKind(str, Enum):
    SPEECH = "speech"
    NOTIFICATION = "notification"
    SOUND = "sound"
    DISPLAY = "display"


class OutputCapability(str, Enum):
    SPEECH = "speech"
    NOTIFICATION = "notification"
    SOUND = "sound"
    DISPLAY = "display"


class OutputPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class OutputDeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(frozen=True)
class OutputRequest:
    content: str
    kind: OutputKind
    target: str | None = None
    priority: OutputPriority = OutputPriority.NORMAL
    locale: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @property
    def required_capability(self) -> OutputCapability:
        return OutputCapability(self.kind.value)


@dataclass(frozen=True)
class OutputDeliveryResult:
    request_id: str
    adapter_name: str
    status: OutputDeliveryStatus
    provider_reference: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status is OutputDeliveryStatus.DELIVERED


@runtime_checkable
class OutputAdapter(Protocol):
    @property
    def name(self) -> str:
        ...

    def capabilities(
        self,
    ) -> frozenset[OutputCapability]:
        ...

    def deliver(
        self,
        request: OutputRequest,
    ) -> OutputDeliveryResult:
        ...
