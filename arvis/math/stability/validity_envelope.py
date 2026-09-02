# arvis/math/stability/validity_envelope.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidityEnvelope:
    """Partial certification of the turn's mathematical validity.

    ``switching_safe`` is the value the envelope's validity consumed
    (posture-dependent: the soft profile feeds True). Campaign
    GATE-SEM (DM-G2) adds ``switching_safe_measured``, the raw T1
    verdict of the switching guard, so the envelope never again
    publishes True for a condition that was measured False without
    saying so; and an absent adaptive layer invalidates the envelope
    instead of leaving it silently valid.
    """

    valid: bool
    projection_available: bool
    switching_safe: bool
    exponential_safe: bool
    kappa_safe: bool
    adaptive_available: bool
    adaptive_band: str | None
    reason: str | None = None
    switching_safe_measured: bool | None = None


def build_validity_envelope(
    *,
    projection_available: bool,
    switching_safe: bool,
    exponential_safe: bool,
    kappa_safe: bool,
    adaptive_available: bool,
    adaptive_band: str | None,
    switching_safe_measured: bool | None = None,
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
            switching_safe_measured=switching_safe_measured,
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
            switching_safe_measured=switching_safe_measured,
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
            switching_safe_measured=switching_safe_measured,
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
            switching_safe_measured=switching_safe_measured,
        )

    if not adaptive_available:
        # DM-G2 (campaign GATE-SEM): an absent adaptive layer is a
        # missing certification axis, not a valid envelope. The
        # registry maps this to the adaptive_unavailable reason code
        # (ARVIS_VALIDITY_ENVELOPE_SPEC_V1.md section 6 anticipated
        # exactly this mapping).
        return ValidityEnvelope(
            valid=False,
            projection_available=projection_available,
            switching_safe=switching_safe,
            exponential_safe=exponential_safe,
            kappa_safe=kappa_safe,
            adaptive_available=False,
            adaptive_band=adaptive_band,
            reason="adaptive_unavailable",
            switching_safe_measured=switching_safe_measured,
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
        switching_safe_measured=switching_safe_measured,
    )
