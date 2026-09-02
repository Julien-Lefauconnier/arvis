# tests/math/stability/test_weak_stability_policy.py
"""Campaign SEUIL, RED-first: the weak-stability floor is a measured
contraction RATE, not an absolute step.

``delta_w_soft_threshold`` lived as ``getattr(ctx, ..., -0.05)``, a
constant wearing a configuration costume (nothing in the repository
or its tests ever set the attribute). The -0.05 was conventional, and
the M10 corpora measured what it actually did: the
``nominal_feedback`` family, engineered to contract on every turn
(p_contraction 1.000), converges geometrically, so its late steps are
small (median |dW| 0.004) and the family got ZERO ALLOW. A floor
demanding a big step refuses the one family that provably contracts
by design.

DM-S1, registered by the owner on 2026-09-02 before the campaign run:
the threshold becomes a rate,

    weak if |delta_w| < max(0.05 * W_current, 0.005)

5 per cent of the current energy (one third of the measured median
contraction rate 0.15), floored at 0.005 (bracketing the p05-p10 of
observed contractions) so a hovering system near W = 0 cannot pass on
noise. Candidates -0.01, -0.025 and keeping -0.05 were measured on
both full corpora before the choice; no candidate produced a single
ALLOW outside the nominal, long_horizon and feedback families, and
D-1.0's ABSTAIN count is bit-identical under every candidate, the
measured proof this filter never relaxes a refusal.
"""

from __future__ import annotations

from pytest import approx

from arvis.math.stability.weak_stability_policy import (
    WEAK_STABILITY_ABSOLUTE_FLOOR,
    WEAK_STABILITY_RATE,
    weak_stability_threshold,
)


def test_the_registered_constants_are_the_dm_s1_values() -> None:
    """The registration pin: these values were chosen from the
    measured dossier and registered before the campaign run. Changing
    them is a new registration, not a tweak."""
    assert WEAK_STABILITY_RATE == 0.05
    assert WEAK_STABILITY_ABSOLUTE_FLOOR == 0.005


def test_the_threshold_scales_with_the_current_energy() -> None:
    assert weak_stability_threshold(1.0) == approx(-0.05)
    assert weak_stability_threshold(0.4) == approx(-0.02)


def test_the_absolute_floor_holds_near_zero_energy() -> None:
    """A converged system hovering at tiny W cannot turn noise into a
    certified contraction."""
    assert weak_stability_threshold(0.0) == -0.005
    assert weak_stability_threshold(0.02) == -0.005
    assert weak_stability_threshold(None) == -0.005


def test_an_unreadable_energy_gets_the_floor() -> None:
    """Fail-safe: garbage in the energy channel degrades to the
    absolute floor, never to an exception or a free pass."""
    assert weak_stability_threshold("not a number") == -0.005  # type: ignore[arg-type]


def test_the_rate_semantics_in_one_sentence() -> None:
    """The defining contrast with the old absolute -0.05: the same
    small step is a real contraction on a small energy and noise on a
    large one."""
    small_step = -0.012

    threshold_small_energy = weak_stability_threshold(0.1)
    threshold_large_energy = weak_stability_threshold(0.5)

    # on W=0.1 the threshold is -0.01: a step of -0.012 is NOT weak
    assert not (threshold_small_energy < small_step < 0)
    # on W=0.5 the threshold is -0.025: the same step IS weak
    assert threshold_large_energy < small_step < 0
