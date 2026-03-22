# tests/math/test_projection_lyapunov_compatibility.py

import math

import pytest

from arvis.cognition.projection.projection_api import project_observation
from tests.fixtures.projection_cases import (
    nominal_case,
    high_risk_case,
    boundary_case,
    noisy_case,
)


# ----------------------------------------
# Dummy Lyapunov (aligned with current core)
# ----------------------------------------

def lyapunov(x, z):
    # Simple proxy: quadratic energy
    return sum(v * v for v in x) + sum(v * v for v in z)


# ----------------------------------------
# Tests
# ----------------------------------------

@pytest.mark.parametrize(
    "case_fn",
    [
        nominal_case,
        high_risk_case,
        boundary_case,
        noisy_case,
    ],
)
def test_lyapunov_is_finite_and_defined(case_fn):
    obs = case_fn()
    proj = project_observation(obs)

    W = lyapunov(proj.x, proj.z)

    assert not math.isnan(W)
    assert not math.isinf(W)
    assert W >= 0.0


def test_lyapunov_continuity_under_small_perturbation():
    base_obs = nominal_case()
    base_proj = project_observation(base_obs)
    W_base = lyapunov(base_proj.x, base_proj.z)

    eps = 0.01
    variations = []

    for i in range(50):
        perturbed = base_obs.__class__(
            numeric_signals={
                k: float(v) + eps for k, v in base_obs.numeric_signals.items()
            },
            structured_signals=base_obs.structured_signals,
            external_signals=base_obs.external_signals,
        )

        proj = project_observation(perturbed)
        W = lyapunov(proj.x, proj.z)

        variations.append(abs(W - W_base))

    max_var = max(variations)

    # No violent discontinuity
    assert max_var < 5.0


def test_lyapunov_consistency_with_norms():
    obs = nominal_case()
    proj = project_observation(obs)

    W = lyapunov(proj.x, proj.z)

    # W should be correlated with norms
    norm_sum = proj.diagnostics.x_norm + proj.diagnostics.z_norm

    assert W >= 0.0
    assert norm_sum >= 0.0

    # basic sanity: non-zero norm → non-zero energy
    if norm_sum > 1e-6:
        assert W > 0.0


def test_no_lyapunov_break_on_invalid_input():
    # even invalid input must not break W computation
    obs = nominal_case().__class__(
        numeric_signals={"risk": "invalid"},
        structured_signals={},
        external_signals={},
    )

    proj = project_observation(obs)

    W = lyapunov(proj.x, proj.z)

    assert not math.isnan(W)
    assert not math.isinf(W)