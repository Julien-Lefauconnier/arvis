# arvis/kernel/pipeline/context/execution_context.py

from dataclasses import dataclass
from typing import Any

from arvis.action.action_decision import ActionDecision
from arvis.runtime.execution.cognitive_execution_state import (
    CognitiveExecutionState,
)


@dataclass
class PipelineExecutionContext:
    executable_intent: Any | None = None
    action_decision: ActionDecision | None = None
    execution_state: CognitiveExecutionState | None = None
