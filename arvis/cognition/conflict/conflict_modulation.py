# arvis/cognition/conflict/conflict_modulation.py


def apply_conflict_to_risk(
    base_risk: float,
    conflict_pressure: float,
    alpha: float = 0.25,
) -> float:
    """
    Modulates risk based on conflict pressure.

    - Pure
    - Deterministic
    - Bounded

    risk' = risk * (1 + alpha * pressure)
    """

    if base_risk <= 0.0:
        return 0.0

    adjusted = base_risk * (1.0 + alpha * conflict_pressure)

    # hard bound (safety)
    return min(1.0, adjusted)
