# arvis/kernel/pipeline/context/runtime_bindings_context.py

from dataclasses import dataclass
from typing import Any

from arvis.cognition.control.cognitive_control_runtime import (
    CognitiveControlRuntime,
)


@dataclass
class PipelineRuntimeBindingsContext:
    runtime: Any | None = None
    syscall_handler: Any | None = None
    process_id: str | None = None
    adapters: dict[str, Any] | None = None
    control_runtime: CognitiveControlRuntime | None = None
