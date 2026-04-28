# arvis/adapters/ir/validity_adapter.py

from __future__ import annotations

from typing import Any


class ValidityIRAdapter:
    @staticmethod
    def from_validity(env: Any) -> dict[str, Any] | None:
        if env is None:
            return None

        return {
            "schema_version": "v1",
            "valid": bool(getattr(env, "valid", False)),
            "reason": getattr(env, "reason", None),
            "projection_available": getattr(env, "projection_available", False),
            "switching_safe": getattr(env, "switching_safe", False),
            "exponential_safe": getattr(env, "exponential_safe", False),
            "kappa_safe": getattr(env, "kappa_safe", False),
            "adaptive_available": getattr(env, "adaptive_available", False),
            "adaptive_band": getattr(env, "adaptive_band", None),
            "certification_scope": getattr(env, "certification_scope", "unknown"),
        }
