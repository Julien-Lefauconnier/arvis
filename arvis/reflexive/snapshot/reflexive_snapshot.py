# arvis/reflexive/snapshot/reflexive_snapshot.py

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from arvis.reflexive.core.reflexive_mode_registry import (
    ReflexiveModeRegistry,
)


@dataclass(frozen=True)
class ReflexiveSnapshot:
    capabilities: Any
    cognitive_state: Any | None
    timeline_views: dict[str, Any]
    introspection: Any | None
    generated_at: datetime
    attestation: Any | None = None
    timeline_explanation: Any | None = None
    irg_explanation: Any | None = None

    def _is_public_role(self, role: Any) -> bool:
        if role is None:
            return False
        role_value = getattr(role, "value", role)
        return role_value in {"public", "exposed", "user_visible", "trace_factuelle"}

    def to_dict(self) -> dict[str, Any]:
        mode = ReflexiveModeRegistry.resolve(
            snapshot=self,
        )
        public_views = {
            key: self._safe_serialize(view)
            for key, view in self.timeline_views.items()
            if hasattr(view, "role") and self._is_public_role(view.role)
        }
        return {
            "mode": mode.value,
            "capabilities": self._safe_serialize(self.capabilities),
            "cognitive_state": self._safe_serialize(self.cognitive_state),
            "timeline_views": public_views,
            # a16 (A15-BETA-02): the final public payload natively
            # carries every parameter its attestation needs; a consumer
            # never reconstructs inputs from the attestation itself.
            "exposed_views": sorted(public_views),
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

        # A14-P1-01: the real CognitiveState is a tree of plain
        # dataclasses; serialize field by field through this same
        # method so nested specials stay covered. Before this branch,
        # the state travelled as a live object and the attestation's
        # json.dumps raised, silently degrading reflexive to None.
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return {
                field.name: self._safe_serialize(getattr(value, field.name))
                for field in dataclasses.fields(value)
            }

        if isinstance(value, Enum):
            return self._safe_serialize(value.value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, dict):
            return {k: self._safe_serialize(v) for k, v in value.items()}

        if isinstance(value, (list, tuple)):
            return [self._safe_serialize(v) for v in value]

        if isinstance(value, (str, int, float, bool)):
            return value

        # Final net: a live object with no serialization contract (the
        # in-state SignalJournal, an observer, a lock holder) surfaces
        # as a deterministic opaque marker. The reflexive payload states
        # the structure without exposing live internals; the curated
        # timeline exposure goes through the role-filtered
        # timeline_views channel, never through the raw state.
        return f"<unserialized:{type(value).__qualname__}>"

    def _build_explanation(self) -> dict[str, Any]:
        # Deprecated: explanation now built upstream in builder
        return {}
