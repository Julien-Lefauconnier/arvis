# arvis/tools/tool_result.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any | None = None
    error: str | None = None
    latency_ms: float | None = None
