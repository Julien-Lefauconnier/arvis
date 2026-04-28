# tests/math/adaptive/test_adaptive_kappa_eff_on_projection_trajectory.py

import math
import random

from arvis.cognition.projection.projection_api import Observation, project_observation
from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from tests.fixtures.projection_cases import nominal_case
from tests.math.test_projection_real_lyapunov_compatibility import (
    _fast_state_from_projection,
    _slow_state_from_projection,
    _symbolic_state_from_mode,
)


def _generate_projection_trajectory(
    base_obs: Observation, steps: int = 80, noise: float = 0.015
) -> list[Observation]:
    trajectory = [base_obs]

    for _ in range(steps):
        prev = trajectory[-1]
        nxt = Observation(
            numeric_signals={
                k: float(v) + random.uniform(-noise, noise)
                for k, v in prev.numeric_signals.items()
            },
            structured_signals=prev.structured_signals,
            external_signals=prev.external_signals,
        )
        trajectory.append(nxt)

    return trajectory


def _compute_W(comp: CompositeLyapunov, obs: Observation) -> float:
    proj = project_observation(obs)
    fast = _fast_state_from_projection(proj)
    slow = _slow_state_from_projection(proj)
    symbolic = _symbolic_state_from_mode(proj.q)
    return comp.W(fast=fast, slow=slow, symbolic=symbolic)


def test_adaptive_kappa_is_defined_on_projection_trajectory():
    comp = CompositeLyapunov()
    est = AdaptiveKappaEffEstimator()

    trajectory = _generate_projection_trajectory(nominal_case(), steps=60, noise=0.01)
    W_values = [_compute_W(comp, obs) for obs in trajectory]

    snapshots = []
    for prev, nxt in zip(W_values[:-1], W_values[1:]):
        snapshots.append(est.update(W_prev=prev, W_next=nxt))

    assert len(snapshots) > 0
    assert any(s.is_available for s in snapshots)

    available = [s for s in snapshots if s.is_available]
    assert len(available) > 0

    for snap in available:
        assert snap.kappa_smoothed is not None
        assert not math.isnan(snap.kappa_smoothed)
        assert not math.isinf(snap.kappa_smoothed)
        assert 0.0 <= snap.kappa_smoothed <= est.config.kappa_max


def test_adaptive_kappa_on_projection_trajectory_produces_valid_margin():
    comp = CompositeLyapunov()
    est = AdaptiveKappaEffEstimator()

    trajectory = _generate_projection_trajectory(nominal_case(), steps=60, noise=0.01)
    W_values = [_compute_W(comp, obs) for obs in trajectory]

    for prev, nxt in zip(W_values[:-1], W_values[1:]):
        est.update(W_prev=prev, W_next=nxt)

    margin = est.adaptive_switching_margin(J=1.1, tau_d=12.0)

    assert margin is not None
    assert not math.isnan(margin)
    assert not math.isinf(margin)


def test_adaptive_kappa_on_projection_trajectory_remains_bounded_under_stronger_noise():
    comp = CompositeLyapunov()
    est = AdaptiveKappaEffEstimator()

    trajectory = _generate_projection_trajectory(nominal_case(), steps=80, noise=0.03)
    W_values = [_compute_W(comp, obs) for obs in trajectory]

    kappas = []
    for prev, nxt in zip(W_values[:-1], W_values[1:]):
        snap = est.update(W_prev=prev, W_next=nxt)
        if snap.is_available and snap.kappa_smoothed is not None:
            kappas.append(snap.kappa_smoothed)

    assert len(kappas) > 0
    assert min(kappas) >= est.config.kappa_min
    assert max(kappas) <= est.config.kappa_max


def test_adaptive_kappa_regime_is_never_unknown_when_available():
    comp = CompositeLyapunov()
    est = AdaptiveKappaEffEstimator()

    trajectory = _generate_projection_trajectory(nominal_case(), steps=50, noise=0.02)
    W_values = [_compute_W(comp, obs) for obs in trajectory]

    valid_regimes = {"stable", "marginal", "unstable", "unavailable"}

    for prev, nxt in zip(W_values[:-1], W_values[1:]):
        snap = est.update(W_prev=prev, W_next=nxt)
        assert snap.regime in valid_regimes
        if snap.is_available:
            assert snap.regime != "unavailable"
