# arvis/runtime/cognitive_runtime_state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from arvis.runtime.cognitive_process import CognitiveProcess, CognitiveProcessId
from arvis.runtime.resource_model import ResourceState
from arvis.runtime.scheduler_state import SchedulerState


@dataclass
class CognitiveRuntimeState:
    scheduler_state: SchedulerState = field(default_factory=SchedulerState)
    resource_state: ResourceState = field(default_factory=ResourceState)
    processes: dict[CognitiveProcessId, CognitiveProcess] = field(default_factory=dict)
    memory_topology: Optional[Any] = None
    control_state: Optional[Any] = None
    timeline: list[dict[str, Any]] = field(default_factory=list)

    def register_process(self, process: CognitiveProcess) -> None:
        process.validate()
        self.processes[process.process_id] = process
        self.resource_state.note_process_seen()

    def get_process(self, process_id: CognitiveProcessId) -> CognitiveProcess:
        try:
            return self.processes[process_id]
        except KeyError as exc:
            raise KeyError(f"Unknown process id: {process_id.value}") from exc

    def append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.timeline.append(
            {
                "event_type": event_type,
                "tick": self.scheduler_state.tick_count,
                "payload": payload,
            }
        )

    def running_processes(self) -> list[CognitiveProcess]:
        return [
            p for p in self.processes.values()
            if p.status.value == "running"
        ]