# arvis/kernel/pipeline/result/observability_result.py

from dataclasses import dataclass
from typing import Any

from arvis.cognition.state.cognitive_state import CognitiveState


@dataclass(frozen=True)
class PipelineObservabilityResult:
    scientific: Any | None = None
    control: Any | None = None
    cognitive_state: CognitiveState | None = None
    # The opaque cross-turn blob a host feeds back as
    # ctx.extra["scientific_state"] on the next turn (DM-F3): the
    # pipeline documented the contract but no typed surface carried
    # it out, so hosts could only read it from a mutated extra dict.
    next_scientific_state: dict[str, Any] | None = None
