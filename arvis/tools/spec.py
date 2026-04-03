# arvis/tools/spec.py

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str

    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)

    idempotent: bool = False
    retryable: bool = True
    side_effectful: bool = True
    timeout_seconds: Optional[float] = None