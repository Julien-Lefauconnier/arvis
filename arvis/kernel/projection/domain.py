# arvis/kernel/projection/domain.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NumericBounds:
    min_value: float
    max_value: float

    def contains(self, value: float) -> bool:
        return self.min_value <= value <= self.max_value

    def margin(self, value: float) -> float:
        if not self.contains(value):
            return -1.0
        return min(value - self.min_value, self.max_value - value)


@dataclass(frozen=True)
class ProjectionDomain:
    """
    Exécutable: définit le domaine admissible de la projection Pi.

    Ce n'est PAS un concept abstrait:
    → c'est un validateur runtime.
    """

    # --- numeric bounds projected---
    bounds: dict[str, NumericBounds] = field(default_factory=dict)

    # --- payload size --- (ex: text, tokens, etc.)
    max_payload_size: int | None = None

    # --- custom validator ---
    custom_validator: Callable[[dict[str, Any]], bool] | None = None

    # tolérance globale (bruit, etc.)
    epsilon: float = 1e-6

    def validate(self, projected: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
        """
        Retourne:
        - validité globale
        - détails par contrainte
        """
        checks: dict[str, bool] = {}

        # --- numeric bounds ---
        for key, bounds in self.bounds.items():
            value = projected.get(key)
            if value is None:
                checks[f"{key}_present"] = False
                continue

            if not isinstance(value, (int, float)):
                checks[f"{key}_numeric"] = False
                continue

            checks[f"{key}_bounds"] = bounds.contains(float(value))

        # --- payload size ---
        if self.max_payload_size is not None:
            size = len(str(projected))
            checks["payload_size"] = size <= self.max_payload_size

        # --- custom validator ---
        if self.custom_validator is not None:
            try:
                checks["custom"] = self.custom_validator(projected)
            except Exception:
                checks["custom"] = False

        is_valid = all(checks.values()) if checks else True
        return is_valid, checks

    def margin_to_boundary(self, projected: dict[str, Any]) -> float:
        """
        Approximation conservative de la distance à la frontière du domaine.
        """
        margins = []

        for key, bounds in self.bounds.items():
            value = projected.get(key)
            if isinstance(value, (int, float)):
                m = bounds.margin(float(value))
                if m >= 0:
                    margins.append(m)

        if not margins:
            return -1.0

        return min(margins)
