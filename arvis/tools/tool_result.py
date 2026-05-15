# arvis/tools/tool_result.py

from dataclasses import dataclass
from typing import Any

from arvis.errors.base import ArvisError


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any | None = None
    error: ArvisError | None = None
    latency_ms: float | None = None
