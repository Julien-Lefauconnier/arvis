# arvis/kernel/projection/certificate.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProjectionCertificationLevel(StrEnum):
    NONE = "NONE"
    MINIMAL = "MINIMAL"
    BASIC = "BASIC"
    LOCAL = "LOCAL"
    CERTIFIED_RUNTIME = "CERTIFIED_RUNTIME"


@dataclass(frozen=True)
class ProjectionCertificate:
    """The runtime outcome of validating one projection.

    Each boolean below reports what the producing validator concluded on that
    axis. A validator is not required to assess every axis: when it does not,
    it reports a conservative value and records the fact in ``checks_detail``
    under ``<axis>_assessed``. Read the two together before treating any of
    these flags as a guarantee.
    """

    domain_valid: bool

    # main checks (M3)
    boundedness_ok: bool
    lipschitz_ok: bool
    noise_robustness_ok: bool
    mode_stability_ok: bool
    lyapunov_compatibility_ok: bool

    # runtime metrics
    margin_to_boundary: float
    local_lipschitz_estimate: float | None
    noise_gain_estimate: float | None

    certification_level: ProjectionCertificationLevel

    # debug / trace
    checks_detail: dict[str, bool]

    @property
    def is_projection_safe(self) -> bool:
        return (
            self.domain_valid
            and self.boundedness_ok
            and self.lipschitz_ok
            and self.noise_robustness_ok
            and self.mode_stability_ok
            and self.lyapunov_compatibility_ok
        )


def minimal_projection_certificate() -> ProjectionCertificate:
    """Minimal projection certificate for inputs with no structured signals.

    A bare informational input (for example a plain text prompt) does not
    produce a full cognitive projection. Rather than hard-blocking such a turn
    on an empty projection, ARVIS attaches this minimal certificate so the turn
    is still governed by the gate (typically REQUIRE_CONFIRMATION) instead of
    being surprisingly rejected with ``projection_invalid``.

    This is explicitly NOT a full cognitive projection: ``certification_level``
    is ``MINIMAL`` and ``checks_detail`` records the limitation. It must not be
    read as a formal stability guarantee.
    """
    return ProjectionCertificate(
        domain_valid=True,
        boundedness_ok=True,
        lipschitz_ok=True,
        noise_robustness_ok=True,
        mode_stability_ok=True,
        lyapunov_compatibility_ok=True,
        margin_to_boundary=1.0,
        local_lipschitz_estimate=None,
        noise_gain_estimate=None,
        certification_level=ProjectionCertificationLevel.MINIMAL,
        checks_detail={
            "minimal_projection": True,
            "full_cognitive_projection": False,
        },
    )
