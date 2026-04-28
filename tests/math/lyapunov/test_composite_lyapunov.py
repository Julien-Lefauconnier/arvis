# tests/math/lyapunov/test_composite_lyapunov.py

import pytest
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.math.lyapunov.target_map import target_map
from arvis.math.lyapunov.lyapunov import lyapunov_value


@pytest.fixture
def comp():
    return CompositeLyapunov()


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


def test_W_positive(comp):
    fast = LyapunovState(0.1, 0.2, 0.3, 0.4)
    slow = SlowState(0.5, 0.6, 0.7, 0.8)
    sym = SymbolicState("explore", 0.8, "ALLOW", "normal", {}, 0.1, 0, 0.0)
    w = comp.W(fast, slow, sym)
    assert w >= 0.0
    max_expected = 1.0 + comp.lambda_mismatch * 4.0
    assert w <= max_expected + 1e-6


def test_delta_W_negative_on_improvement(comp, symbolic_empty):
    fast_prev = LyapunovState(0.4, 0.5, 0.5, 0.3)
    fast_next = LyapunovState(0.1, 0.2, 0.2, 0.7)  # amélioration
    slow = SlowState(0.5, 0.5, 0.5, 0.5)
    delta = comp.delta_W(
        fast_prev=fast_prev,
        fast_next=fast_next,
        slow_prev=slow,
        slow_next=slow,
        symbolic_prev=symbolic_empty,
        symbolic_next=symbolic_empty,
    )
    # Fast improvement should not increase energy if slow is aligned
    assert delta < 1e-6


def test_delta_W_positive_on_degradation(comp, symbolic_empty):
    """
    Si fast + slow se dégradent → ΔW doit être positif
    """
    fast_prev = LyapunovState(0.1, 0.1, 0.1, 0.1)
    fast_next = LyapunovState(0.6, 0.6, 0.6, 0.6)

    slow_prev = SlowState(0.1, 0.1, 0.1, 0.1)
    slow_next = SlowState(0.9, 0.9, 0.9, 0.9)

    delta = comp.delta_W(
        fast_prev=fast_prev,
        fast_next=fast_next,
        slow_prev=slow_prev,
        slow_next=slow_next,
        symbolic_prev=symbolic_empty,
        symbolic_next=symbolic_empty,
    )

    assert delta > -1e-6


def test_delta_W_sensitive_to_slow_mismatch(comp, symbolic_empty):
    """
    Même fast stable mais slow diverge → ΔW doit augmenter
    """
    fast = LyapunovState(0.2, 0.2, 0.2, 0.2)

    slow_prev = SlowState(0.1, 0.1, 0.1, 0.1)
    slow_next = SlowState(1.0, 1.0, 1.0, 1.0)

    delta = comp.delta_W(
        fast_prev=fast,
        fast_next=fast,
        slow_prev=slow_prev,
        slow_next=slow_next,
        symbolic_prev=symbolic_empty,
        symbolic_next=symbolic_empty,
    )

    assert delta > 0.0, "ΔW doit détecter la divergence slow"


def test_W_requires_symbolic_or_Tx(comp):
    """
    Doit fallback proprement si symbolic absent
    """
    fast = LyapunovState(0.1, 0.2, 0.3, 0.4)
    slow = SlowState(0.5, 0.6, 0.7, 0.8)

    w = comp.W(fast, slow, symbolic=None, T_x=None)

    assert w >= 0.0
    # W is not bounded to [0,1] anymore:
    # W = V + λ ||z - T(x)||²
    # Upper bound depends on λ and dimension
    max_expected = 1.0 + comp.lambda_mismatch * 4.0
    assert w <= max_expected + 1e-6


def test_W_with_manual_Tx(comp):
    """
    Permet bypass symbolic via T(x)
    """
    import numpy as np

    fast = LyapunovState(0.1, 0.2, 0.3, 0.4)
    slow = SlowState(0.5, 0.6, 0.7, 0.8)

    T_x = np.zeros_like(slow.as_vector())

    w = comp.W(fast, slow, symbolic=None, T_x=T_x)

    assert w >= 0.0


def test_small_gain(comp):
    assert comp.check_small_gain(eta=0.05) is True
    assert comp.check_small_gain(eta=0.5, alpha=0.1, L_T=2.0) is False


def test_W_minimum_at_target(comp, symbolic_empty):
    fast = LyapunovState(0.2, 0.2, 0.2, 0.2)

    T = target_map(symbolic_empty, fast=fast)

    slow_eq = SlowState(*T)

    w = comp.W(fast, slow_eq, symbolic_empty)

    assert abs(w - lyapunov_value(fast)) < 1e-6


def test_delta_W_zero_if_stationary(comp, symbolic_empty):
    fast = LyapunovState(0.3, 0.3, 0.3, 0.3)
    slow = SlowState(0.4, 0.4, 0.4, 0.4)

    delta = comp.delta_W(
        fast_prev=fast,
        fast_next=fast,
        slow_prev=slow,
        slow_next=slow,
        symbolic_prev=symbolic_empty,
        symbolic_next=symbolic_empty,
    )

    assert abs(delta) < 1e-9
