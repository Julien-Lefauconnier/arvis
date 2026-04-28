# arvis/kernel/projection/validator.py

from __future__ import annotations

from typing import Any

from .certificate import (
    ProjectionCertificate,
    ProjectionCertificationLevel,
)
from .domain import ProjectionDomain


class ProjectionValidator:
    """
    Transforme une projection brute en certificat runtime.
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
        projected: dict[str, Any],
        previous_projected: dict[str, Any] | None = None,
        ctx: Any | None = None,
    ) -> ProjectionCertificate:
        domain_valid, checks_detail = self.domain.validate(projected)
        margin = self.domain.margin_to_boundary(projected)

        # --- boundedness ---
        boundedness_ok = domain_valid

        # --- lipschitz approx ---
        local_lipschitz = None
        lipschitz_ok = True

        if previous_projected is not None:
            try:
                delta = sum(
                    abs(
                        float(projected.get(k, 0)) - float(previous_projected.get(k, 0))
                    )
                    for k in projected
                    if isinstance(projected.get(k), (int, float))
                )
                local_lipschitz = delta
                lipschitz_ok = delta <= self.lipschitz_threshold
            except Exception:
                lipschitz_ok = False

        # --- noise robustness (placeholder simple) ---
        noise_gain = None
        noise_robustness_ok = True

        # TODO: brancher sur un vrai estimateur plus tard
        # pour l'instant on assume OK si domain OK
        noise_robustness_ok = domain_valid

        # --- mode stability ---
        mode_stability_ok = True  # placeholder

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
            except Exception:
                lyapunov_ok = False
                checks_detail["lyapunov_check_error"] = False

        # --- certification level ---
        if not domain_valid:
            level = ProjectionCertificationLevel.NONE
        elif all(
            [
                boundedness_ok,
                lipschitz_ok,
                noise_robustness_ok,
                mode_stability_ok,
                lyapunov_ok,
            ]
        ):
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
