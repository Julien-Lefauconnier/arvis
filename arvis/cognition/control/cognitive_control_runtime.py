# arvis/cognition/control/cognitive_control_runtime.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CognitiveControlRuntime:
    """
    Mutable per-user runtime state for the full control engine.

    This object is intentionally stateful.
    It stores user-local adaptive observers/controllers only.
    """

    epsilon_monitor: object | None = None
    drift_detector: object | None = None
    local_dynamics: object | None = None
    regime_estimator: object | None = None
    regime_control: object | None = None
    exploration_state: object | None = None
    counterfactual: object | None = None
    cf_bandit: object | None = None

    last_action: str | None = None
    last_risk: float | None = None
    inertia_risk: float | None = None