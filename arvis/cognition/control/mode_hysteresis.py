# arvis/cognition/control/mode_hysteresis.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.signals import RiskSignal
from arvis.math.signals.utils import signal_value


@dataclass(frozen=True)
class ModeHysteresisParams:
    safe_enter: float = 0.80
    safe_exit: float = 0.70
    critical_enter: float = 0.90
    critical_exit: float = 0.85


class ModeHysteresis:
    """
    Kernel-safe hysteresis controller.

    Maintains cognitive mode stability across risk transitions.
    """

    def __init__(self, params: ModeHysteresisParams | None = None) -> None:
        self._params = params or ModeHysteresisParams()
        self._state: dict[str, CognitiveMode] = {}

    def update(self, user_id: str, risk: float) -> CognitiveMode:
        risk = signal_value(risk, 0.0)
        prev = self._state.get(user_id, CognitiveMode.NORMAL)
        p = self._params

        if prev == CognitiveMode.CRITICAL:
            if risk < p.critical_exit:
                prev = CognitiveMode.SAFE
            else:
                return CognitiveMode.CRITICAL

        if prev == CognitiveMode.SAFE:
            if risk >= p.critical_enter:
                return CognitiveMode.CRITICAL
            if risk < p.safe_exit:
                prev = CognitiveMode.NORMAL
            else:
                return CognitiveMode.SAFE

        if risk >= p.critical_enter:
            mode = CognitiveMode.CRITICAL
        elif risk >= p.safe_enter:
            mode = CognitiveMode.SAFE
        else:
            mode = CognitiveMode.NORMAL

        self._state[user_id] = mode
        return mode