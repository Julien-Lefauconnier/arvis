# tests/math/test_projection_real_lyapunov_compatibility.py

import math

import pytest

from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.cognition.projection.projection_api import Observation, project_observation
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.lyapunov import LyapunovState, lyapunov_value
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.lyapunov.target_map import target_map
from tests.fixtures.projection_cases import (
    boundary_case,
    high_risk_case,
    noisy_case,
    nominal_case,
)


def _pad_or_truncate(values: tuple[float, ...], size: int, fill: float = 0.0) -> tuple[float, ...]:
    seq = tuple(float(v) for v in values)
    if len(seq) >= size:
        return seq[:size]
    return seq + (fill,) * (size - len(seq))


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _fast_state_from_projection(proj) -> LyapunovState:
    """
    Adapter from projection x -> LyapunovState.

    The current projection API does not yet expose a theorem-native fast state,
    so we build a safe 4D adapter:
    - truncate/pad to 4 dims,
    - clamp to [0,1] because LyapunovState expects normalized signals.
    """
    x4 = _pad_or_truncate(proj.x, 4, fill=0.0)
    x4 = tuple(_clamp01(v) for v in x4)
    return LyapunovState(*x4)


def _slow_state_from_projection(proj) -> SlowState:
    """
    Adapter from projection z -> SlowState.
    """
    z4 = _pad_or_truncate(proj.z, 4, fill=0.0)
    return SlowState(*z4)


def _symbolic_state_from_mode(mode: str) -> SymbolicState:
    """
    Minimal symbolic anchor compatible with target_map(symbolic, fast=...).

    This is intentionally simple and deterministic:
    - the current projection API only returns q,
    - so we derive a stable symbolic surrogate from q.
    """
    if mode == "nominal":
        gate_verdict = "ALLOW"
        conversation_mode = "normal"
        intent_confidence = 0.2
    elif mode == "alert":
        gate_verdict = "REVIEW"
        conversation_mode = "cautious"
        intent_confidence = 0.5
    else:
        gate_verdict = "BLOCK"
        conversation_mode = "restricted"
        intent_confidence = 0.8

    return SymbolicState(
        intent_type=mode,
        intent_confidence=intent_confidence,
        gate_verdict=gate_verdict,
        conversation_mode=conversation_mode,
        conflict_histogram={},
        conflict_severity=0.0,
        override_count=0,
        override_rate=0.0,
    )


@pytest.fixture
def comp() -> CompositeLyapunov:
    return CompositeLyapunov()


@pytest.mark.parametrize(
    "case_fn",
    [
        nominal_case,
        high_risk_case,
        boundary_case,
        noisy_case,
    ],
)
def test_real_composite_lyapunov_is_finite_and_defined(case_fn, comp: CompositeLyapunov):
    obs = case_fn()
    proj = project_observation(obs)

    fast = _fast_state_from_projection(proj)
    slow = _slow_state_from_projection(proj)
    symbolic = _symbolic_state_from_mode(proj.q)

    W = comp.W(fast=fast, slow=slow, symbolic=symbolic)

    assert not math.isnan(W)
    assert not math.isinf(W)
    assert W >= 0.0


def test_real_composite_lyapunov_remains_defined_on_invalid_input(comp: CompositeLyapunov):
    obs = Observation(
        numeric_signals={"risk": "invalid"},
        structured_signals={},
        external_signals={},
    )

    proj = project_observation(obs)

    fast = _fast_state_from_projection(proj)
    slow = _slow_state_from_projection(proj)
    symbolic = _symbolic_state_from_mode(proj.q)

    W = comp.W(fast=fast, slow=slow, symbolic=symbolic)

    assert not math.isnan(W)
    assert not math.isinf(W)
    assert W >= 0.0


def test_real_composite_lyapunov_equals_fast_energy_on_target_manifold(comp: CompositeLyapunov):
    """
    Sanity check against the true ARVIS structure:
    if slow == target_map(symbolic, fast), then the mismatch term is zero and
    W should collapse to the fast Lyapunov energy.
    """
    proj = project_observation(nominal_case())

    fast = _fast_state_from_projection(proj)
    symbolic = _symbolic_state_from_mode(proj.q)

    T = target_map(symbolic, fast=fast)
    slow_eq = SlowState(*tuple(float(v) for v in T))

    W = comp.W(fast=fast, slow=slow_eq, symbolic=symbolic)
    V = lyapunov_value(fast)

    assert abs(W - V) < 1e-6


def test_real_composite_delta_W_is_finite_under_small_perturbation(comp: CompositeLyapunov):
    base_obs = nominal_case()
    next_obs = Observation(
        numeric_signals={k: float(v) + 0.01 for k, v in base_obs.numeric_signals.items()},
        structured_signals=base_obs.structured_signals,
        external_signals=base_obs.external_signals,
    )

    prev_proj = project_observation(base_obs)
    next_proj = project_observation(next_obs)

    fast_prev = _fast_state_from_projection(prev_proj)
    fast_next = _fast_state_from_projection(next_proj)

    slow_prev = _slow_state_from_projection(prev_proj)
    slow_next = _slow_state_from_projection(next_proj)

    symbolic_prev = _symbolic_state_from_mode(prev_proj.q)
    symbolic_next = _symbolic_state_from_mode(next_proj.q)

    delta = comp.delta_W(
        fast_prev=fast_prev,
        fast_next=fast_next,
        slow_prev=slow_prev,
        slow_next=slow_next,
        symbolic_prev=symbolic_prev,
        symbolic_next=symbolic_next,
    )

    assert not math.isnan(delta)
    assert not math.isinf(delta)


def test_real_composite_lyapunov_varies_smoothly_under_small_perturbation(comp: CompositeLyapunov):
    base_obs = nominal_case()
    base_proj = project_observation(base_obs)

    fast_base = _fast_state_from_projection(base_proj)
    slow_base = _slow_state_from_projection(base_proj)
    symbolic_base = _symbolic_state_from_mode(base_proj.q)

    W_base = comp.W(fast=fast_base, slow=slow_base, symbolic=symbolic_base)

    variations = []

    for eps in (0.001, 0.005, 0.01):
        perturbed = Observation(
            numeric_signals={k: float(v) + eps for k, v in base_obs.numeric_signals.items()},
            structured_signals=base_obs.structured_signals,
            external_signals=base_obs.external_signals,
        )
        proj = project_observation(perturbed)

        fast = _fast_state_from_projection(proj)
        slow = _slow_state_from_projection(proj)
        symbolic = _symbolic_state_from_mode(proj.q)

        W = comp.W(fast=fast, slow=slow, symbolic=symbolic)
        variations.append(abs(W - W_base))

    max_var = max(variations)

    # Conservative threshold: we only want to rule out violent discontinuity.
    assert max_var < 5.0


def test_real_composite_lyapunov_fast_only_fallback_is_defined(comp: CompositeLyapunov):
    proj = project_observation(high_risk_case())
    fast = _fast_state_from_projection(proj)

    W = comp.W(fast=fast, slow=None, symbolic=None)

    assert not math.isnan(W)
    assert not math.isinf(W)
    assert W >= 0.0


def test_real_composite_small_gain_sanity(comp: CompositeLyapunov):
    """
    Not a projection test strictly speaking, but a minimal integration sanity check:
    the real CompositeLyapunov still exposes the small-gain guard used by the core.
    """
    assert comp.check_small_gain(eta=0.05) is True
    assert comp.check_small_gain(eta=0.5, alpha=0.1, L_T=2.0) is False