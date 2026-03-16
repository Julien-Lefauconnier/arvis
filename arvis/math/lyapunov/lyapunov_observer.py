# arvis/math//lyapunov/lyapunov_observer.py

from dataclasses import dataclass
from typing import Optional, Dict, Any

from arvis.math.lyapunov.lyapunov import LyapunovState,V
from arvis.stability.stability_state_projector import StabilityStateProjector as LyapunovStateBuilder

from arvis.math.lyapunov.lyapunov_gate import (
    lyapunov_gate,
    LyapunovGateParams,
    LyapunovVerdict,
)
from arvis.stability.stability_observer import StabilityObserver
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot


@dataclass
class LyapunovObservation:
    v_prev: float
    v_new: float
    delta: float
    verdict: LyapunovVerdict


class LyapunovObserver(StabilityObserver):
    """
    Unified observer:
    - math layer
    - bundle layer
    - contract compliant
    """

    def __init__(self, params: Optional[LyapunovGateParams] = None):
        self.params = params or LyapunovGateParams()
        self._last_state: Optional[LyapunovState] = None

    # --------------------------------------------------
    # PURE MATH API (used in unit tests)
    # --------------------------------------------------
    def evaluate(
        self,
        previous_state: LyapunovState,
        new_state: LyapunovState,
    ) -> LyapunovObservation:

        v_prev = V(previous_state)
        v_new = V(new_state)

        verdict = lyapunov_gate(previous_state, new_state, self.params)

        return LyapunovObservation(
            v_prev=v_prev,
            v_new=v_new,
            delta=v_new - v_prev,
            verdict=verdict,
        )

    # --------------------------------------------------
    # PRODUCTION API (contract)
    # --------------------------------------------------
    def observe(
        self,
        previous_bundle: CognitiveBundleSnapshot,
        current_bundle: CognitiveBundleSnapshot,
    ) -> LyapunovObservation:

        prev_state = LyapunovStateBuilder.from_bundle(previous_bundle)
        cur_state = LyapunovStateBuilder.from_bundle(current_bundle)

        # Keep internal last state (optional lifecycle use)
        self._last_state = cur_state

        obs = self.evaluate(prev_state, cur_state)
        return obs

    def reset(self):
        """Useful for tests or session reset."""
        self._last_state = None

    def to_dict(self, obs: LyapunovObservation) -> Dict[str, Any]:
        return {
            "v_prev": obs.v_prev,
            "v_new": obs.v_new,
            "delta": obs.delta,
            "verdict": obs.verdict.value,
        }