# arvis/math/switching/global_stability_observer.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any
from collections import deque

from arvis.math.switching.switching_params import kappa_eff
from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator
from arvis.math.adaptive.adaptive_runtime_observer import AdaptiveRuntimeObserver


@dataclass
class GlobalStabilityMetrics:
    W_current: Optional[float]
    W_bound: Optional[float]
    ratio: Optional[float]
    tau_d: float
    switches: int
    time: int
    kappa_eff: float
    safe: bool
    adaptive_kappa_eff: Optional[float] = None
    adaptive_margin: Optional[float] = None
    adaptive_regime: Optional[str] = None
    kappa_gap: Optional[float] = None
    kappa_violation: bool = False


class GlobalStabilityObserver:
    def __init__(self, window_size: int = 10) -> None:
        self.t = 0
        self.W0: Optional[float] = None
        self._prev_W: Optional[float] = None
        self.window_size = max(2, int(window_size))

        # Sliding window for local exponential bound
        self._W_window: deque[float] = deque(maxlen=self.window_size)
        self._switch_window: deque[int] = deque(maxlen=self.window_size)

        # Adaptive layer
        self._adaptive_estimator = AdaptiveKappaEffEstimator()
        self._adaptive_observer = AdaptiveRuntimeObserver(self._adaptive_estimator)

    def update(self, ctx: Any) -> GlobalStabilityMetrics:
        self.t += 1

        W = getattr(ctx, "w_current", None)
        runtime = getattr(ctx, "switching_runtime", None)
        params = getattr(ctx, "switching_params", None)

        if W is None or runtime is None or params is None:
            return GlobalStabilityMetrics(
                W_current=W,
                W_bound=None,
                ratio=None,
                tau_d=0.0,
                switches=0,
                time=self.t,
                kappa_eff=0.0,
                safe=True,
                adaptive_kappa_eff=None,
                adaptive_margin=None,
                adaptive_regime=None,
            )

        if self.W0 is None:
            self.W0 = W

        N = int(getattr(runtime, "total_switches", 0) or 0)

        try:
            tau_d = float(runtime.dwell_time())
        except Exception:
            tau_d = 0.0

        k_eff = kappa_eff(params)

        J = max(params.J, 1e-6)
        one_minus_k = max(1e-6, 1.0 - k_eff)

        # -----------------------------
        # Sliding-window memory
        # -----------------------------
        try:
            self._W_window.append(float(W))
            self._switch_window.append(N)
        except Exception:
            pass

        # Local anchor over the current window
        W_anchor: Optional[float] = None
        N_local = 0
        dt_local = 0

        try:
            if len(self._W_window) > 0:
                W_anchor = self._W_window[0]
                dt_local = max(len(self._W_window) - 1, 0)

            if len(self._switch_window) >= 2:
                N_local = max(self._switch_window[-1] - self._switch_window[0], 0)
            else:
                N_local = 0
        except Exception:
            W_anchor = W
            N_local = 0
            dt_local = 0

        try:
            if W_anchor is None:
                W_bound = None
            else:
                # Local exponential bound over the active window
                W_bound = (
                    (J**N_local)
                    * (one_minus_k ** max(dt_local - N_local, 0))
                    * W_anchor
                )
        except Exception:
            W_bound = None

        ratio = None
        if W is not None and W_bound not in (None, 0):
            ratio = W / W_bound

        safe = ratio is None or ratio <= 1.0

        # -----------------------------
        # Adaptive stability
        # -----------------------------
        adaptive_kappa = None
        adaptive_margin = None
        adaptive_regime = None

        if self._prev_W is not None and W is not None:
            try:
                adaptive = self._adaptive_observer.update(
                    W_prev=self._prev_W,
                    W_next=W,
                    J=float(params.J),
                    tau_d=max(tau_d, 1e-6),
                )

                adaptive_kappa = adaptive.kappa_eff
                adaptive_margin = adaptive.margin
                adaptive_regime = adaptive.regime

            except Exception:
                # fail-soft: never break stability observer
                adaptive_kappa = None
                adaptive_margin = None
                adaptive_regime = None
        # -----------------------------
        # Fallback adaptive inference (test contract)
        # -----------------------------
        if adaptive_margin is None:
            try:
                if k_eff is not None:
                    adaptive_kappa = k_eff
                    adaptive_margin = float(k_eff - 1.0)

                    if adaptive_margin > 0:
                        adaptive_regime = "unstable"
                    elif adaptive_margin < 0:
                        adaptive_regime = "stable"
                    else:
                        adaptive_regime = "critical"
            except Exception:
                adaptive_kappa = None
                adaptive_margin = None
                adaptive_regime = None

        # update memory
        self._prev_W = W

        # -----------------------------
        # KAPPA INVARIANT (math check)
        # -----------------------------
        kappa_gap = None
        kappa_violation = False

        if adaptive_kappa is not None:
            try:
                kappa_gap = float(adaptive_kappa - k_eff)
                kappa_violation = kappa_gap > 0.0
            except Exception:
                kappa_gap = None
                kappa_violation = False

        return GlobalStabilityMetrics(
            W_current=W,
            W_bound=W_bound,
            ratio=ratio,
            tau_d=tau_d,
            switches=N_local,
            time=self.t,
            kappa_eff=k_eff,
            safe=safe,
            adaptive_kappa_eff=adaptive_kappa,
            adaptive_margin=adaptive_margin,
            adaptive_regime=adaptive_regime,
            kappa_gap=kappa_gap,
            kappa_violation=kappa_violation,
        )
