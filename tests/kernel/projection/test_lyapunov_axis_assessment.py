# tests/kernel/projection/test_lyapunov_axis_assessment.py
"""Campaign ALLOW, RED-first: the certificate never reads the drift
score as a Lyapunov derivative.

The validator assessed ``lyapunov_compatibility_ok`` against the
composite energy delta, and fell back to the private ``ctx._dv``
attribute when that delta was absent. Two facts made the fallback a
defect rather than a degraded mode:

* ``ctx._dv`` holds ``float(core_ctx.drift_score)``, and
  ``DriftSignal.__post_init__`` stores ``clamp01(abs(value))``. The
  value is therefore in [0, 1] and never negative, so the comparison
  ``dv <= 1e-9`` could only hold when drift was exactly zero. Any
  drift at all produced a declared Lyapunov incompatibility.
* ``composite.delta_w`` is written by the gate stage, which runs
  after the projection stage. At the moment the certificate the gate
  consumes is built, the delta is always ``None``, so the fallback
  was not an edge case: it was the branch taken on every certified
  turn.

Measured on the D-2.0 campaign before the fix: 1270 turns carrying
``projection_unsafe`` and ``projection_lyapunov_incompatible``, 1394
carrying ``validity_projection_unavailable``, and zero final ALLOW
across both M10 campaigns.

An axis that cannot be measured at this point in the pipeline is
reported unassessed, which is the treatment noise robustness and mode
stability already receive (see test_unassessed_projection_axes.py).
It is not reported as a measured violation.
"""

from __future__ import annotations

from arvis.kernel.pipeline.context.scientific_context import (
    PipelineScientificContext,
)
from arvis.kernel.projection.certificate import ProjectionCertificationLevel
from arvis.kernel.projection.validator import ProjectionValidator
from arvis.math.signals.drift import DriftSignal


class _AlwaysValidDomain:
    def validate(self, projected):
        return True, {}

    def margin_to_boundary(self, projected):
        return 1.0


def _validator() -> ProjectionValidator:
    return ProjectionValidator(domain=_AlwaysValidDomain())


class _DriftOnlyCtx:
    """A context at projection time: drift measured, composite delta
    not yet written by the gate stage."""

    def __init__(self, drift: float) -> None:
        self.scientific = PipelineScientificContext()
        self._dv = float(DriftSignal(drift))


def test_the_drift_signal_can_never_be_negative() -> None:
    """The premise of the defect, pinned so it cannot drift: the
    fallback compared a clamped magnitude against a threshold that
    only a signed derivative could satisfy."""
    assert float(DriftSignal(-0.4)) == 0.4
    assert float(DriftSignal(0.4)) == 0.4
    assert float(DriftSignal(9.0)) == 1.0


def test_drift_alone_is_not_a_declared_lyapunov_incompatibility() -> None:
    """The regression: an ordinary turn with ordinary drift and no
    composite delta yet must not be certified incompatible."""
    certificate = _validator().validate({"x": 0.1}, ctx=_DriftOnlyCtx(0.5))

    assert certificate.lyapunov_compatibility_ok is True


def test_an_unmeasurable_axis_is_reported_unassessed() -> None:
    """Reported, not silently dropped: a consumer can tell an axis
    that held from an axis that was never evaluated."""
    certificate = _validator().validate({"x": 0.1}, ctx=_DriftOnlyCtx(0.5))

    assert certificate.checks_detail["lyapunov_compatibility_assessed"] is False
    assert "lyapunov_dv_non_positive" not in certificate.checks_detail


def test_drift_no_longer_costs_the_local_certification() -> None:
    """The certification level covers the axes actually measured, so
    an unassessed axis neither grants nor withdraws certification."""
    certificate = _validator().validate({"x": 0.1}, ctx=_DriftOnlyCtx(0.5))

    assert certificate.certification_level is ProjectionCertificationLevel.LOCAL


def test_a_present_composite_delta_is_still_assessed() -> None:
    """The real signal keeps its full effect in both directions."""
    validator = _validator()

    contracting = _DriftOnlyCtx(0.5)
    contracting.scientific.composite.delta_w = -0.2
    expanding = _DriftOnlyCtx(0.0)
    expanding.scientific.composite.delta_w = 0.2

    ok = validator.validate({"x": 0.1}, ctx=contracting)
    violated = validator.validate({"x": 0.1}, ctx=expanding)

    assert ok.lyapunov_compatibility_ok is True
    assert ok.checks_detail["lyapunov_compatibility_assessed"] is True
    assert violated.lyapunov_compatibility_ok is False
    assert violated.checks_detail["lyapunov_compatibility_assessed"] is True
    assert violated.certification_level is ProjectionCertificationLevel.BASIC


def test_the_composite_delta_wins_over_any_private_attribute() -> None:
    """No private-attribute path may soften a measured violation."""
    ctx = _DriftOnlyCtx(0.0)
    ctx.scientific.composite.delta_w = 0.2

    certificate = _validator().validate({"x": 0.1}, ctx=ctx)

    assert certificate.lyapunov_compatibility_ok is False


def test_a_projection_with_no_context_assesses_nothing() -> None:
    """Without a context there is no signal at all, and the axis says
    so rather than defaulting to a silent pass."""
    certificate = _validator().validate({"x": 0.1})

    assert certificate.checks_detail["lyapunov_compatibility_assessed"] is False
    assert certificate.lyapunov_compatibility_ok is True


def test_a_present_but_uncoercible_delta_fails_closed() -> None:
    """The distinction that keeps the unassessed path from becoming a
    hole: an ABSENT signal is unassessed and conservative, a PRESENT
    signal that cannot be read is a failure to measure something that
    was there, and F-002 keeps it fail-closed.

    Added after mutation replay, where turning this branch into a
    relaxation survived every other pin.
    """
    ctx = _DriftOnlyCtx(0.0)
    ctx.scientific.composite.delta_w = "not a number"  # type: ignore[assignment]

    certificate = _validator().validate({"x": 0.1}, ctx=ctx)

    assert certificate.lyapunov_compatibility_ok is False
    assert certificate.checks_detail["lyapunov_compatibility_assessed"] is True
    assert certificate.certification_level is ProjectionCertificationLevel.BASIC
