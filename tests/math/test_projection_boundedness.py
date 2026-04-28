# tests/math/test_projection_boundedness.py

import pytest

from arvis.cognition.projection.projection_api import ALLOWED_MODES, project_observation
from tests.fixtures.projection_cases import (
    boundary_case,
    high_risk_case,
    invalid_case,
    noisy_case,
    nominal_case,
)

X_BOUND = 10.0
Z_BOUND = 10.0
W_BOUND = 10.0


@pytest.mark.parametrize(
    "case_fn",
    [
        nominal_case,
        high_risk_case,
        boundary_case,
        noisy_case,
    ],
)
def test_projection_boundedness(case_fn):
    obs = case_fn()
    result = project_observation(obs)

    # --- No crash ---
    assert result is not None

    # --- Norm bounds ---
    assert result.diagnostics.x_norm <= X_BOUND
    assert result.diagnostics.z_norm <= Z_BOUND
    assert result.diagnostics.w_norm <= W_BOUND

    # --- Mode validity ---
    assert result.q in ALLOWED_MODES

    # --- No NaN / inf ---
    for v in result.x + result.z + result.w:
        assert v == v  # NaN check
        assert abs(v) < 1e6


def test_invalid_observation_flagged():
    obs = invalid_case()
    result = project_observation(obs)

    assert not result.diagnostics.is_admissible
    assert len(result.diagnostics.admissibility_violations) > 0
