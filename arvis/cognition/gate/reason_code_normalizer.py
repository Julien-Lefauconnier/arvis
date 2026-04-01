# arvis/cognition/gate/reason_code_normalizer.py

from __future__ import annotations

import os
from typing import Iterable, Tuple

from .reason_code_registry import ReasonCodeRegistry

STRICT_MODE = os.getenv("ARVIS_REASON_STRICT", "false").lower() == "true"

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

        # --- Generic ---
        "fusion_fallback": "fusion_fallback",
        "gate_policy_adjustment": "gate_policy_adjustment",
    }

    # -----------------------------------------
    # Public API
    # -----------------------------------------
    @classmethod
    def normalize(cls, codes: Iterable[str]) -> Tuple[str, ...]:
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
                if STRICT_MODE:
                    raise ValueError(f"Unknown reason code: {mapped}")
                mapped = "unknown_reason"

            if mapped not in normalized:
                normalized.append(mapped)

        return tuple(normalized)