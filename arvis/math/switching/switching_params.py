# arvis/math/switching/switching_params.py

import math
from dataclasses import dataclass
from typing import Protocol


class SwitchingRuntime(Protocol):
    def dwell_time(self) -> float: ...

    total_switches: int


@dataclass(frozen=True)
class SwitchingParams:
    alpha: float
    gamma_z: float
    eta: float
    L_T: float
    J: float


def kappa_eff(params: SwitchingParams) -> float:
    return params.alpha - params.gamma_z * params.eta * params.L_T


def switching_lhs(runtime: SwitchingRuntime | None, params: SwitchingParams) -> float:
    if runtime is None:
        return float("-inf")

    try:
        tau_d = max(float(runtime.dwell_time()), 1e-6)
    except Exception:
        tau_d = 1e-6

    J = max(params.J, 1e-6)
    kappa = kappa_eff(params)
    one_minus_k = max(1e-6, 1.0 - kappa)

    return math.log(J) / tau_d + math.log(one_minus_k)


def switching_condition(
    runtime: SwitchingRuntime | None, params: SwitchingParams
) -> bool:
    return switching_lhs(runtime, params) < 0
