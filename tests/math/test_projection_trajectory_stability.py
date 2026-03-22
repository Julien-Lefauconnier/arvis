# tests/math/test_projection_trajectory_stability.py

import math
import random


from arvis.cognition.projection.projection_api import project_observation, Observation
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from tests.math.test_projection_real_lyapunov_compatibility import (
    _fast_state_from_projection,
    _slow_state_from_projection,
    _symbolic_state_from_mode,
)
from tests.fixtures.projection_cases import nominal_case


def generate_trajectory(base_obs, steps=50, noise=0.02):
    trajectory = [base_obs]

    for _ in range(steps):
        prev = trajectory[-1]

        perturbed = Observation(
            numeric_signals={
                k: float(v) + random.uniform(-noise, noise)
                for k, v in prev.numeric_signals.items()
            },
            structured_signals=prev.structured_signals,
            external_signals=prev.external_signals,
        )

        trajectory.append(perturbed)

    return trajectory


def test_trajectory_lyapunov_stability():
    comp = CompositeLyapunov()

    trajectory = generate_trajectory(nominal_case(), steps=100)

    W_values = []
    delta_values = []

    prev = None

    for obs in trajectory:
        proj = project_observation(obs)

        fast = _fast_state_from_projection(proj)
        slow = _slow_state_from_projection(proj)
        symbolic = _symbolic_state_from_mode(proj.q)

        W = comp.W(fast=fast, slow=slow, symbolic=symbolic)
        W_values.append(W)

        if prev is not None:
            delta = comp.delta_W(
                fast_prev=prev["fast"],
                fast_next=fast,
                slow_prev=prev["slow"],
                slow_next=slow,
                symbolic_prev=prev["symbolic"],
                symbolic_next=symbolic,
            )
            delta_values.append(delta)

        prev = {
            "fast": fast,
            "slow": slow,
            "symbolic": symbolic,
        }

    # -----------------------------
    # Checks
    # -----------------------------

    # 1. No explosion
    assert max(W_values) < 100.0

    # 2. No NaN
    assert all(not math.isnan(w) for w in W_values)

    # 3. ΔW not exploding
    if delta_values:
        max_delta = max(abs(d) for d in delta_values)
        assert max_delta < 50.0

    # 4. Trend sanity (not strictly decreasing, but not diverging)
    mean_W = sum(W_values) / len(W_values)
    assert mean_W < 50.0