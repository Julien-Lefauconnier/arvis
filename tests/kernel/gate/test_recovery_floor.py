# tests/kernel/gate/test_recovery_floor.py
"""The stage-side recovery detector requires a real improvement.

Campaign GATE-SEM (LOT G4 / DM-G4, audit P0-2 bis, 2026-09-02).
Recovery feeds the sanctioned ABSTAIN -> REQUIRE_CONFIRMATION
relaxation (recovery_to_confirmation), so its trigger must not be
satisfiable by floating-point noise. The kernel-side detector applied
RECOVERY_MIN_IMPROVEMENT since audit G2; the stage-side detector in
composite.py accepted any negative delta down to -1e-18 and is OR-ed
with the kernel's in the decision stack, so the floor was void on the
live path. Probed on the pre-campaign tree: delta_w = -1e-18 promoted
ABSTAIN to REQUIRE_CONFIRMATION through the stage detector.
"""

from __future__ import annotations

from arvis.kernel.pipeline.stages.gate.composite import detect_recovery
from arvis.math.gate.gate_kernel import RECOVERY_MIN_IMPROVEMENT
from tests.fixtures.builders.context_builder import build_test_context


def test_noise_delta_is_not_recovery() -> None:
    """RED on the pre-campaign tree: -1e-18 detected as recovery."""
    ctx = build_test_context()

    assert detect_recovery(ctx, delta_w=-1e-18, w_prev=None, w_current=None) is False


def test_real_delta_is_recovery() -> None:
    ctx = build_test_context()

    assert detect_recovery(ctx, delta_w=-0.05, w_prev=None, w_current=None) is True


def test_floor_boundary_is_exclusive() -> None:
    ctx = build_test_context()

    at_floor = detect_recovery(
        ctx,
        delta_w=-RECOVERY_MIN_IMPROVEMENT,
        w_prev=None,
        w_current=None,
    )
    assert at_floor is False

    past_floor = detect_recovery(
        ctx,
        delta_w=-RECOVERY_MIN_IMPROVEMENT * 1.5,
        w_prev=None,
        w_current=None,
    )
    assert past_floor is True


def test_composite_energy_comparison_uses_the_same_floor() -> None:
    """RED on the pre-campaign tree: a 1e-12 energy dip qualified."""
    ctx = build_test_context()

    noise = detect_recovery(ctx, delta_w=None, w_prev=1.0, w_current=1.0 - 1e-12)
    assert noise is False

    real = detect_recovery(ctx, delta_w=None, w_prev=1.0, w_current=0.9)
    assert real is True
