# arvis/cognition/projection/projection_diagnostics.py

from dataclasses import dataclass, field

Scalar = float | int | bool | str


@dataclass(frozen=True)
class ProjectionDiagnostics:
    """
    Diagnostics attached to every projection result.

    This is part of the mathematical contract of the projection layer.
    """

    # Domain validity
    is_admissible: bool
    admissibility_violations: tuple[str, ...]

    # Normalization
    normalization_warnings: tuple[str, ...]

    # Switching diagnostics
    mode_boundary_margin: float | None

    # Local sensitivity (optional at early stage)
    local_sensitivity_estimate: float | None

    # Norms (mandatory for boundedness checks)
    x_norm: float
    z_norm: float
    w_norm: float

    # Extra debug / extensibility
    extra: dict[str, Scalar] = field(default_factory=dict)
