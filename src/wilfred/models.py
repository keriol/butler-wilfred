from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ToolPermission(str, Enum):
    READ = "READ"
    ACTION = "ACTION"
    DANGEROUS = "DANGEROUS"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., Any]
    parameters: dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    permission: ToolPermission = ToolPermission.READ
    timeout_seconds: int = 10
