# tests/math/lyapunov/test_target_map.py

import pytest

from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.target_map import target_map


@pytest.fixture
def symbolic_empty():
    return SymbolicState(
        intent_type="unknown",
        intent_confidence=0.0,
        gate_verdict="unknown",
        conversation_mode="unknown",
        conflict_histogram={},
        conflict_severity=0.0,
        override_count=0,
        override_rate=0.0,
    )


def test_target_map_no_gate_dependency(symbolic_empty):
    fast = LyapunovState(0.1, 0.2, 0.3, 0.4)

    T = target_map(symbolic_empty, fast=fast)

    assert T.shape == (4,)


def test_target_map_convex_combination(symbolic_empty):
    fast = LyapunovState(1.0, 1.0, 1.0, 1.0)

    T = target_map(symbolic_empty, fast=fast, rho_fast=0.3)

    assert (T >= 0.0).all()
    assert (T <= 1.0).all()
