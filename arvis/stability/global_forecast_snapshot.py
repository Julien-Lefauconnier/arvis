# arvis/stability/global_forecast_snapshot.py

from dataclasses import dataclass
from typing import Optional


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
    time_to_critical: Optional[float]
    early_warning: bool
