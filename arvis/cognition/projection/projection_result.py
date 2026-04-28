# arvis/cognition/projection/projection_result.py

from dataclasses import dataclass

from .projection_diagnostics import ProjectionDiagnostics


@dataclass(frozen=True)
class ProjectionResult:
    """
    Output of the projection operator Π.

    This is the canonical interface between cognition and math.
    """

    x: tuple[float, ...]
    z: tuple[float, ...]
    q: str
    w: tuple[float, ...]

    diagnostics: ProjectionDiagnostics
