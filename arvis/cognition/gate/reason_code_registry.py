# arvis/cognition/gate/reason_code_registry.py

from __future__ import annotations

from typing import Set


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
    _CODES: Set[str] = {
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

        # --- Recovery ---
        "recovery_override",

        # --- Generic ---
        "fusion_fallback",
        "gate_policy_adjustment",
        "unknown_reason",  # fallback safe
    }

    # -----------------------------------------
    # API
    # -----------------------------------------
    @classmethod
    def is_valid(cls, code: str) -> bool:
        return code in cls._CODES

    @classmethod
    def all(cls) -> Set[str]:
        return set(cls._CODES)