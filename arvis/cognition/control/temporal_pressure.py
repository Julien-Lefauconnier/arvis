# arvis/cognition/control/temporal_pressure.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp01


@dataclass(frozen=True)
class TemporalPressureSnapshot:
    pressure: float
    volatility: float
    density: float
    health_penalty: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "pressure", clamp01(self.pressure))
        object.__setattr__(self, "volatility", clamp01(self.volatility))
        object.__setattr__(self, "density", clamp01(self.density))
        object.__setattr__(self, "health_penalty", clamp01(self.health_penalty))


class TemporalPressure:
    """
    Kernel-safe temporal pressure model.

    Requires external timeline summary input.
    """

    def compute(
        self,
        *,
        total: int,
        has_conflicts: bool,
        has_gaps: bool,
        has_uncertainty: bool,
        healthy: bool,
    ) -> TemporalPressureSnapshot:
        density = min(1.0, float(total) / 100.0) if total > 0 else 0.0

        conflicts = 1 if has_conflicts else 0
        gaps = 1 if has_gaps else 0
        uncertainty = 1 if has_uncertainty else 0

        instability_ratio = float(conflicts + gaps + uncertainty) / float(max(1, total))
        volatility = min(1.0, instability_ratio * 2.0)

        health_penalty = 0.2 if not healthy else 0.0

        pressure = clamp01(0.5 * density + 0.4 * volatility + health_penalty)

        return TemporalPressureSnapshot(
            pressure=float(pressure),
            volatility=float(volatility),
            density=float(density),
            health_penalty=float(health_penalty),
        )
