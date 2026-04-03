# arvis/tools/tool_result.py

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None