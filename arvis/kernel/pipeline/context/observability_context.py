# arvis/kernel/pipeline/context/observability_context.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.ir.state import CognitiveStateIR


@dataclass
class PipelineObservabilityContext:
    """
    Read-only observability projection space.

    Contains:
    - predictive projections
    - global stability projections
    - symbolic observability
    - derived stability statistics

    No runtime authority.
    No decision authority.
    No execution authority.
    """

    predictive_snapshot: Any | None = None
    global_forecast: Any | None = None
    global_stability: Any | None = None
    multi_horizon: Any | None = None

    stability_stats: Any | None = None
    stability_projection: Any | None = None
    stability_statistics: Any | None = None

    symbolic_drift: Any | None = None
    symbolic_features: Any | None = None

    system_tension: Any | None = None

    ir_state: CognitiveStateIR | None = None
    cognitive_state: Any | None = None
