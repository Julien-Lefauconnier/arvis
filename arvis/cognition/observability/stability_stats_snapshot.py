# arvis/cognition/observability/stability_stats_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class StabilityStatsSnapshot:
    mean_delta: float
    contraction_rate: float
    instability_rate: float
    samples: int