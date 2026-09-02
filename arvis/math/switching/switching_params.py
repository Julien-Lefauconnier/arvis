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


# Shared floor for a dwell time entering a T1-shaped bound. A zero
# dwell (the turn right after a switch, or a fresh clock) makes the
# bound massively positive, which is exactly what the theory says:
# no dwell has been accumulated, the switching condition is violated.
# The adaptive margin (arvis/math/adaptive/adaptive_kappa_eff.py)
# applies the SAME floor, so the two T1 readings can never diverge on
# how they treat an empty clock (campaign GATE-SEM, DM-G1).
DWELL_TIME_FLOOR: float = 1e-6


def kappa_eff(params: SwitchingParams) -> float:
    return params.alpha - params.gamma_z * params.eta * params.L_T


def switching_lhs(runtime: SwitchingRuntime | None, params: SwitchingParams) -> float:
    if runtime is None:
        return float("-inf")

    try:
        tau_d = max(float(runtime.dwell_time()), DWELL_TIME_FLOOR)
    except Exception:  # arvis-broad: fail-soft runtime probe
        tau_d = DWELL_TIME_FLOOR

    J = max(params.J, 1e-6)
    kappa = kappa_eff(params)
    one_minus_k = max(1e-6, 1.0 - kappa)

    return math.log(J) / tau_d + math.log(one_minus_k)


def switching_condition(
    runtime: SwitchingRuntime | None, params: SwitchingParams
) -> bool:
    return switching_lhs(runtime, params) < 0


# Canonical default parameter set of the 0.1 series (campaign HARDEN,
# DM-H9c: this used to exist as two copies in the pipeline layer, one
# of them dead, while the bootstrap small-gain check declared its own
# alpha=0.3 against these alpha=0.15). Single source; consumers:
# pipeline preparation and the bootstrap small-gain check.
DEFAULT_SWITCHING_PARAMS = SwitchingParams(
    alpha=0.15,
    gamma_z=0.4,
    eta=0.05,
    L_T=1.0,
    J=1.5,
)
