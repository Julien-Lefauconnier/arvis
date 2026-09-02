# tests/math/projection/test_pi_operator_drift_reaction.py
"""Campaign PROJ, RED-first: the projection operator does not react
to the drift score.

The operator's "stability feedback control" read the private
``ctx._dv`` attribute as a signed energy derivative and clamped its
blending strength (``alpha = min(alpha, 0.6)``) whenever the value
was positive. Campaign ALLOW established what that attribute
actually carries: ``float(core_ctx.drift_score)``, a ``DriftSignal``
magnitude clamped to [0, 1], never negative. The clamp therefore
fired on every turn with any drift at all (85 per cent of campaign 2
turns) in the name of a divergence that was never measured, and the
"light (almost identity)" alpha = 1.0 branch was reachable only on
the turns whose drift was exactly zero.

DM-P1 removes the reaction outright rather than reinterpreting the
thresholds against the magnitude: the signal the branch wants (a
signed derivative) does not exist at projection time, the corpus
measurement shows a magnitude reinterpretation at the declared
``is_high`` threshold would never fire (maximum observed drift
0.283), and inventing new unregistered constants is exactly what
this repository avoids. Drift-reactive projection strength is
re-posed at DM4 with a real signal.

Measured on both M10 corpora before pinning: removing the reaction
changes no verdict (distributions bit-identical), leaves both
registered judgments unchanged, and removes about 20 spurious
``projection_boundary`` flags per corpus.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.math.projection.pi_operator import PiOperator


def _ctx(
    dv: float | None,
    *,
    valid: bool = True,
    regime: str = "stable",
) -> SimpleNamespace:
    """Duck context shaped like the canonical scientific nesting the
    operator actually reads (ctx.scientific.adaptive.*)."""
    ctx = SimpleNamespace(
        scientific=SimpleNamespace(
            adaptive=SimpleNamespace(
                validity_envelope=SimpleNamespace(valid=valid),
                adaptive_snapshot=SimpleNamespace(regime=regime),
            )
        )
    )
    if dv is not None:
        ctx._dv = dv
    return ctx


def test_drift_alone_does_not_change_the_operated_view() -> None:
    """The regression: an ordinary positive drift must not contract
    the view. The drift score is a magnitude, not a divergence."""
    pi = PiOperator()
    view = {"x": 10.0}

    with_drift = pi.project(view, _ctx(dv=0.5))
    without_signal = pi.project(view, _ctx(dv=None))

    assert with_drift.to_dict() == without_signal.to_dict()


def test_a_zero_drift_turn_is_not_a_special_case_anymore() -> None:
    """Before the fix, drift == 0.0 was the only value that reached
    alpha = 1.0. Now every drift value takes the same path."""
    pi = PiOperator()
    view = {"x": 10.0}

    zero = pi.project(view, _ctx(dv=0.0))
    small = pi.project(view, _ctx(dv=0.05))
    large = pi.project(view, _ctx(dv=0.999))

    assert zero.to_dict() == small.to_dict() == large.to_dict()


def test_the_envelope_and_regime_reactions_are_untouched() -> None:
    """What the operator still reacts to: an invalid envelope
    contracts hardest, a critical regime contracts moderately, and
    both contract more than the healthy path."""
    pi = PiOperator()
    view = {"x": 10.0}

    healthy = pi.project(view, _ctx(dv=None)).to_dict()["x"]
    critical = pi.project(view, _ctx(dv=None, regime="critical")).to_dict()["x"]
    invalid = pi.project(view, _ctx(dv=None, valid=False)).to_dict()["x"]

    assert invalid < critical < healthy


def test_the_final_safety_squash_still_bounds_every_value() -> None:
    """Removing the drift reaction removes nothing of the kernel
    invariant: the operated view stays strictly inside (-1, 1)."""
    pi = PiOperator()

    projected = pi.project({"a": 1000.0, "b": -1000.0}, _ctx(dv=0.5))

    for value in projected.to_dict().values():
        assert -1.0 < value < 1.0
