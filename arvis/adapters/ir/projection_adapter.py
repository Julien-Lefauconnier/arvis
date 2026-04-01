# arvis/adapters/ir/projection_adapter.py

from __future__ import annotations

from typing import Any


class ProjectionIRAdapter:

    @staticmethod
    def from_projection(cert: Any) -> dict[str, Any] | None:
        if cert is None:
            return None

        return {
            "schema_version": "v1",
            "available": bool(getattr(cert, "available", False)),
            "domain_valid": getattr(cert, "domain_valid", None),
            "is_projection_safe": getattr(cert, "is_projection_safe", None),
            "lyapunov_compatibility_ok": getattr(cert, "lyapunov_compatibility_ok", None),
            "margin_to_boundary": getattr(cert, "margin_to_boundary", None),
            "certification_level": getattr(cert, "certification_level", "UNKNOWN"),
            "projection_domain": getattr(cert, "projection_domain", None),
            "proof_status": getattr(cert, "proof_status", "none"),
            "warning_codes": tuple(getattr(cert, "warning_codes", ()) or ()),
        }