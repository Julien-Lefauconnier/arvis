# arvis/cognition/conflict/conflict_confirmation.py

def requires_conflict_confirmation(
    conflict_pressure: float,
    threshold: float = 0.5,
) -> bool:
    """
    Determines whether conflict requires external confirmation.

    Pure function.
    """

    return conflict_pressure >= threshold