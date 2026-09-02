# tests/math/stability/test_validity_envelope_adaptive.py
"""The validity envelope refuses an absent adaptive layer and carries
the measured switching verdict.

Campaign GATE-SEM (LOT G2 / DM-G2, audit P0-1 and P1-5, 2026-09-02).
Before this campaign the envelope returned ``valid=True`` with
``adaptive_available=False`` (a missing certification axis certified
nothing and invalidated nothing), and in the soft switching posture
it published ``switching_safe: True`` on turns whose measured T1
condition was False, with no trace of the measurement.
ARVIS_VALIDITY_ENVELOPE_SPEC_V1.md section 6 had already reserved the
``adaptive_unavailable`` mapping this change activates.
"""

from __future__ import annotations

from arvis.math.stability.validity_envelope import build_validity_envelope


def _build(**overrides: object) -> object:
    base: dict[str, object] = dict(
        projection_available=True,
        switching_safe=True,
        exponential_safe=True,
        kappa_safe=True,
        adaptive_available=True,
        adaptive_band="stable",
    )
    base.update(overrides)
    return build_validity_envelope(**base)  # type: ignore[arg-type]


def test_absent_adaptive_layer_invalidates_the_envelope() -> None:
    """RED on the pre-campaign tree: this envelope came back valid."""
    env = _build(adaptive_available=False)

    assert env.valid is False
    assert env.reason == "adaptive_unavailable"


def test_adaptive_refusal_ranks_below_the_harder_axes() -> None:
    env = _build(adaptive_available=False, kappa_safe=False)

    assert env.valid is False
    assert env.reason == "kappa_violation"


def test_measured_switching_travels_beside_the_effective_value() -> None:
    """A soft posture feeds effective True; the envelope now also
    carries what was actually measured."""
    env = _build(switching_safe=True, switching_safe_measured=False)

    assert env.switching_safe is True
    assert env.switching_safe_measured is False


def test_fully_certified_envelope_stays_valid() -> None:
    env = _build(switching_safe_measured=True)

    assert env.valid is True
    assert env.reason is None
    assert env.switching_safe_measured is True
