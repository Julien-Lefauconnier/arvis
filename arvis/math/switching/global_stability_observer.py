# arvis/math/switching/global_stability_observer.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from arvis.math.switching.switching_params import kappa_eff


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


class GlobalStabilityObserver:

    def __init__(self) -> None:
        self.t = 0
        self.W0: Optional[float] = None

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
            )

        if self.W0 is None:
            self.W0 = W

        N = getattr(runtime, "total_switches", 0)

        try:
            tau_d = float(runtime.dwell_time())
        except Exception:
            tau_d = 0.0

        k_eff = kappa_eff(params)

        J = max(params.J, 1e-6)
        one_minus_k = max(1e-6, 1.0 - k_eff)

        try:
            W_bound = (J ** N) * (one_minus_k ** max(self.t - N, 0)) * self.W0
        except Exception:
            W_bound = None

        ratio = None
        if W is not None and W_bound not in (None, 0):
            ratio = W / W_bound

        safe = ratio is None or ratio <= 1.0

        return GlobalStabilityMetrics(
            W_current=W,
            W_bound=W_bound,
            ratio=ratio,
            tau_d=tau_d,
            switches=N,
            time=self.t,
            kappa_eff=k_eff,
            safe=safe,
        )