# tests/kernel/projection/test_domain_danger_bounds.py
"""DM-F3 (campaign FIX): the domain margin measures proximity to the
DANGEROUS bounds only.

The margin was ``min(value - min, max - value)`` over every axis, so
an axis sitting at its HEALTHY extreme counted as boundary
proximity. ``risk.conflict_pressure`` is fed by the collapse risk,
whose healthy value is exactly 0.0, its lower bound: every healthy
turn measured a margin of 0.0, fired ``projection_boundary`` and was
floored at REQUIRE_CONFIRMATION. That is the structural reason ALLOW
never appeared, in the quickstart or across the 3072 turns of the
two M10 campaigns.

Bounds now declare which side is dangerous; both remain dangerous by
default, so any undeclared axis keeps the historical behavior.
"""

from __future__ import annotations

from arvis.kernel.projection.domain import NumericBounds, ProjectionDomain


def test_healthy_extreme_is_not_boundary_proximity() -> None:
    """A risk axis at zero risk is the safest possible state, not a
    domain edge."""
    bounds = NumericBounds(0.0, 100.0, danger_low=False)

    assert bounds.margin(0.0) > 0.1
    # the dangerous side still measures normally
    assert bounds.margin(99.95) < 0.1


def test_both_bounds_dangerous_by_default() -> None:
    bounds = NumericBounds(0.0, 1.0)

    assert bounds.margin(0.0) == 0.0
    assert bounds.margin(1.0) == 0.0
    assert bounds.margin(0.5) == 0.5


def test_a_coherence_axis_is_dangerous_when_low() -> None:
    """Full coherence (1.0) is healthy; incoherence (0.0) is the
    danger."""
    bounds = NumericBounds(0.0, 1.0, danger_high=False)

    assert bounds.margin(1.0) > 0.1
    assert bounds.margin(0.02) < 0.1


def test_out_of_domain_stays_negative() -> None:
    bounds = NumericBounds(0.0, 1.0, danger_low=False)

    assert bounds.margin(1.5) == -1.0
    assert bounds.margin(-0.5) == -1.0


def test_domain_margin_ignores_healthy_extremes() -> None:
    """The whole point, at domain level: a healthy projected state
    keeps a usable margin instead of collapsing to zero."""
    domain = ProjectionDomain(
        bounds={
            "risk.conflict_pressure": NumericBounds(0.0, 100.0, danger_low=False),
            "state.coherence_score": NumericBounds(0.0, 1.0, danger_high=False),
            "trace.adaptive_kappa_eff": NumericBounds(0.0, 1.0),
        }
    )

    healthy = {
        "risk.conflict_pressure": 0.0,
        "state.coherence_score": 1.0,
        "trace.adaptive_kappa_eff": 0.4,
    }

    assert domain.margin_to_boundary(healthy) == 0.4


def test_an_axis_with_no_dangerous_end_is_fully_interior() -> None:
    """A purely informational axis (neither end dangerous) must not
    report boundary proximity anywhere inside its range; returning a
    zero margin there would floor every turn (MATH mutation replay of
    campaign FIX, survivor M2)."""
    bounds = NumericBounds(0.0, 100.0, danger_low=False, danger_high=False)

    assert bounds.margin(0.0) == 100.0
    assert bounds.margin(50.0) == 100.0
    assert bounds.margin(100.0) == 100.0
    assert bounds.margin(101.0) == -1.0

    degenerate = NumericBounds(5.0, 5.0, danger_low=False, danger_high=False)
    assert degenerate.margin(5.0) == 0.0


def test_the_bootstrapped_domain_declares_its_dangerous_ends() -> None:
    """The semantics only help if the axes keep their declaration
    (campaign FIX mutation replay, survivor M3): a healthy extreme
    silently re-declared dangerous would floor every healthy turn
    again, invisibly."""
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline

    bounds = CognitivePipeline().projection_domain.bounds

    # healthy extreme is the LOW end: zero tension, zero conflict
    for axis in ("state.system_tension", "risk.conflict_pressure"):
        assert bounds[axis].danger_low is False, axis
        assert bounds[axis].danger_high is True, axis

    # healthy extreme is the HIGH end: full coherence, high kappa
    for axis in ("state.coherence_score", "trace.adaptive_kappa_eff"):
        assert bounds[axis].danger_high is False, axis
        assert bounds[axis].danger_low is True, axis

    # both ends matter: no control and saturated control
    control = bounds["control.control_signal"]
    assert control.danger_low is True and control.danger_high is True
