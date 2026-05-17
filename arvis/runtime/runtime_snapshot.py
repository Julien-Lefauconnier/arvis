# arvis/runtime/runtime_snapshot.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel_core.process.snapshot import ProcessSnapshot


@dataclass(frozen=True)
class RuntimeSnapshot:
    tick_count: int
    active_process_id: str | None

    ready_queue: tuple[str, ...]
    blocked_queue: tuple[str, ...]
    suspended_queue: tuple[str, ...]
    waiting_confirmation_queue: tuple[str, ...]
    completed_queue: tuple[str, ...]
    aborted_queue: tuple[str, ...]

    processes: tuple[ProcessSnapshot, ...]

    timeline_commitment: str
