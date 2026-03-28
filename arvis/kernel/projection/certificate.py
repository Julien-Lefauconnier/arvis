# arvis/kernel/projection/certificate.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ProjectionCertificationLevel(str, Enum):
    NONE = "NONE"
    BASIC = "BASIC"
    LOCAL = "LOCAL"
    CERTIFIED_RUNTIME = "CERTIFIED_RUNTIME"


@dataclass(frozen=True)
class ProjectionCertificate:
    domain_valid: bool

    # main checks (M3)
    boundedness_ok: bool
    lipschitz_ok: bool
    noise_robustness_ok: bool
    mode_stability_ok: bool
    lyapunov_compatibility_ok: bool

    # runtime metrics
    margin_to_boundary: float
    local_lipschitz_estimate: Optional[float]
    noise_gain_estimate: Optional[float]

    certification_level: ProjectionCertificationLevel

    # debug / trace
    checks_detail: Dict[str, bool]

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