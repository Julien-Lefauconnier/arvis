# arvis/runtime/scheduler_decision.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.runtime.cognitive_process import CognitiveBudget, CognitiveProcessId
from arvis.runtime.runtime_decision_record import RuntimeDecisionRecord


@dataclass
class SchedulerDecision:
    selected_process_id: CognitiveProcessId | None
    rationale: str
    resource_grant: CognitiveBudget | None = None
    preempted_process_id: CognitiveProcessId | None = None
    score: float | None = None
    result: Any | None = None
    decision_record: RuntimeDecisionRecord | None = None

    @property
    def is_noop(self) -> bool:
        return self.selected_process_id is None
