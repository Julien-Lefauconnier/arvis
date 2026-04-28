# arvis/reflexive/attestation/reflexive_attestation.py

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from arvis.reflexive.core.reflexive_mode import ReflexiveMode


@dataclass(frozen=True)
class ReflexiveAttestation:
    """
    Reflexive surface attestation.
    """

    type: str
    scope: str
    authority: str
    immutability: bool
    deterministic: bool
    mode: ReflexiveMode
    exposed_views: list[str]
    fingerprint: str

    @classmethod
    def from_rendered_payload(
        cls,
        rendered_payload: dict[str, Any],
    ) -> ReflexiveAttestation:
        if not isinstance(rendered_payload, dict):
            raise TypeError("rendered_payload must be a dict")

        payload = deepcopy(rendered_payload)

        mode_value = payload.get("mode")
        mode = ReflexiveMode(mode_value)

        if "exposed_views" not in payload:
            raise ValueError("rendered_payload must declare exposed_views")

        exposed_views_raw = payload.get("exposed_views")
        if not isinstance(exposed_views_raw, list):
            raise TypeError("exposed_views must be a list")

        exposed_views = sorted(exposed_views_raw)

        # timeline_views may contain more than exposed views:
        # do not attest hidden / extra views.
        timeline_views_all = payload.get("timeline_views", {})
        if not isinstance(timeline_views_all, dict):
            raise TypeError("timeline_views must be a dict")

        timeline_views = {
            k: v for k, v in timeline_views_all.items() if k in exposed_views
        }

        payload.pop("generated_at", None)
        payload.pop("mode", None)
        payload.pop("exposed_views", None)
        payload.pop("timeline_views", None)

        fingerprint_source = {
            "timeline_views": timeline_views,
            "payload": payload,
            "exposed_views": exposed_views,
        }

        fingerprint = cls._compute_fingerprint(fingerprint_source)

        return cls(
            type="reflexive_snapshot",
            scope="reflexive",
            authority="system",
            immutability=True,
            deterministic=True,
            mode=mode,
            exposed_views=exposed_views,
            fingerprint=fingerprint,
        )

    @staticmethod
    def _compute_fingerprint(source: dict[str, Any]) -> str:
        serialized = json.dumps(
            source,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "scope": self.scope,
            "authority": self.authority,
            "immutability": self.immutability,
            "deterministic": self.deterministic,
            "mode": self.mode.value,
            "exposed_views": self.exposed_views,
            "fingerprint": self.fingerprint,
        }
