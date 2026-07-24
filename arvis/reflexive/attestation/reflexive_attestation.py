# arvis/reflexive/attestation/reflexive_attestation.py

from __future__ import annotations

import hashlib
import hmac
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from arvis.reflexive.core.reflexive_mode import ReflexiveMode

# Version of the canonicalization rule below. A consumer reading
# canon_version from an attestation knows exactly which transformation
# reproduces the fingerprint (audit a15, A15-BETA-02).
ATTESTATION_CANON_VERSION = "1.0"


@dataclass(frozen=True)
class ReflexiveAttestation:
    """Reflexive surface attestation (canonicalization 1.0).

    The fingerprint is computed from the rendered payload after a
    documented, versioned canonicalization:

    - the ``attestation`` key is removed: the attestation is excluded
      from its own fingerprint, so the final public payload verifies
      directly (A15-BETA-02);
    - the volatile ``generated_at`` and the derived ``mode``,
      ``exposed_views`` and ``timeline_views`` keys are removed from
      the payload body;
    - ``timeline_views`` is re-attested filtered to ``exposed_views``
      only, and ``exposed_views`` is attested sorted;
    - the source is JSON-serialized with sorted keys and compact
      separators, then hashed with SHA-256.

    ``deterministic`` means the fingerprint is a pure function of that
    canonical source: no salt, no randomness. Identity across separate
    runs is NOT claimed: the attested state legitimately carries
    decision timestamps. ``immutability`` is true of this object: every
    field is immutable (the view names are a tuple).
    """

    type: str
    scope: str
    authority: str
    immutability: bool
    deterministic: bool
    mode: ReflexiveMode
    exposed_views: tuple[str, ...]
    fingerprint: str
    canon_version: str = ATTESTATION_CANON_VERSION

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

        # The attestation is excluded from its own fingerprint: the
        # canonical source of a final payload and of the pre-attestation
        # rendering are identical (A15-BETA-02).
        payload.pop("attestation", None)
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
            exposed_views=tuple(exposed_views),
            fingerprint=fingerprint,
        )

    @classmethod
    def verify(cls, rendered_payload: dict[str, Any]) -> bool:
        """Verify a final public payload against its embedded attestation.

        Recomputes the fingerprint from the payload as exposed, with no
        implicit transformation, and compares it to the embedded one.
        Fail-closed: any malformed or altered payload returns False.
        """
        try:
            embedded = rendered_payload.get("attestation")
            if not isinstance(embedded, dict):
                return False
            published = embedded.get("fingerprint")
            if not isinstance(published, str):
                return False
            recomputed = cls.from_rendered_payload(rendered_payload)
            return hmac.compare_digest(recomputed.fingerprint, published)
        except (TypeError, ValueError, KeyError):
            return False

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
            "exposed_views": list(self.exposed_views),
            "fingerprint": self.fingerprint,
            "canon_version": self.canon_version,
        }
