"""Compatibility facade for shared Butler Core output contracts."""

from butler_core import (
    OutputAdapter,
    OutputDeliveryResult,
    OutputDeliveryStatus,
    OutputKind,
    OutputPriority,
    OutputRequest,
)


# Pre-0.2 compatibility name. Capabilities are now represented directly
# by Butler Core OutputKind values.
OutputCapability = OutputKind


__all__ = [
    "OutputAdapter",
    "OutputCapability",
    "OutputDeliveryResult",
    "OutputDeliveryStatus",
    "OutputKind",
    "OutputPriority",
    "OutputRequest",
]
