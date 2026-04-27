# arvis/runtime/cognitive_runtime_state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from arvis.runtime.resource_model import ResourceState
from arvis.kernel_core.process import CognitiveProcess, CognitiveProcessId
from arvis.kernel_core.state.scheduler_state import SchedulerState
from arvis.kernel_core.interrupts.interrupt_bus import CognitiveInterruptBus
from arvis.signals.signal_journal import SignalJournal
from arvis.api.signals import CanonicalSignal
from arvis.adapters.kernel.signals.signal_factory import SignalFactory
from arvis.adapters.kernel.timeline_from_signals import (
    signal_journal_to_timeline_snapshot,
)
from arvis.timeline.timeline_commitment import (
    TimelineCommitment,
)

@dataclass
class CognitiveRuntimeState:
    scheduler_state: SchedulerState = field(default_factory=SchedulerState)
    resource_state: ResourceState = field(default_factory=ResourceState)
    processes: dict[CognitiveProcessId, CognitiveProcess] = field(default_factory=dict)
    memory_topology: Optional[Any] = None
    control_state: Optional[Any] = None
    timeline: Any = field(default_factory=SignalJournal)
    _local_counter: int = 0
    _last_tick: int = -1
    _last_ts_local: float = 0.0
    interrupt_bus: CognitiveInterruptBus = field(default_factory=CognitiveInterruptBus)
    

    def register_process(self, process: CognitiveProcess) -> None:
        process.validate()
        if process.process_id in self.processes:
            raise ValueError(f"Duplicate process id: {process.process_id.value}")
        self.processes[process.process_id] = process
        self.resource_state.note_process_seen()

    def get_process(self, process_id: CognitiveProcessId) -> CognitiveProcess:
        try:
            return self.processes[process_id]
        except KeyError as exc:
            raise KeyError(f"Unknown process id: {process_id.value}") from exc
    

    def append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        signal = self._map_runtime_event(event_type, payload)
        self.timeline.append(signal)

    # -----------------------------------------------------
    # Runtime → Canonical Signal Mapping
    # -----------------------------------------------------
    _EVENT_TO_CODE = {
        "process_enqueued": "decision_emitted",
        "process_completed": "decision_emitted",
        "process_aborted": "instability_detected",
        "process_suspended": "early_warning_detected",
        "process_blocked": "conflict_detected",
        "process_waiting_confirmation": "uncertainty_detected",
        "scheduler_selected": "decision_emitted",
        "process_preempted": "early_warning_detected",
        "hook_error": "ghost_signal",
        "syscall_succeeded": "decision_emitted",
        "syscall_failed": "ghost_signal",
    }

    def _map_runtime_event(
        self,
        event_type: str,
        payload: dict[str, Any]
    ) -> CanonicalSignal:
        code = self._EVENT_TO_CODE.get(event_type)

        if code is None:
            # fallback safe (important for forward compatibility)
            code = "ghost_signal"

        current_tick = self.scheduler_state.tick_count

        # reset counter when tick changes
        if current_tick != self._last_tick:
            self._local_counter = 0
            self._last_tick = current_tick

        self._local_counter += 1

        ts = float(current_tick) + (self._local_counter * 1e-6)

        # SAFETY: enforce monotonicity vs factory
        if ts <= self._last_ts_local:
            ts = self._last_ts_local + 1e-6

        self._last_ts_local = ts

        signal = SignalFactory.create(
            code,
            subject_ref=f"process:{payload.get('process_id', 'unknown')}",
            temporal_anchor=f"tick:{self.scheduler_state.tick_count}",
            timestamp=ts,
            signal_id=payload.get("causal_id"),
        )

        return signal

    def running_processes(self) -> list[CognitiveProcess]:
        return [
            p for p in self.processes.values()
            if p.status.value == "running"
        ]
    
    # -----------------------------------------------------
    # Timeline commitment (Veramem-backed)
    # -----------------------------------------------------
    def compute_timeline_commitment(self) -> str:
        if not isinstance(self.timeline, SignalJournal):
            raise RuntimeError("Timeline is not a SignalJournal")

        snapshot = signal_journal_to_timeline_snapshot(self.timeline)
        commitment = TimelineCommitment.from_snapshot(snapshot)
        return commitment.commitment