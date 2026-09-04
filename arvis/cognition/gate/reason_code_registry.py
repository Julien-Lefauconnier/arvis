# arvis/cognition/gate/reason_code_registry.py

from __future__ import annotations


class ReasonCodeRegistry:
    """
    Canonical registry of allowed reason codes (spec-aligned).

    This is the SINGLE SOURCE OF TRUTH for:
    - validation
    - documentation
    - IR consistency
    """

    # -----------------------------------------
    # Canonical allowed reason codes
    # -----------------------------------------
    _CODES: set[str] = {
        # --- Global stability ---
        "global_instability_confirmed",
        "global_instability_abstained",
        # --- Adaptive ---
        "adaptive_margin_warning",
        "adaptive_instability_veto",
        # --- Projection ---
        "projection_invalid",
        "projection_boundary",
        "projection_unsafe",
        "projection_lyapunov_incompatible",
        # --- Kappa ---
        "kappa_violation",
        "kappa_margin_warning",
        "kappa_margin_critical",
        # --- Validity envelope ---
        # Campaign REASONS (2026-09-04): these are what the envelope
        # publishes when it refuses to certify a turn, and they were the
        # most frequent reason codes in the system. The gate built them
        # as f"validity_{reason}", so none was ever registered and every
        # one reached the IR as "unknown_reason": the audit record named
        # no cause for the most common refusal in the product. The
        # emitted set is now closed in VALIDITY_REASON_CODES.
        "validity_projection_unavailable",
        "validity_switching_violation",
        "validity_exponential_violation",
        "validity_kappa_violation",
        "validity_adaptive_unavailable",
        "validity_unknown",  # envelope refused for an unmapped reason
        # --- Switching (monitor-only under the default posture) ---
        "switching_soft_warning",
        "switching_unsafe_monitoring",
        # --- Declared input risk ---
        "input_risk_governed",
        "input_risk_hardened",
        "input_risk_relax_denied",
        # --- Recovery ---
        "recovery_override",
        # --- Generic ---
        "fusion_fallback",
        "gate_policy_adjustment",
        "gate_fail_closed",
        "unknown_reason",  # fallback safe
        # --- Access ---
        "access_denied",
    }

    # -----------------------------------------
    # API
    # -----------------------------------------
    @classmethod
    def is_valid(cls, code: str) -> bool:
        return code in cls._CODES

    @classmethod
    def all(cls) -> set[str]:
        return set(cls._CODES)
