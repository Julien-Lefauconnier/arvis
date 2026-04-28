# # arvis/runtime/cognitive_state.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState


@dataclass(frozen=True)
class CognitiveState:
    runtime: CognitiveRuntimeState
    last_result: Any = None

    @property
    def scheduler_state(self) -> Any:
        return self.runtime.scheduler_state

    @property
    def resource_state(self) -> Any:
        return self.runtime.resource_state

    @property
    def processes(self) -> Any:
        return self.runtime.processes

    @property
    def timeline(self) -> Any:
        return self.runtime.timeline
