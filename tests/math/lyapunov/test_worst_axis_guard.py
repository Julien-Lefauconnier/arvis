# tests/math/lyapunov/test_worst_axis_guard.py
"""The mean must not average away a saturated axis (DM3, MATH-A M4).

V is a convex combination of four axes, so a single catastrophic axis
is diluted by a factor of four: risk=1.0 with everything else at zero
gave V=0.25, far under the 0.8 mean threshold, and the gate answered
REQUIRE_CONFIRMATION at worst (audit M3). The worst-axis guard refuses
when any single axis reaches saturation (0.95 by default), whatever
the mean says. It is a strictly monotone hardening: it can only turn
non-ABSTAIN verdicts into ABSTAIN.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov_gate import (
    LyapunovGateParams,
    LyapunovVerdict,
    lyapunov_gate,
)

_CALM = LyapunovState(0.0, 0.0, 0.0, 0.0)


def test_saturated_risk_axis_refuses_despite_low_mean() -> None:
    verdict = lyapunov_gate(previous=_CALM, current=LyapunovState(0.0, 1.0, 0.0, 0.0))
    assert verdict is LyapunovVerdict.ABSTAIN, (
        "risk=1.0 alone means V=0.25: the mean threshold never fires, "
        f"the worst-axis guard must (got {verdict})"
    )


def test_each_axis_triggers_the_guard() -> None:
    for axis in range(4):
        values = [0.0, 0.0, 0.0, 0.0]
        values[axis] = 1.0
        verdict = lyapunov_gate(previous=_CALM, current=LyapunovState(*values))
        assert verdict is LyapunovVerdict.ABSTAIN, f"axis {axis} not guarded"


def test_below_saturation_the_guard_stays_out_of_the_way() -> None:
    verdict = lyapunov_gate(
        previous=LyapunovState(0.0, 0.9, 0.0, 0.0),
        current=LyapunovState(0.0, 0.94, 0.0, 0.0),
    )
    assert verdict is not LyapunovVerdict.ABSTAIN, (
        "0.94 is under the saturation threshold; the guard must not "
        "widen beyond its documented level"
    )


def test_guard_threshold_is_tunable() -> None:
    params = LyapunovGateParams(axis_abstain_threshold=0.5)
    verdict = lyapunov_gate(
        previous=_CALM,
        current=LyapunovState(0.0, 0.6, 0.0, 0.0),
        params=params,
    )
    assert verdict is LyapunovVerdict.ABSTAIN


_unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


@given(b=_unit, r=_unit, u=_unit, g=_unit, pb=_unit, pr=_unit, pu=_unit, pg=_unit)
def test_guard_is_strictly_monotone_hardening(
    b: float,
    r: float,
    u: float,
    g: float,
    pb: float,
    pr: float,
    pu: float,
    pg: float,
) -> None:
    """Disabling the guard never yields a stricter verdict than having
    it on: the guard only maps verdicts to ABSTAIN, never the reverse."""
    prev = LyapunovState(pb, pr, pu, pg)
    cur = LyapunovState(b, r, u, g)
    with_guard = lyapunov_gate(previous=prev, current=cur)
    without_guard = lyapunov_gate(
        previous=prev,
        current=cur,
        params=LyapunovGateParams(axis_abstain_threshold=1.1),
    )
    if with_guard != without_guard:
        assert with_guard is LyapunovVerdict.ABSTAIN
        assert max(b, r, u, g) >= LyapunovGateParams().axis_abstain_threshold
