# arvis/kernel_core/process/snapshot.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessSnapshot:
    process_id: str
    kind: str
    status: str
    priority: float
    created_tick: int

    user_id: str | None
    parent_process_id: str | None

    waiting_on: str | None
    run_count: int
    last_run_tick: int | None
    last_error: str | None

    current_stage_index: int
    stage_history: tuple[str, ...]
    total_stage_count: int | None
    pipeline_prepared: bool
    pipeline_finalized: bool

    consumed_reasoning_steps: int
    consumed_attention_tokens: int
    consumed_uncertainty: float
    consumed_elapsed_ms: int
    consumed_memory_span: int

    subscribed_interrupts: tuple[str, ...]
