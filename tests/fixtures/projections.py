# tests/fixtures/projections.py

import pytest

from tests.fixtures.builders.projection_builder import (
    build_projection_state,
)


@pytest.fixture
def nominal_projection():
    return build_projection_state()


@pytest.fixture
def unstable_projection():
    return build_projection_state(
        conflict_pressure=0.9,
        drift_score=0.8,
        collapse_risk=0.95,
        confidence=0.1,
    )
