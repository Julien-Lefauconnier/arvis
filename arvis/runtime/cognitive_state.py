# arvis/runtime/cognitive_state.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel_core.process import (
    CognitiveProcess,
    CognitiveProcessId,
)
from arvis.kernel_core.state.scheduler_state import SchedulerState
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.resource_model import ResourceState
from arvis.signals.signal_journal import SignalJournal

RuntimeResult = object


@dataclass(frozen=True)
class CognitiveState:
    runtime: CognitiveRuntimeState
    last_result: RuntimeResult | None = None

    @property
    def scheduler_state(self) -> SchedulerState:
        return self.runtime.scheduler_state

    @property
    def resource_state(self) -> ResourceState:
        return self.runtime.resource_state

    @property
    def processes(
        self,
    ) -> dict[CognitiveProcessId, CognitiveProcess]:
        return self.runtime.processes

    @property
    def timeline(self) -> SignalJournal:
        return self.runtime.timeline
