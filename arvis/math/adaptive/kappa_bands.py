# arvis/math/adaptive/kappa_bands.py

"""The kappa margin band table, single source (campaign HARDEN, DM-H9).

The band thresholds and the per-band epsilon regulation factors were
duplicated verbatim in the control stage and the gate adaptive layer
(audit P1-9b): two copies of a verdict-affecting policy with nothing
keeping them equal. Both consumers now read this table; the
thresholds are part of ``policies_fingerprint``.

Semantics (M8): the margin is the adaptive switching margin;
non-negative means the T1 condition is violated NOW (hard band), the
negative bands grade the distance to violation.
"""

from __future__ import annotations

KAPPA_BAND_CRITICAL_THRESHOLD = -0.02
KAPPA_BAND_WARNING_THRESHOLD = -0.05


def kappa_band(margin: float) -> str:
    """Band label for a measured kappa margin (hard, critical,
    warning, stable). Total over floats."""
    if margin > 0.0:
        return "hard"
    if margin > KAPPA_BAND_CRITICAL_THRESHOLD:
        return "critical"
    if margin > KAPPA_BAND_WARNING_THRESHOLD:
        return "warning"
    return "stable"


# Epsilon regulation factor applied by the control stage per band
# (continuous kappa margin regulation, M8). "stable" leaves epsilon
# untouched.
KAPPA_BAND_EPSILON_FACTORS: dict[str, float] = {
    "hard": 0.25,
    "critical": 0.5,
    "warning": 0.8,
    "stable": 1.0,
}
