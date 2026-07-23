# arvis/kernel/projection/validator.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from arvis.math.projection.projection_view import ProjectionView

from .certificate import (
    ProjectionCertificate,
    ProjectionCertificationLevel,
)
from .domain import ProjectionDomain


class ProjectionValidator:
    """Turn a raw projection into a runtime certificate.

    Two of the six certificate axes are NOT assessed here. Noise robustness has
    no estimator and reuses domain validity as a conservative monotonic proxy;
    mode stability examines nothing at all. Both are recorded as unassessed in
    ``checks_detail`` and are excluded from the certification level, so a LOCAL
    certificate only ever attests axes that were actually measured.

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
        lyapunov_ok = True
        if ctx is not None:
            try:
                delta_w = getattr(ctx, "delta_w", None)
                dv = getattr(ctx, "_dv", None)

                if delta_w is not None:
                    lyapunov_ok = float(delta_w) <= self.lyapunov_positive_threshold
                    checks_detail["lyapunov_delta_w_non_positive"] = lyapunov_ok
                elif dv is not None:
                    lyapunov_ok = float(dv) <= self.lyapunov_positive_threshold
                    checks_detail["lyapunov_dv_non_positive"] = lyapunov_ok
                else:
                    checks_detail["lyapunov_signal_available"] = False
                    lyapunov_ok = True
            except (TypeError, ValueError, OverflowError):
                lyapunov_ok = False
                checks_detail["lyapunov_check_error"] = False

        # --- certification level ---
        # Computed over the axes this validator actually measures. The two
        # unassessed axes are deliberately excluded: certifying on an axis that
        # was never evaluated would overstate what the certificate attests.
        # Behaviour is unchanged today, since both hold whenever domain_valid
        # does, and domain_valid is the only branch that reaches here.
        if not domain_valid:
            level = ProjectionCertificationLevel.NONE
        elif all([boundedness_ok, lipschitz_ok, lyapunov_ok]):
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
