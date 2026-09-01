# validation/m10/estimators.py
"""LOT B2: measuring alpha and L_T on the projected dynamics.

M13 names this the sharpest open problem: the switching guard runs
kappa_eff = alpha - gamma_z * eta * L_T with assumed constants
(alpha=0.15, L_T=1.0 in the preparation defaults). This module
MEASURES both on corpus D:

- alpha: per-step contraction factor of the energy the gate actually
  consumed, alpha_t = 1 - W_{t+1}/W_t, estimated over the contraction
  segments of the nominal family (the regime A12 speaks about);
- L_T: sampled Lipschitz ratios of the target map T over pairs of
  symbolic states drawn from its input domain,
  ||T(s1) - T(s2)|| / d(s1, s2).

Both come back as distributions, not points: the report publishes
median and dispersion, and the small-gain margin is re-evaluated at
the conservative quantiles.
"""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.target_map import target_map
from arvis.math.state.symbolic_state import SymbolicState
from validation.m10.runner import TurnMeasurement

_EPS = 1e-9


@dataclass(frozen=True)
class AlphaEstimate:
    samples: int
    median: float | None
    mean: float | None
    p10: float | None
    p90: float | None
    contraction_share: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "samples": self.samples,
            "median": self.median,
            "mean": self.mean,
            "p10": self.p10,
            "p90": self.p90,
            "contraction_share": self.contraction_share,
        }


def estimate_alpha(
    ms: list[TurnMeasurement],
    families: tuple[str, ...] = ("nominal",),
) -> AlphaEstimate:
    """Per-step contraction factors from consecutive W pairs of the
    selected families (nominal by default: A12's contraction regime)."""
    factors: list[float] = []
    steps = 0
    by_trajectory: dict[str, list[TurnMeasurement]] = {}
    for m in ms:
        if m.family in families:
            by_trajectory.setdefault(m.trajectory_id, []).append(m)
    for turns in by_trajectory.values():
        turns = sorted(turns, key=lambda t: t.turn_index)
        for prev, cur in itertools.pairwise(turns):
            if prev.w_current is None or cur.w_current is None:
                continue
            if prev.w_current <= _EPS:
                continue
            steps += 1
            factor = 1.0 - (cur.w_current / prev.w_current)
            if factor > 0.0:
                factors.append(factor)
    factors.sort()

    def q(p: float) -> float | None:
        if not factors:
            return None
        idx = min(len(factors) - 1, max(0, int(p * (len(factors) - 1))))
        return factors[idx]

    return AlphaEstimate(
        samples=len(factors),
        median=q(0.5),
        mean=sum(factors) / len(factors) if factors else None,
        p10=q(0.1),
        p90=q(0.9),
        contraction_share=(len(factors) / steps) if steps else 0.0,
    )


@dataclass(frozen=True)
class LipschitzEstimate:
    samples: int
    median: float | None
    p90: float | None
    p99: float | None
    max_ratio: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "samples": self.samples,
            "median": self.median,
            "p90": self.p90,
            "p99": self.p99,
            "max_ratio": self.max_ratio,
        }


_INTENTS = ("informational_query", "search", "action_request", "unknown")
_VERDICTS = ("ALLOW", "REQUIRE_CONFIRMATION", "ABSTAIN")
_MODES = ("default", "focused", "degraded")


def _random_symbolic(rng: random.Random) -> SymbolicState:
    histogram = {
        kind: rng.randrange(0, 4)
        for kind in ("epistemic", "decision", "temporal", "ethical")
        if rng.random() < 0.7
    }
    return SymbolicState(
        intent_type=rng.choice(_INTENTS),
        intent_confidence=round(rng.uniform(0.0, 1.0), 4),
        gate_verdict=rng.choice(_VERDICTS),
        conversation_mode=rng.choice(_MODES),
        conflict_histogram=histogram,
        conflict_severity=round(rng.uniform(0.0, 1.0), 4),
        override_count=rng.randrange(0, 5),
        override_rate=round(rng.uniform(0.0, 1.0), 4),
    )


def _symbolic_distance(a: SymbolicState, b: SymbolicState) -> float:
    """Input-side metric for the Lipschitz ratio: euclidean over the
    numeric coordinates plus discrete jumps for the categorical ones
    (a documented, published choice; L_T is only meaningful relative
    to an explicit input metric)."""
    numeric = math.sqrt(
        (a.intent_confidence - b.intent_confidence) ** 2
        + (a.conflict_severity - b.conflict_severity) ** 2
        + (a.override_rate - b.override_rate) ** 2
    )
    discrete = (
        (a.intent_type != b.intent_type)
        + (a.gate_verdict != b.gate_verdict)
        + (a.conversation_mode != b.conversation_mode)
    )
    hist_keys = set(a.conflict_histogram) | set(b.conflict_histogram)
    hist = sum(
        abs(a.conflict_histogram.get(k, 0) - b.conflict_histogram.get(k, 0))
        for k in hist_keys
    )
    return numeric + float(discrete) + 0.25 * float(hist)


def estimate_target_map_lipschitz(
    samples: int = 4000,
    seed: int = 20260901,
) -> LipschitzEstimate:
    """Sampled Lipschitz ratios of target_map over random symbolic
    state pairs (with a shared fast state, T's second input)."""
    rng = random.Random(seed)
    ratios: list[float] = []
    for _ in range(samples):
        fast = LyapunovState(
            budget_used=rng.uniform(0.0, 1.0),
            risk=rng.uniform(0.0, 1.0),
            uncertainty=rng.uniform(0.0, 1.0),
            governance=rng.uniform(0.0, 1.0),
        )
        s1 = _random_symbolic(rng)
        s2 = _random_symbolic(rng)
        distance = _symbolic_distance(s1, s2)
        if distance <= _EPS:
            continue
        t1 = np.asarray(target_map(s1, fast=fast), dtype=float)
        t2 = np.asarray(target_map(s2, fast=fast), dtype=float)
        ratios.append(float(np.linalg.norm(t1 - t2)) / distance)
    ratios.sort()

    def q(p: float) -> float | None:
        if not ratios:
            return None
        idx = min(len(ratios) - 1, max(0, int(p * (len(ratios) - 1))))
        return ratios[idx]

    return LipschitzEstimate(
        samples=len(ratios),
        median=q(0.5),
        p90=q(0.9),
        p99=q(0.99),
        max_ratio=ratios[-1] if ratios else None,
    )


def small_gain_verdict(
    alpha: AlphaEstimate,
    lipschitz: LipschitzEstimate,
    gamma_z: float = 0.4,
    eta: float = 0.05,
    assumed_alpha: float = 0.15,
    assumed_l_t: float = 1.0,
) -> dict[str, Any]:
    """kappa_eff = alpha - gamma_z * eta * L_T, assumed vs measured
    (measured conservatively: alpha at its p10, L_T at its p99)."""
    assumed = assumed_alpha - gamma_z * eta * assumed_l_t
    measured: float | None = None
    if alpha.p10 is not None and lipschitz.p99 is not None:
        measured = alpha.p10 - gamma_z * eta * lipschitz.p99
    return {
        "kappa_eff_assumed": assumed,
        "kappa_eff_measured_conservative": measured,
        "alpha_assumed": assumed_alpha,
        "alpha_measured_p10": alpha.p10,
        "alpha_measured_median": alpha.median,
        "l_t_assumed": assumed_l_t,
        "l_t_measured_p99": lipschitz.p99,
        "l_t_measured_median": lipschitz.median,
        "small_gain_positive_measured": (measured is not None and measured > 0.0),
    }
