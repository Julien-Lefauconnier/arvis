# arvis/cognition/projection/projection_api.py

from dataclasses import dataclass
from typing import Dict, Any

from .projection_result import ProjectionResult
from .projection_diagnostics import ProjectionDiagnostics


# -----------------------------
# Observation contract
# -----------------------------

@dataclass(frozen=True)
class Observation:
    numeric_signals: Dict[str, float]
    structured_signals: Dict[str, Any]
    external_signals: Dict[str, Any]


# -----------------------------
# Constants (TEMP — will evolve)
# -----------------------------

ALLOWED_MODES = ("nominal", "alert", "critical")

X_BOUND = 10.0
Z_BOUND = 10.0
W_BOUND = 10.0


# -----------------------------
# Core projection entrypoint
# -----------------------------

def project_observation(observation: Observation) -> ProjectionResult:
    """
    Deterministic projection Π(o) -> (x, z, q, w)

    Current implementation:
    - simple deterministic mapping
    - placeholder for real projection pipeline
    """

    # ---- Basic validation ----
    violations_initial: list[str] = []
    for k, v in observation.numeric_signals.items():
        if not isinstance(v, (int, float)):
            violations_initial.append(f"non_numeric:{k}")

    is_admissible = len(violations_initial) == 0

    # ---- Simple deterministic projection ----
    # (placeholder logic — will be replaced later)

    x_values = []
    violations: list[str] = []

    for k, v in observation.numeric_signals.items():
        try:
            x_values.append(float(v))
        except (ValueError, TypeError):
            violations.append(f"non_numeric:{k}")
            x_values.append(0.0)  # fallback safe value

    x = tuple(x_values)

    z = tuple(sum(x) / len(x) if x else 0.0 for _ in range(2))

    # simple mode logic
    avg = sum(x) / len(x) if x else 0.0
    if avg < 0.3:
        q = "nominal"
    elif avg < 0.7:
        q = "alert"
    else:
        q = "critical"

    w = tuple(min(abs(v), 1.0) for v in x[:2])

    # ---- Norms ----
    x_norm = sum(abs(v) for v in x)
    z_norm = sum(abs(v) for v in z)
    w_norm = sum(abs(v) for v in w)

    # ---- Diagnostics ----
    diagnostics = ProjectionDiagnostics(
        is_admissible=is_admissible,
        admissibility_violations=tuple(violations),
        normalization_warnings=(),
        mode_boundary_margin=None,
        local_sensitivity_estimate=None,
        x_norm=x_norm,
        z_norm=z_norm,
        w_norm=w_norm,
    )

    return ProjectionResult(
        x=x,
        z=z,
        q=q,
        w=w,
        diagnostics=diagnostics,
    )