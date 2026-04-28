# arvis/kernel_core/process/process_runtime_state.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.kernel_core.process.types import CognitiveProcessStatus


@dataclass
class ProcessRuntimeState:
    status: CognitiveProcessStatus
    waiting_on: str | None = None

    last_result: Any = None
    last_error: str | None = None
    last_score: float | None = None

    run_count: int = 0
    last_run_tick: int | None = None

    consumed_reasoning_steps: int = 0
    consumed_attention_tokens: int = 0
    consumed_uncertainty: float = 0.0
    consumed_elapsed_ms: int = 0
    consumed_memory_span: int = 0
