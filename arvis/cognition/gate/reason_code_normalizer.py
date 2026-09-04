# arvis/cognition/gate/reason_code_normalizer.py

from __future__ import annotations

import os
from collections.abc import Iterable

from .reason_code_registry import ReasonCodeRegistry


def _strict_mode() -> bool:
    """ARVIS_REASON_STRICT, read lazily (DM-H6, campaign HARDEN): the
    module-level constant froze the value at import time, so setting
    the variable after ``import arvis`` was silently ignored. See
    docs/CONFIGURATION.md."""
    return os.getenv("ARVIS_REASON_STRICT", "false").lower() == "true"


class ReasonCodeNormalizer:
    """
    Normalize reason codes to a canonical spec-aligned vocabulary.

    Goals:
    - enforce naming consistency
    - map legacy/internal codes → spec codes
    - guarantee clean output (no empty / malformed codes)
    """

    # -----------------------------------------
    # Canonical mapping (internal → spec)
    # -----------------------------------------
    _MAPPING: dict[str, str] = {
        # --- Global stability ---
        "global_instability_confirm": "global_instability_confirmed",
        "global_instability_abstain": "global_instability_abstained",
        # --- Adaptive ---
        "adaptive_warning": "adaptive_margin_warning",
        "adaptive_instability": "adaptive_instability_veto",
        "adaptive_hard_veto": "adaptive_instability_veto",
        # --- Projection ---
        "projection_invalid": "projection_invalid",
        "projection_boundary": "projection_boundary",
        "projection_unsafe": "projection_unsafe",
        "projection_lyapunov_incompatible": "projection_lyapunov_incompatible",
        # --- Kappa ---
        "kappa_violation": "kappa_violation",
        "kappa_margin_warning": "kappa_margin_warning",
        "kappa_margin_critical": "kappa_margin_critical",
        # --- Recovery ---
        "recovery_post_fusion_override": "recovery_override",
        # --- Declared input risk (campaign REASONS) ---
        # The gate names its own stage when it records a transition
        # ("input_risk_gate", "input_risk_harden") and its policy when it
        # names the cause ("input_risk_policy"): three internal spellings
        # for two meanings, the declared risk governed the verdict or it
        # only hardened it. All of them used to arrive as
        # "unknown_reason".
        "input_risk_gate": "input_risk_governed",
        "input_risk_policy": "input_risk_governed",
        "input_risk_harden": "input_risk_hardened",
        "verdict_provenance_not_artifact": "input_risk_relax_denied",
        # --- Generic ---
        "fusion_fallback": "fusion_fallback",
        "gate_policy_adjustment": "gate_policy_adjustment",
        "gate_exception": "gate_fail_closed",
    }

    # -----------------------------------------
    # Public API
    # -----------------------------------------
    @classmethod
    def normalize(cls, codes: Iterable[str]) -> tuple[str, ...]:
        """
        Normalize a collection of reason codes.

        - strips whitespace
        - lowercases
        - applies mapping
        - removes duplicates (order preserved)
        """

        normalized: list[str] = []

        for code in codes:
            c = str(code).strip().lower()
            if not c:
                continue

            mapped = cls._MAPPING.get(c, c)

            # -----------------------------------------
            # VALIDATION
            # -----------------------------------------
            if not ReasonCodeRegistry.is_valid(mapped):
                if _strict_mode():
                    raise ValueError(f"Unknown reason code: {mapped}")
                mapped = "unknown_reason"

            if mapped not in normalized:
                normalized.append(mapped)

        return tuple(normalized)
