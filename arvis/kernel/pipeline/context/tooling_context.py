# arvis/kernel/pipeline/context/tooling_context.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineToolingContext:
    tool_success: bool | None = None
    tool_failure: bool | None = None
    last_tool_spec: Any | None = None

    retry_requested: bool = False
    retry_count: int = 0

    force_tool: str | None = None
    force_execution: bool = False

    tool_feedback: dict[str, Any] | None = None

    tool_results: list[Any] = field(default_factory=list)
    tool_payloads: list[dict[str, Any]] = field(default_factory=list)
