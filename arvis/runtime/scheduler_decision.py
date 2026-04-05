# arvis/runtime/scheduler_decision.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from arvis.runtime.cognitive_process import CognitiveBudget, CognitiveProcessId


@dataclass
class SchedulerDecision:
    selected_process_id: Optional[CognitiveProcessId]
    rationale: str
    resource_grant: Optional[CognitiveBudget] = None
    preempted_process_id: Optional[CognitiveProcessId] = None
    score: Optional[float] = None
    result: Any | None = None

    @property
    def is_noop(self) -> bool:
        return self.selected_process_id is None