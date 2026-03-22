# arvis/math/stability/validity_envelope.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ValidityEnvelope:
    valid: bool
    projection_available: bool
    switching_safe: bool
    exponential_safe: bool
    kappa_safe: bool
    adaptive_available: bool
    adaptive_band: Optional[str]
    reason: Optional[str] = None


def build_validity_envelope(
    *,
    projection_available: bool,
    switching_safe: bool,
    exponential_safe: bool,
    kappa_safe: bool,
    adaptive_available: bool,
    adaptive_band: Optional[str],
) -> ValidityEnvelope:
    if not projection_available:
        return ValidityEnvelope(
            valid=False,
            projection_available=False,
            switching_safe=switching_safe,
            exponential_safe=exponential_safe,
            kappa_safe=kappa_safe,
            adaptive_available=adaptive_available,
            adaptive_band=adaptive_band,
            reason="projection_unavailable",
        )

    if not switching_safe:
        return ValidityEnvelope(
            valid=False,
            projection_available=projection_available,
            switching_safe=False,
            exponential_safe=exponential_safe,
            kappa_safe=kappa_safe,
            adaptive_available=adaptive_available,
            adaptive_band=adaptive_band,
            reason="switching_violation",
        )

    if not exponential_safe:
        return ValidityEnvelope(
            valid=False,
            projection_available=projection_available,
            switching_safe=switching_safe,
            exponential_safe=False,
            kappa_safe=kappa_safe,
            adaptive_available=adaptive_available,
            adaptive_band=adaptive_band,
            reason="exponential_violation",
        )

    if not kappa_safe:
        return ValidityEnvelope(
            valid=False,
            projection_available=projection_available,
            switching_safe=switching_safe,
            exponential_safe=exponential_safe,
            kappa_safe=False,
            adaptive_available=adaptive_available,
            adaptive_band=adaptive_band,
            reason="kappa_violation",
        )

    return ValidityEnvelope(
        valid=True,
        projection_available=projection_available,
        switching_safe=switching_safe,
        exponential_safe=exponential_safe,
        kappa_safe=kappa_safe,
        adaptive_available=adaptive_available,
        adaptive_band=adaptive_band,
        reason=None,
    )