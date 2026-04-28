# arvis/adapters/ir/stability_adapter.py

from __future__ import annotations

from typing import Any


class StabilityIRAdapter:
    @staticmethod
    def from_stability(cert: Any) -> dict[str, Any] | None:
        if cert is None:
            return None

        if not isinstance(cert, dict):
            return None

        return {
            "schema_version": "v1",
            "local_stability": bool(cert.get("local", False)),
            "global_stability": bool(cert.get("global", False)),
            "kappa_safe": bool(cert.get("kappa_safe", True)),
            "margin": cert.get("margin"),
            "stability_domain": cert.get("domain", "unknown"),
        }
