# arvis/cognition/projection/projection_result.py

from dataclasses import dataclass
from typing import Tuple

from .projection_diagnostics import ProjectionDiagnostics


@dataclass(frozen=True)
class ProjectionResult:
    """
    Output of the projection operator Π.

    This is the canonical interface between cognition and math.
    """

    x: Tuple[float, ...]
    z: Tuple[float, ...]
    q: str
    w: Tuple[float, ...]

    diagnostics: ProjectionDiagnostics