# arvis/stability/global_forecast_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalForecastSnapshot:
    """
    Declarative stability forecast snapshot.

    Kernel guarantees:
    - numeric only
    - no forecasting logic
    """

    predicted_mean_delta: float
    slope: float
    collapse_risk: float
    time_to_critical: float | None
    early_warning: bool
