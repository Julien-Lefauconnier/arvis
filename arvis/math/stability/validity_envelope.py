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


# The gate publishes an invalid envelope as a reason code. That code used
# to be built as f"validity_{envelope.reason}", which is why none of these
# five were ever registered: a constructed string is invisible to the
# registry ratchet, so every one of them reached the IR as
# "unknown_reason" and the audit record said nothing about why the turn
# failed closed (campaign REASONS, 2026-09-04). The mapping is explicit so
# the emitted set stays closed, greppable, and registrable.
VALIDITY_REASON_CODES: dict[str, str] = {
    "projection_unavailable": "validity_projection_unavailable",
    "switching_violation": "validity_switching_violation",
    "exponential_violation": "validity_exponential_violation",
    "kappa_violation": "validity_kappa_violation",
    "adaptive_unavailable": "validity_adaptive_unavailable",
}


def validity_reason_code(reason: str | None) -> str:
    """Return the registered reason code for an envelope reason.

    An unmapped reason is a defect rather than a value to pass through:
    the envelope is the only producer of these reasons, so a new one must
    be registered with the others. It degrades to ``validity_unknown``,
    which is a registered code, so the audit record still names the layer
    that refused.
    """
    if reason is None:
        return "validity_unknown"
    return VALIDITY_REASON_CODES.get(reason, "validity_unknown")
