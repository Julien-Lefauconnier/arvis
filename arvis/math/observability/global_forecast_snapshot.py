# arvis/cognition/observability/global_forecast_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalForecastSnapshot:
    predicted_mean_delta: float
    slope: float
    collapse_risk: float
    time_to_critical: float | None
    early_warning: bool
