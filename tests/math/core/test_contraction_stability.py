# tests/math/core/test_contraction_stability.py
"""Adversarial validation of the fast-loop stability certificate.

These tests do not assert on a curated happy path: they SEARCH for an input
sequence that breaks a proven guarantee: random sequences over many seeds plus
hand-built worst cases (out-of-range, non-finite, alternating extremes): and
confirm the real :class:`ContractionMonitorCore` never violates the compact
invariant (I) or the Lipschitz energy bound (II).
"""

from __future__ import annotations

import math
import random
from typing import Any

from arvis.math.core.contraction_monitor_core import ContractionMonitorCore
from arvis.math.core.stability_certificate import (
    STATE_LOWER,
    STATE_UPPER,
    certify,
)
from arvis.math.lyapunov.lyapunov import LyapunovState, LyapunovWeights, lyapunov_value

_TOL = 1e-9
_REASONS = ("action_request", "search", "informational_query", "unknown", "", None)
_CONFIDENCES: tuple[Any, ...] = (
    None,
    -5.0,
    0.0,
    0.3,
    0.5,
    0.7,
    1.0,
    5.0,
    math.nan,
    math.inf,
)


def _frame(n_axes: int) -> Any:
    return type("Frame", (), {"axes": tuple(range(n_axes))})()


def _bundle(confidence: Any, n_axes: int, reason: Any, pressure: float) -> Any:
    """Duck-typed cognitive bundle the monitor reads (see core_stage seam)."""
    retrieval = (
        None
        if confidence is None
        else type(
            "Retrieval",
            (),
            {"confidence": confidence, "scores": [], "semantic_roles": []},
        )()
    )
    decision = type(
        "Decision",
        (),
        {
            "uncertainty_frames": [_frame(n_axes)] if n_axes else [],
            "reason": reason,
        },
    )()
    return type(
        "Bundle",
        (),
        {
            "retrieval_snapshot": retrieval,
            "decision_result": decision,
            "memory_features": {"memory_pressure": pressure},
        },
    )()


def _adversarial_turn(rng: random.Random) -> Any:
    return _bundle(
        confidence=rng.choice(_CONFIDENCES),
        n_axes=rng.randint(0, 9),
        reason=rng.choice(_REASONS),
        pressure=rng.uniform(-2.0, 2.0),
    )


def test_certificate_constants() -> None:
    cert = certify()
    assert cert.axis_leverage == (0.25, 0.25, 0.25, 0.25)
    assert cert.energy_lipschitz_inf == 1.0
    assert (cert.state_lower, cert.state_upper) == (STATE_LOWER, STATE_UPPER)
    # Skewed (but still convex after normalization) weights keep L_inf == 1.
    skewed = certify(
        LyapunovWeights(w_budget=3.0, w_risk=1.0, w_uncertainty=0.0, w_governance=0.0)
    )
    assert math.isclose(sum(skewed.axis_leverage), 1.0, abs_tol=_TOL)
    assert math.isclose(skewed.energy_lipschitz_inf, 1.0, abs_tol=_TOL)


def test_energy_move_bound_is_an_upper_bound() -> None:
    """Pure check of guarantee (II) on the real energy map, over random pairs."""
    cert = certify()
    rng = random.Random(7)
    for _ in range(20000):
        x = tuple(rng.uniform(0.0, 1.0) for _ in range(4))
        y = tuple(rng.uniform(0.0, 1.0) for _ in range(4))
        v_x = lyapunov_value(LyapunovState(*x))
        v_y = lyapunov_value(LyapunovState(*y))
        dx = (y[0] - x[0], y[1] - x[1], y[2] - x[2], y[3] - x[3])
        assert abs(v_y - v_x) <= cert.energy_move_bound(dx) + _TOL


def test_state_stays_in_compact_invariant_under_adversarial_input() -> None:
    """Guarantee (I): no adversarial sequence escapes the compact box."""
    for seed in range(60):
        rng = random.Random(seed)
        core = ContractionMonitorCore()
        state = None
        for _ in range(50):
            snap, state = core.compute(_adversarial_turn(rng), state)
            cl = snap.cur_lyap
            signals = (
                cl.budget_used,
                cl.risk,
                cl.uncertainty,
                cl.governance,
                snap.energy_v,
                snap.drift_score,
                snap.collapse_risk,
                snap.risk_ucb,
            )
            for value in signals:
                assert math.isfinite(value)
                assert STATE_LOWER - _TOL <= value <= STATE_UPPER + _TOL
            # The certified ceiling never under-reports the empirical risk.
            assert snap.risk_ucb + _TOL >= snap.collapse_risk


def test_energy_change_respects_lipschitz_under_adversarial_input() -> None:
    """Guarantee (II): on the real monitor, |dV| never exceeds the bound."""
    cert = certify()
    for seed in range(60):
        rng = random.Random(1000 + seed)
        core = ContractionMonitorCore()
        state = None
        for _ in range(50):
            snap, state = core.compute(_adversarial_turn(rng), state)
            prev = snap.prev_lyap
            if prev is None:
                continue
            cl = snap.cur_lyap
            dx = (
                cl.budget_used - prev.budget_used,
                cl.risk - prev.risk,
                cl.uncertainty - prev.uncertainty,
                cl.governance - prev.governance,
            )
            assert abs(snap.delta_v) <= cert.energy_move_bound(dx) + _TOL


def test_nonfinite_input_is_neutralized() -> None:
    """NaN/inf grounding confidence is absorbed (clamp -> lower), never raised."""
    core = ContractionMonitorCore()
    state = None
    for confidence in (math.nan, math.inf, -math.inf):
        snap, state = core.compute(_bundle(confidence, 1, "search", 0.0), state)
        risk = snap.cur_lyap.risk
        assert math.isfinite(risk)
        assert STATE_LOWER - _TOL <= risk <= STATE_UPPER + _TOL
