# arvis/reflexive/snapshot/reflexive_snapshot.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


from arvis.reflexive.core.reflexive_mode_registry import (
    ReflexiveModeRegistry,
)


@dataclass(frozen=True)
class ReflexiveSnapshot:
    capabilities: Any
    cognitive_state: Optional[Any]
    timeline_views: Dict[str, Any]
    introspection: Optional[Any]
    generated_at: datetime
    attestation: Optional[Any] = None
    timeline_explanation: Optional[Any] = None
    irg_explanation: Optional[Any] = None

    def _is_public_role(self, role: Any) -> bool:
        if role is None:
            return False
        role_value = getattr(role, "value", role)
        return role_value in {"public", "exposed", "user_visible", "trace_factuelle"}

    def to_dict(self) -> Dict[str, Any]:
        mode = ReflexiveModeRegistry.resolve(
            snapshot=self,
        )
        return {
            "mode": mode.value,
            "capabilities": self._safe_serialize(self.capabilities),
            "cognitive_state": self._safe_serialize(self.cognitive_state),
            "timeline_views": {
                key: self._safe_serialize(view)
                for key, view in self.timeline_views.items()
                if hasattr(view, "role") and self._is_public_role(view.role)
            },
            "introspection": self._safe_serialize(self.introspection),
            # ----------------------------------------
            # Use canonical pre-built explanations
            # ----------------------------------------
            "explanation": self._safe_serialize(self.timeline_explanation),
            "irg_explanation": self._safe_serialize(self.irg_explanation),
            "generated_at": self.generated_at.isoformat(),
            "attestation": self._safe_serialize(self.attestation),
        }

    def _safe_serialize(self, value: Any) -> Any:
        if value is None:
            return None

        if hasattr(value, "to_dict"):
            return value.to_dict()

        if isinstance(value, dict):
            return {k: self._safe_serialize(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._safe_serialize(v) for v in value]

        return value

    def _build_explanation(self) -> Dict[str, Any]:
        # Deprecated: explanation now built upstream in builder
        return {}
