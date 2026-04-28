# arvis/kernel_core/process/process_execution_state.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProcessExecutionState:
    current_stage_index: int = 0
    stage_history: list[str] = field(default_factory=list)
    total_stage_count: int | None = None

    pipeline_prepared: bool = False
    pipeline_finalized: bool = False
