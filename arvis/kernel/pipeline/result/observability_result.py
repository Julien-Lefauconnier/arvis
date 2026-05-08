# arvis/kernel/pipeline/result/observability_result.py

from dataclasses import dataclass
from typing import Any

from arvis.cognition.state.cognitive_state import CognitiveState


@dataclass(frozen=True)
class PipelineObservabilityResult:
    scientific: Any | None = None
    control: Any | None = None
    cognitive_state: CognitiveState | None = None
