# arvis/kernel/projection/validator.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from arvis.kernel.pipeline.context.scientific_accessors import (
    delta_w as delta_w_of,
)
from arvis.math.projection.projection_view import ProjectionView

from .certificate import (
    ProjectionCertificate,
    ProjectionCertificationLevel,
)
from .domain import ProjectionDomain


class ProjectionValidator:
    """Turn a raw projection into a runtime certificate.

    Three of the six certificate axes may go unassessed here. Noise robustness
    has no estimator and reuses domain validity as a conservative monotonic
    proxy; mode stability examines nothing at all; Lyapunov compatibility is
    assessed only when a composite energy delta is available on the context,
    which on the pre-gate certificate it never is. All three are recorded as
    unassessed in ``checks_detail`` and are excluded from the certification
    level, so a LOCAL certificate only ever attests axes that were actually
    measured.

    An unassessed axis reports its conservative value and says so. It is never
    reported as a measured violation: doing that with the drift score standing
    in for the energy delta is precisely the defect campaign ALLOW closed.

    This is a bounded, declared limitation, not a hidden one: see the guarantee
    scope published with the release.
    """

    def __init__(
        self,
        domain: ProjectionDomain,
        lipschitz_threshold: float = 10.0,
        noise_threshold: float = 5.0,
        lyapunov_positive_threshold: float = 1e-9,
    ) -> None:
        self.domain = domain
        self.lipschitz_threshold = lipschitz_threshold
        self.noise_threshold = noise_threshold
        self.lyapunov_positive_threshold = lyapunov_positive_threshold

    def validate(
        self,
        projected: ProjectionView | Mapping[str, float],
        previous_projected: ProjectionView | Mapping[str, float] | None = None,
        ctx: Any | None = None,
    ) -> ProjectionCertificate:
        if not isinstance(projected, ProjectionView):
            projected = ProjectionView.from_mapping(projected)

        if previous_projected is not None and not isinstance(
            previous_projected, ProjectionView
        ):
            previous_projected = ProjectionView.from_mapping(previous_projected)
        domain_valid, checks_detail = self.domain.validate(projected.to_dict())
        margin = self.domain.margin_to_boundary(projected.to_dict())

        # --- boundedness ---
        boundedness_ok = domain_valid

        # --- lipschitz approx ---
        local_lipschitz = None
        lipschitz_ok = True

        if previous_projected is not None:
            try:
                delta = 0.0

                for k in projected.keys():
                    current = projected.get(k, 0.0)
                    previous = previous_projected.get(k, 0.0)

                    if isinstance(current, (int, float)) and isinstance(
                        previous,
                        (int, float),
                    ):
                        delta += abs(float(current) - float(previous))
                local_lipschitz = delta
                lipschitz_ok = delta <= self.lipschitz_threshold
            except (AttributeError, TypeError, ValueError, OverflowError):
                lipschitz_ok = False

        # --- noise robustness: NOT ASSESSED ---
        # Nothing here estimates a noise gain. Domain validity is reused as a
        # conservative monotonic proxy, which is why noise_gain_estimate stays
        # None: there is no measurement behind this value and it must not be
        # read as a bound. The axis is flagged unassessed below.
        noise_gain = None
        noise_robustness_ok = domain_valid
        checks_detail["noise_robustness_assessed"] = False

        # --- mode stability: NOT ASSESSED ---
        # No mode transition is examined at this point.
        mode_stability_ok = True
        checks_detail["mode_stability_assessed"] = False

        # --- lyapunov compatibility ---
        # Assessed against the composite energy delta, and against
        # nothing else. This branch used to fall back to the private
        # ``ctx._dv`` attribute whenever that delta was absent, which
        # was a defect on two counts (campaign ALLOW):
        #
        # ``ctx._dv`` carries ``float(core_ctx.drift_score)``, and
        # ``DriftSignal`` stores ``clamp01(abs(value))``. A clamped
        # magnitude in [0, 1] is never negative, so ``dv <= 1e-9`` held
        # only when drift was exactly zero: any drift at all was
        # reported as a measured Lyapunov incompatibility. And the gate
        # stage writes ``composite.delta_w`` after the projection stage
        # runs, so on the certificate the gate actually consumes the
        # delta is always None and the fallback was the branch taken
        # every time, not an edge case.
        #
        # An axis this validator cannot measure at this point is
        # reported unassessed, exactly as noise robustness and mode
        # stability already are, and excluded from the certification
        # level. Assessing it for real would mean making the composite
        # delta available before certification, which is a pipeline
        # ordering change with a far wider blast radius.
        lyapunov_ok = True
        lyapunov_assessed = False
        if ctx is not None:
            try:
                delta_w = delta_w_of(ctx)

                if delta_w is not None:
                    lyapunov_ok = float(delta_w) <= self.lyapunov_positive_threshold
                    lyapunov_assessed = True
                    checks_detail["lyapunov_delta_w_non_positive"] = lyapunov_ok
            except (TypeError, ValueError, OverflowError):
                # A signal that is present but uncoercible is a failure
                # to measure something that was there, not an absence:
                # it stays fail-closed (F-002).
                lyapunov_ok = False
                lyapunov_assessed = True
                checks_detail["lyapunov_check_error"] = False

        checks_detail["lyapunov_compatibility_assessed"] = lyapunov_assessed

        # --- certification level ---
        # Computed over the axes this validator actually measures. The
        # unassessed axes are deliberately excluded: certifying on an axis that
        # was never evaluated would overstate what the certificate attests, and
        # withdrawing certification over one would understate it just as badly.
        # Lyapunov compatibility joins that rule whenever no composite delta is
        # available to assess it against.
        assessed_axes = [boundedness_ok, lipschitz_ok]

        if lyapunov_assessed:
            assessed_axes.append(lyapunov_ok)

        if not domain_valid:
            level = ProjectionCertificationLevel.NONE
        elif all(assessed_axes):
            level = ProjectionCertificationLevel.LOCAL
        else:
            level = ProjectionCertificationLevel.BASIC

        return ProjectionCertificate(
            domain_valid=domain_valid,
            boundedness_ok=boundedness_ok,
            lipschitz_ok=lipschitz_ok,
            noise_robustness_ok=noise_robustness_ok,
            mode_stability_ok=mode_stability_ok,
            lyapunov_compatibility_ok=lyapunov_ok,
            margin_to_boundary=margin,
            local_lipschitz_estimate=local_lipschitz,
            noise_gain_estimate=noise_gain,
            certification_level=level,
            checks_detail=checks_detail,
        )
