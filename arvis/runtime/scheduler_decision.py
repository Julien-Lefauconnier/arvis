# arvis/runtime/scheduler_decision.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.runtime.cognitive_process import CognitiveBudget, CognitiveProcessId


@dataclass
class SchedulerDecision:
    selected_process_id: CognitiveProcessId | None
    rationale: str
    resource_grant: CognitiveBudget | None = None
    preempted_process_id: CognitiveProcessId | None = None
    score: float | None = None
    result: Any | None = None

    @property
    def is_noop(self) -> bool:
        return self.selected_process_id is None
