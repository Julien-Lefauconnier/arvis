# arvis/kernel/projection/projected_state.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProjectedState:
    """
    Runtime implementation of Π_impl.

    This is NOT the theoretical full Π : C -> (x, z, q, w).
    It is a deterministic, typed runtime projection extracted from the
    pipeline context, designed to feed certification (Π_cert).
    """

    state_signals: dict[str, float] = field(default_factory=dict)
    risk_signals: dict[str, float] = field(default_factory=dict)
    control_signals: dict[str, float] = field(default_factory=dict)
    trace_features: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_projection_view(self) -> dict[str, float]:
        """
        Flat numeric view used by the certification layer.

        Names are prefixed to keep the projected space explicit and stable.
        """
        projection: dict[str, float] = {}

        def _inject(prefix: str, values: Mapping[str, float]) -> None:
            for key, value in values.items():
                if isinstance(value, (int, float)):
                    projection[f"{prefix}.{key}"] = float(value)

        _inject("state", self.state_signals)
        _inject("risk", self.risk_signals)
        _inject("control", self.control_signals)
        _inject("trace", self.trace_features)

        return projection

    def primary_tension(self) -> float:
        """
        Backward-compatible helper for legacy code/tests still expecting
        system_tension semantics.
        """
        return float(
            self.state_signals.get(
                "system_tension",
                self.risk_signals.get("system_tension", 0.0),
            )
        )
