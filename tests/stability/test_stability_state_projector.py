# tests/stability/test_stability_state_projector.py

import pytest

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.state.lyapunov_projection_state import (
    LyapunovProjectionState,
)
from arvis.stability.stability_state_projector import (
    StabilityStateProjector,
)


def test_projector_basic(nominal_projection):
    state = StabilityStateProjector.from_projection(nominal_projection)

    assert isinstance(state, LyapunovState)

    assert 0.0 <= state.risk <= 1.0
    assert 0.0 <= state.uncertainty <= 1.0
    assert 0.0 <= state.governance <= 1.0


def test_projection_mapping_values():
    projection = LyapunovProjectionState(
        conflict_pressure=0.2,
        drift_score=0.6,
        collapse_risk=0.4,
        confidence=0.75,
    )

    state = StabilityStateProjector.from_projection(projection)

    assert state.risk == pytest.approx(0.4)
    assert state.uncertainty == pytest.approx(0.25)
    assert state.governance == pytest.approx(0.6)


def test_projection_clamping():
    projection = LyapunovProjectionState(
        conflict_pressure=10.0,
        drift_score=10.0,
        collapse_risk=10.0,
        confidence=-10.0,
    )

    state = StabilityStateProjector.from_projection(projection)

    assert state.risk == 1.0
    assert state.uncertainty == 1.0
    assert state.governance == 1.0


def test_projection_invalid_values_safe():
    projection = LyapunovProjectionState(
        conflict_pressure=0.0,
        drift_score="invalid",  # type: ignore[arg-type]
        collapse_risk="invalid",  # type: ignore[arg-type]
        confidence="invalid",  # type: ignore[arg-type]
    )

    state = StabilityStateProjector.from_projection(projection)

    assert state.risk == 0.0
    assert state.uncertainty == 0.0
    assert state.governance == 0.0


def test_project_passthrough():
    projector = StabilityStateProjector()

    obj = {"x": 1}

    assert projector.project(obj) is obj
