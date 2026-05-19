# arvis/kernel/pipeline/context/observability/projections_context.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ObservabilityProjectionContext:
    predictive_snapshot: Any | None = None
    global_forecast: Any | None = None
    global_stability: Any | None = None
    multi_horizon: Any | None = None

    stability_stats: Any | None = None
    stability_projection: Any | None = None
    stability_statistics: Any | None = None

    system_tension: Any | None = None
